from datetime import datetime, date
from sqlmodel import select
from db.db import SessionDep
from db.entity import Detection, DetectionDetail, DailyStats, Trashcan, WasteType
from models.request import DetectionCreate, DetectionObject, BBox
from service.detection_mapping import camera_to_trashcan_id, class_id_to_type_name

class DetectionService:
    async def detection_mapping(self, data, file, db: SessionDep):
        #camera_id -> trashcan_id 변환
        camera_id = data.get("camera_id")
        trashcan_id = camera_to_trashcan_id(camera_id)

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

        return await self.save_detection(payload, db)

    async def get_waste_type_id(self, type_name: str, db: SessionDep) -> int | None:
        stmt = select(WasteType.waste_type_id).where(WasteType.type_name == type_name)
        return (await db.execute(stmt)).scalar_one_or_none()
    
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
                bbox_info=obj.box.model_dump(),
            )
            db.add(detail)
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
                stats.detection_count += 1
            else:
                db.add(DailyStats(
                    stats_date=date.today(),
                    trashcan_city=trashcan_city,
                    waste_type_id=obj.waste_type_id,
                    detection_count=1,
                ))
        await db.commit()

        return {
            "saved": True,
            "detection_id": detection.detection_id,
            "total_objects": payload.object_count
        }    