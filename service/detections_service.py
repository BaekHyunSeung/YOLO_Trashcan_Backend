from __future__ import annotations

from collections import Counter
from typing import Literal
from uuid import uuid4
from pathlib import Path
from datetime import datetime, date, timedelta
from sqlmodel import select
from sqlalchemy import desc, func, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from db.db import SessionDep
from db.entity import Detection, DetectionDetail, DailyStats, Trashcan, WasteType, TrashcanErrorLog
from models.request import DetectionCreate, DetectionObject, BBox
from fastapi import HTTPException
from utils.detection_intake import (
    DetectionIntervalGate,
    load_detection_intake_settings,
    normalize_detection_score,
)
from utils.service_helpers import image_storage_root, trashcan_pk_exists
from utils.waste_type_config import get_class_id_to_type_name


class DetectionService:
    IMAGE_RELATIVE_DIR = "detect_img"

    def __init__(self) -> None:
        self._intake = load_detection_intake_settings()
        self._interval_gate = DetectionIntervalGate(self._intake.min_interval_seconds)

    async def should_skip_intake_interval(
        self, trashcan_id: int | None, camera_id: int
    ) -> bool:
        """등록 간격 미달이면 True(본문 무시·204). trashcan 미매핑이면 간격 적용 안 함."""
        if trashcan_id is None:
            return False
        return not await self._interval_gate.claim(camera_id)

    async def _detection_item_to_object(
        self, d: dict, db: SessionDep
    ) -> DetectionObject | None:
        score = normalize_detection_score(d.get("score", 0.0))
        if score < self._intake.min_confidence:
            return None
        class_id = d.get("class_id")
        bbox = d.get("bbox", [0, 0, 0, 0])
        type_name = get_class_id_to_type_name(class_id)
        if type_name is None:
            return None
        waste_type_id = await self.get_waste_type_id(type_name, db)
        if waste_type_id is None:
            return None
        return DetectionObject(
            waste_type_id=waste_type_id,
            type_name=type_name,
            confidence=score,
            box=BBox(
                x1=bbox[0],
                y1=bbox[1],
                x2=bbox[2],
                y2=bbox[3],
            ),
        )

    def _build_image_filename(
        self,
        trashcan_id: int,
        detection_id: int,
        detected_at: datetime,
        original_filename: str | None,
    ) -> str:
        original_name = Path(original_filename or "").name
        suffix = Path(original_name).suffix or ".jpg"
        timestamp = detected_at.strftime("%Y%m%d_%H%M%S_%f")[:-3]
        uuid = uuid4().hex[:8]
        return f"{trashcan_id}_{detection_id}_{timestamp}_{uuid}{suffix}"

    def _build_image_paths(self, saved_filename: str) -> tuple[str, str, Path]:
        relative_path = Path(self.IMAGE_RELATIVE_DIR) / saved_filename
        absolute_path = image_storage_root() / relative_path
        return saved_filename, relative_path.as_posix(), absolute_path

    async def save_uploaded_image(
        self,
        file,
        trashcan_id: int,
        detection_id: int,
        detected_at: datetime,
        original_filename: str | None,
    ) -> tuple[str, str]:
        saved_filename = self._build_image_filename(
            trashcan_id,
            detection_id,
            detected_at,
            original_filename,
        )
        safe_filename, saved_path, absolute_path = self._build_image_paths(saved_filename)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        contents = await file.read()
        absolute_path.write_bytes(contents)
        await file.seek(0)

        return safe_filename, saved_path

    async def detection_mapping(
        self,
        data,
        file,
        db: SessionDep,
        trashcan_id: int | None = None,
    ):
        # camera_id -> trashcan_id 조회
        if trashcan_id is None:
            camera_id = data.get("camera_id")
            status, tid = await self.lookup_trashcan_for_detection(camera_id, db)
            if status == "missing":
                raise HTTPException(
                    status_code=400,
                    detail=f"등록되지 않은 쓰레기통입니다. camera_id={camera_id}",
                )
            if status == "deleted":
                raise HTTPException(
                    status_code=400,
                    detail=f"삭제된 쓰레기통입니다. trashcan_id={tid}, camera_id={camera_id}",
                )
            trashcan_id = tid
        await self.update_trashcan_online(trashcan_id, db)

        objects: list[DetectionObject] = []
        for raw in data.get("detections", []):
            if not isinstance(raw, dict):
                continue
            obj = await self._detection_item_to_object(raw, db)
            if obj is not None:
                objects.append(obj)

        if not objects:
            await file.read()
            return None

        payload = DetectionCreate(
            trashcan_id=trashcan_id,
            filename=file.filename,
            object_count=len(objects),
            objects=objects,
        )

        await self.save_detection(payload, file, db)
        return None

    async def save_trashcan_error_log(
        self,
        trashcan_id: int | None,
        camera_id: int | None,
        status_code: int,
        message: str | None,
        occurred_at: str | None,
        db: SessionDep,
    ) -> None:
        if trashcan_id is not None:
            if not await trashcan_pk_exists(trashcan_id, db):
                return
        occurred_value = None
        if occurred_at:
            try:
                normalized = occurred_at.replace("Z", "+00:00")
                occurred_value = datetime.fromisoformat(normalized)
            except ValueError:
                occurred_value = None
        effective_time = occurred_value or datetime.now()
        if effective_time.tzinfo is not None:
            effective_time = effective_time.astimezone(tz=None).replace(tzinfo=None)
        base_stmt = (
            select(TrashcanErrorLog)
            .where(TrashcanErrorLog.status_code == status_code)
            .where(TrashcanErrorLog.message == message)
        )
        if trashcan_id is not None:
            base_stmt = base_stmt.where(TrashcanErrorLog.trashcan_id == trashcan_id)
        else:
            base_stmt = base_stmt.where(TrashcanErrorLog.trashcan_id.is_(None))
            base_stmt = base_stmt.where(TrashcanErrorLog.camera_id == camera_id)
        last_log = (
            await db.execute(
                base_stmt.order_by(
                    desc(TrashcanErrorLog.created_at),
                    desc(TrashcanErrorLog.id),
                ).limit(1)
            )
        ).scalar_one_or_none()
        if last_log:
            last_time = last_log.last_occurred_at or last_log.created_at
            if last_time and last_time.tzinfo is not None:
                last_time = last_time.astimezone(tz=None).replace(tzinfo=None)
            if last_time and effective_time - last_time <= timedelta(minutes=1):
                last_log.repeat_count = (last_log.repeat_count or 1) + 1
                last_log.last_occurred_at = effective_time
                await db.commit()
                return
        log = TrashcanErrorLog(
            trashcan_id=trashcan_id,
            camera_id=camera_id,
            status_code=status_code,
            message=message,
            occurred_at=occurred_value,
            last_occurred_at=effective_time,
            repeat_count=1,
        )
        db.add(log)
        await db.commit()
        return

    async def get_waste_type_id(self, type_name: str, db: SessionDep) -> int | None:
        stmt = (
            select(WasteType.waste_type_id)
            .where(WasteType.type_name == type_name)
            .where(WasteType.is_active == True)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def lookup_trashcan_for_detection(
        self,
        raw_id: int | str | None,
        db: SessionDep,
    ) -> tuple[Literal["active", "deleted", "missing"], int | None]:
        """camera_id(= trashcan PK) 기준: 활성 / 삭제됨 / 없음."""
        if raw_id is None:
            return ("missing", None)
        try:
            tid = int(raw_id)
        except (TypeError, ValueError):
            return ("missing", None)
        stmt = select(Trashcan.trashcan_id, Trashcan.is_deleted).where(
            Trashcan.trashcan_id == tid
        )
        row = (await db.execute(stmt)).first()
        if row is None:
            return ("missing", None)
        _pk, is_deleted = row[0], row[1]
        if is_deleted:
            return ("deleted", tid)
        return ("active", tid)

    async def get_trashcan_id(
        self, trashcan_id_value: int | str | None, db: SessionDep
    ) -> int | None:
        """수신 가능한(삭제되지 않은) 쓰레기통 ID만 반환."""
        status, tid = await self.lookup_trashcan_for_detection(trashcan_id_value, db)
        if status == "active":
            return tid
        return None

    async def update_trashcan_online(self, trashcan_id: int, db: SessionDep) -> None:
        stmt = (
            select(Trashcan)
            .where(Trashcan.trashcan_id == trashcan_id)
            .where(Trashcan.is_deleted == False)
        )
        target = (await db.execute(stmt)).scalar_one_or_none()
        if not target:
            return
        target.is_online = True
        target.last_connected_at = datetime.now()
        await db.commit()
    
    async def save_detection(self, payload: DetectionCreate, file, db: SessionDep):
        #detection 저장
        detected_at = datetime.now()
        detection = Detection(
            trashcan_id=payload.trashcan_id,
            image_name=None,
            image_path=None,
            detected_at=detected_at,
            object_count=payload.object_count,
        )
        db.add(detection)
        await db.commit()
        await db.refresh(detection)

        safe_filename, saved_path = await self.save_uploaded_image(
            file,
            payload.trashcan_id,
            detection.detection_id,
            detected_at,
            payload.filename,
        )
        detection.image_name = safe_filename
        detection.image_path = saved_path
        await db.commit()

        #detection_detail 저장
        for obj in payload.objects:
            detail = DetectionDetail(
                detection_id=detection.detection_id,
                waste_type_id=obj.waste_type_id,
                confidence=obj.confidence,
                bbox_x1=obj.box.x1,
                bbox_y1=obj.box.y1,
                bbox_x2=obj.box.x2,
                bbox_y2=obj.box.y2,
            )
            db.add(detail)
        await db.commit()

        # trashcan 수거량: DB에서 원자적으로 증가 (동시 요청 시 read-modify-write lost update 방지)
        stmt_vol = (
            update(Trashcan)
            .where(Trashcan.trashcan_id == payload.trashcan_id)
            .values(
                current_volume=func.coalesce(Trashcan.current_volume, 0)
                + payload.object_count,
            )
        )
        await db.execute(stmt_vol)
        await db.commit()

        #trashcan_city 조회
        trashcan_city = (
            await db.execute(
                select(Trashcan.trashcan_city).where(Trashcan.trashcan_id == payload.trashcan_id)
            )
        ).scalar_one()

        # daily_stats: 유니크 키 기준 ON DUPLICATE KEY UPDATE로 원자적 증가
        today = date.today()
        for waste_type_id, delta in Counter(
            obj.waste_type_id for obj in payload.objects
        ).items():
            ins = mysql_insert(DailyStats).values(
                stats_date=today,
                trashcan_city=trashcan_city,
                waste_type_id=waste_type_id,
                detection_count=delta,
            )
            ins = ins.on_duplicate_key_update(
                detection_count=func.coalesce(DailyStats.detection_count, 0) + delta,
            )
            await db.execute(ins)
        await db.commit()