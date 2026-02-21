from service.trashcan_status_utils import mark_offline_if_stale

from sqlmodel import select
from sqlalchemy import func
from db.entity import Trashcan, Detection, DetectionDetail, WasteType
from db.db import SessionDep


class TrashcanDetail:
    def __init__(self):
        pass

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
            "MetalCan": 0,
            "PetBottle": 0,
            "Plastic": 0,
            "Styrofoam": 0,
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

    async def get_waste_detail(self, trashcan_id: int, db: SessionDep):
        trashcan_stmt = (
            select(Trashcan.trashcan_id)
            .where(Trashcan.trashcan_id == trashcan_id)
            .where(Trashcan.is_deleted == False)
        )
        trashcan_exists = (await db.execute(trashcan_stmt)).first()
        if not trashcan_exists:
            return None

        events_stmt = (
            select(func.count(Detection.detection_id))
            .where(Detection.trashcan_id == trashcan_id)
        )
        total_events = (await db.execute(events_stmt)).scalar() or 0

        detail_stmt = (
            select(
                WasteType.type_name,
                Detection.detection_id,
                Detection.image_name,
                Detection.image_path,
                Detection.detected_at,
            )
            .join(DetectionDetail, DetectionDetail.waste_type_id == WasteType.waste_type_id)
            .join(Detection, Detection.detection_id == DetectionDetail.detection_id)
            .where(Detection.trashcan_id == trashcan_id)
            .order_by(Detection.detected_at.desc())
        )
        detail_rows = (await db.execute(detail_stmt)).all()

        items_by_type = {
            "MetalCan": [],
            "PetBottle": [],
            "Plastic": [],
            "Styrofoam": [],
        }
        for row in detail_rows:
            if row.type_name in items_by_type:
                items_by_type[row.type_name].append(
                    {
                        "detection_id": row.detection_id,
                        "image_name": row.image_name,
                        "image_path": row.image_path,
                        "detected_at": row.detected_at,
                    }
                )

        return {
            "trashcan_id": trashcan_id,
            "total_objects": len(detail_rows),
            "total_events": int(total_events),
            "items_by_type": items_by_type,
        }
