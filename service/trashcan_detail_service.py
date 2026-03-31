import os
from pathlib import Path

from utils.trashcan_status_utils import mark_offline_if_stale

from sqlmodel import select
from sqlalchemy import func
from db.entity import Trashcan, Detection, DetectionDetail, WasteType
from db.db import SessionDep
from utils.waste_type_config import get_waste_type_names


class TrashcanDetail:
    def __init__(self):
        pass

    def _get_image_root_path(self) -> Path:
        configured_path = os.getenv("IMAGE_PATH", ".")
        return Path(configured_path.strip().strip("\""))

    def _resolve_detection_image_path(self, relative_path: str | None) -> Path | None:
        if not relative_path:
            return None

        image_root = self._get_image_root_path().resolve()
        absolute_path = (image_root / relative_path).resolve()

        try:
            if os.path.commonpath([str(image_root), str(absolute_path)]) != str(image_root):
                return None
        except ValueError:
            return None

        if not absolute_path.is_file():
            return None

        return absolute_path

    async def get_trashcans_detail(self, trashcan_id: int, db: SessionDep):
        await mark_offline_if_stale(db, minutes=5)
        trashcan_stmt = (
            select(Trashcan)
            .where(Trashcan.trashcan_id == trashcan_id)
            .where(Trashcan.is_deleted == False)
        )
        trashcan_row = (await db.execute(trashcan_stmt)).first()
        if not trashcan_row:
            return None

        trashcan = trashcan_row[0]
        capacity = trashcan.trashcan_capacity or 0
        current_volume = trashcan.current_volume or 0
        free_capacity = capacity - current_volume

        total_stmt = (
            select(func.coalesce(func.sum(Detection.object_count), 0))
            .where(Detection.trashcan_id == trashcan_id)
        )
        total_collected = (await db.execute(total_stmt)).scalar() or 0
        events_stmt = (
            select(func.count(Detection.detection_id))
            .where(Detection.trashcan_id == trashcan_id)
        )
        total_events = (await db.execute(events_stmt)).scalar() or 0

        type_stmt = (
            select(
                WasteType.type_name,
                func.count(DetectionDetail.detail_id).label("type_count"),
            )
            .join(DetectionDetail, DetectionDetail.waste_type_id == WasteType.waste_type_id)
            .join(Detection, Detection.detection_id == DetectionDetail.detection_id)
            .where(Detection.trashcan_id == trashcan_id)
            .group_by(WasteType.type_name)
            .order_by(WasteType.type_name.asc())
        )
        type_rows = (await db.execute(type_stmt)).all()
        detect_items = {
            type_name: 0
            for type_name in await get_waste_type_names(db)
        }
        for row in type_rows:
            if row.type_name in detect_items:
                detect_items[row.type_name] += int(row.type_count or 0)

        return {
            "trashcan_id": trashcan.trashcan_id,
            "trashcan_name": trashcan.trashcan_name,
            "address_detail": trashcan.address_detail,
            "is_online": trashcan.is_online,
            "last_connected_at": trashcan.last_connected_at,
            "trashcan_capacity": capacity,
            "current_volume": current_volume,
            "free_capacity": free_capacity,
            "detect_items_response": {
                "total_objects": int(total_collected),
                "total_events": int(total_events),
                "data": detect_items,
            },
        }

    async def get_waste_detail(
        self,
        trashcan_id: int,
        db: SessionDep,
        type_name: str | None,
        offset: int,
        limit: int,
    ):
        trashcan_stmt = (
            select(Trashcan.trashcan_id)
            .where(Trashcan.trashcan_id == trashcan_id)
            .where(Trashcan.is_deleted == False)
        )
        trashcan_exists = (await db.execute(trashcan_stmt)).first()
        if not trashcan_exists:
            return None

        events_stmt = select(func.count(func.distinct(Detection.detection_id))).where(
            Detection.trashcan_id == trashcan_id
        )
        if type_name:
            events_stmt = (
                events_stmt.join(
                    DetectionDetail, DetectionDetail.detection_id == Detection.detection_id
                )
                .join(WasteType, WasteType.waste_type_id == DetectionDetail.waste_type_id)
                .where(WasteType.type_name == type_name)
            )
        total_events = (await db.execute(events_stmt)).scalar() or 0

        objects_stmt = (
            select(func.count(DetectionDetail.detail_id))
            .join(Detection, Detection.detection_id == DetectionDetail.detection_id)
            .where(Detection.trashcan_id == trashcan_id)
        )
        if type_name:
            objects_stmt = (
                objects_stmt.join(
                    WasteType, WasteType.waste_type_id == DetectionDetail.waste_type_id
                )
                .where(WasteType.type_name == type_name)
            )
        total_objects = (await db.execute(objects_stmt)).scalar() or 0

        detail_stmt = (
            select(
                DetectionDetail.detail_id,
                WasteType.type_name,
                Detection.detection_id,
                Detection.image_name,
                Detection.image_path,
                Detection.detected_at,
            )
            .join(DetectionDetail, DetectionDetail.waste_type_id == WasteType.waste_type_id)
            .join(Detection, Detection.detection_id == DetectionDetail.detection_id)
            .where(Detection.trashcan_id == trashcan_id)
        )
        if type_name:
            detail_stmt = detail_stmt.where(WasteType.type_name == type_name)
        detail_stmt = (
            detail_stmt
            .order_by(
                Detection.detected_at.desc(),
                Detection.detection_id.desc(),
                DetectionDetail.detail_id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        detail_rows = (await db.execute(detail_stmt)).all()

        items_by_type = {
            type_name: []
            for type_name in await get_waste_type_names(db)
        }
        for row in detail_rows:
            item = {
                "detail_id": row.detail_id,
                "detection_id": row.detection_id,
                "type_name": row.type_name,
                "image_name": row.image_name,
                "image_path": row.image_path,
                "detected_at": row.detected_at,
            }
            if row.type_name in items_by_type:
                items_by_type[row.type_name].append(item)

        return {
            "trashcan_id": trashcan_id,
            "type_name": type_name,
            "offset": offset,
            "limit": limit,
            "total_objects": int(total_objects),
            "total_events": int(total_events),
            "items_by_type": items_by_type,
        }

    def get_detection_image_by_relative_path(self, image_name: str) -> Path | None:
        relative_path = (Path("detect_img") / image_name).as_posix()
        return self._resolve_detection_image_path(relative_path)
