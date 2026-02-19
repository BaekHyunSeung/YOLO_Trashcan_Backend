from datetime import datetime, date, timedelta
from sqlmodel import select
from db.db import SessionDep
from db.entity import Detection, DetectionDetail, DailyStats, Trashcan, WasteType
from models.request import DetectionCreate, DetectionObject, BBox
from fastapi import HTTPException

def class_id_to_type_name(class_id: int) -> str | None:
    mapping = {
        0: "MetalCan",
        1: "PetBottle",
        2: "Plastic",
        3: "Styrofoam",
    }
    return mapping.get(class_id)

class DetectionService:
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
            trashcan_id = await self.get_trashcan_id(camera_id, db)
        if trashcan_id is None:
            camera_id = data.get("camera_id")
            raise HTTPException(
                status_code=400,
                detail=f"알 수 없는 trashcan_id / 받은 camera_id: {camera_id}",
            )
        await self.update_trashcan_online(trashcan_id, db)

        objects = []
        for d in data.get("detections", []):
            class_id = d.get("class_id")
            bbox = d.get("bbox", [0,0,0,0])
            score = d.get("score", 0.0)

            type_name = class_id_to_type_name(class_id)
            if type_name is None:
                continue

            waste_type_id = await self.get_waste_type_id(type_name, db)
            if waste_type_id is None:
                continue 

            obj = DetectionObject(
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
            objects.append(obj)

        payload = DetectionCreate(
            trashcan_id=trashcan_id,
            filename=file.filename,
            saved_path=f"detect_img/{file.filename}",
            object_count=len(objects),
            objects=objects,
        )

        await self.save_detection(payload, db)
        return None

    async def get_waste_type_id(self, type_name: str, db: SessionDep) -> int | None:
        stmt = select(WasteType.waste_type_id).where(WasteType.type_name == type_name)
        return (await db.execute(stmt)).scalar_one_or_none()

    async def get_trashcan_id(self, trashcan_id_value: int | str | None, db: SessionDep) -> int | None:
        if trashcan_id_value is None:
            return None
        try:
            trashcan_id = int(trashcan_id_value)
        except (TypeError, ValueError):
            return None
        stmt = select(Trashcan.trashcan_id).where(Trashcan.trashcan_id == trashcan_id)
        return (await db.execute(stmt)).scalar_one_or_none()

    async def update_trashcan_online(self, trashcan_id: int, db: SessionDep) -> None:
        stmt = select(Trashcan).where(Trashcan.trashcan_id == trashcan_id)
        target = (await db.execute(stmt)).scalar_one_or_none()
        if not target:
            return
        target.is_online = True
        target.last_connected_at = datetime.now()
        await db.commit()
    
    async def save_detection(self, payload: DetectionCreate, db: SessionDep):
        #detection 저장
        detection = Detection(
            trashcan_id=payload.trashcan_id,
            image_name=payload.filename,
            image_path=payload.saved_path,
            detected_at=datetime.now(),
            object_count=payload.object_count,
        )
        db.add(detection)
        await db.commit()
        await db.refresh(detection)

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

        #trashcan 수거량 업데이트
        target_trashcan = (
            await db.execute(
                select(Trashcan).where(Trashcan.trashcan_id == payload.trashcan_id)
            )
        ).scalar_one_or_none()
        if target_trashcan:
            target_trashcan.current_volume = (target_trashcan.current_volume or 0) + payload.object_count
            await db.commit()

        #trashcan_city 조회
        trashcan_city = (
            await db.execute(
                select(Trashcan.trashcan_city).where(Trashcan.trashcan_id == payload.trashcan_id)
            )
        ).scalar_one()

        #daily_stats 저장
        for obj in payload.objects:
            daily = select(DailyStats).where(
                DailyStats.stats_date == date.today(),
                DailyStats.trashcan_city == trashcan_city,
                DailyStats.waste_type_id == obj.waste_type_id,
            )
            stats = (await db.execute(daily)).scalar_one_or_none()
            if stats:
                stats.detection_count = (stats.detection_count or 0) + 1
            else:
                db.add(DailyStats(
                    stats_date=date.today(),
                    trashcan_city=trashcan_city,
                    waste_type_id=obj.waste_type_id,
                    detection_count=1,
                ))
        await db.commit()