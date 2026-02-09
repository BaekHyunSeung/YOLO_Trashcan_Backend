import asyncio
import urllib.request
from sqlmodel import select
from sqlalchemy import func
from db.entity import Trashcan, Detection, DetectionDetail, WasteType
from db.db import SessionDep

class TrashcanList:
    def __init__(self):
        pass

    async def get_trashcans_list(self, db: SessionDep, offset: int, limit: int):
        stmt = (
            select(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                Trashcan.is_online,
                func.coalesce(func.sum(Detection.object_count), 0).label("total_collected"),
            )
            .join(Detection, Detection.trashcan_id == Trashcan.trashcan_id, isouter=True)
            .where(Trashcan.is_deleted == False)
            .group_by(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                Trashcan.is_online,
            )
            .offset(offset)
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "trashcan_id": row.trashcan_id,
                "trashcan_name": row.trashcan_name,
                "address_detail": row.address_detail,
                "is_online": row.is_online,
                "total_collected": int(row.total_collected or 0),
            }
            for row in rows
        ]
    
    async def get_trashcans_detail(self, trashcan_id: int, db: SessionDep):
        pass

    async def sort_trashcans_list(self, db: SessionDep):
        pass

    async def search_trashcans_list(self, db: SessionDep):
        pass