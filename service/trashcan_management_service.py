import asyncio
from datetime import datetime
from sqlmodel import select
from sqlalchemy import func
from db.entity import Trashcan, Detection
from db.db import SessionDep
from models.request import TrashcanModify
from models.request import TrashcanCreate
from service.connection_utils import ping_server

class TrashcanManagementService:
    def __init__(self):
        pass

    async def get_trashcans(self, db: SessionDep):
        stmt = (
            select(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                func.coalesce(func.sum(Detection.object_count), 0).label("total_collected"),
            )
            .join(Detection, Detection.trashcan_id == Trashcan.trashcan_id, isouter=True)
            .where(Trashcan.is_deleted == False)
            .group_by(Trashcan.trashcan_id, Trashcan.trashcan_name, Trashcan.address_detail)
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "trashcan_id": row.trashcan_id,
                "trashcan_name": row.trashcan_name,
                "address_detail": row.address_detail,
                "total_collected": int(row.total_collected or 0),
            }
            for row in rows
        ]

    async def get_trashcan_health(self, trashcan_id: int, db: SessionDep):
        stmt = select(Trashcan).where(Trashcan.trashcan_id == trashcan_id)
        trashcan = (await db.execute(stmt)).scalar_one_or_none()
        if not trashcan or not trashcan.server_url:
            return {"trashcan_id": trashcan_id, "status": "error", "message": "Server URL not found"}

        try:
            reachable = await asyncio.to_thread(ping_server, trashcan.server_url)
        except Exception:
            return {"trashcan_id": trashcan_id, "status": "error", "message": "Failed to connect to server"}
        
        if reachable:
            trashcan.is_online = True
            trashcan.last_connected_at = datetime.now()
            await db.commit()
            return {"trashcan_id": trashcan_id, "status": "ok", "message": "Server is healthy"}
        trashcan.is_online = False
        await db.commit()
        return {"trashcan_id": trashcan_id, "status": "error", "message": "Failed to connect to server"}
        

    async def modify_trashcan(self, trashcan: TrashcanModify, db: SessionDep):
        stmt = select(Trashcan).where(Trashcan.trashcan_id == trashcan.trashcan_id)
        target = (await db.execute(stmt)).scalar_one_or_none()
        if not target or target.is_deleted:
            return {"updated": False, "message": "Trashcan not found or deleted"}

        target.trashcan_id = trashcan.trashcan_id
        target.trashcan_name = trashcan.trashcan_name
        target.trashcan_city = trashcan.trashcan_city
        target.address_detail = trashcan.address_detail
        target.trashcan_latitude = trashcan.trashcan_latitude
        target.trashcan_longitude = trashcan.trashcan_longitude
        await db.commit()
        await db.refresh(target)
        return {"updated": True, "trashcan_id": target.trashcan_id, "message": "Trashcan updated successfully"}

    async def delete_trashcan(self, trashcan_id: int, db: SessionDep):
        stmt = select(Trashcan).where(Trashcan.trashcan_id == trashcan_id)
        target = (await db.execute(stmt)).scalar_one_or_none()
        if not target or target.is_deleted:
            return {"deleted": False, "message": "Trashcan not found or deleted"}
        
        target.is_deleted = True
        await db.commit()
        return {"deleted": True, "trashcan_id": target.trashcan_id, "message": "Trashcan deleted successfully"}
    
    async def recover_trashcan(self, trashcan_id: int, db: SessionDep):
        stmt = select(Trashcan).where(Trashcan.trashcan_id == trashcan_id)
        target = (await db.execute(stmt)).scalar_one_or_none()
        if not target or not target.is_deleted:
            return {"recovered": False, "message": "Trashcan not found or not deleted"}
        
        target.is_deleted = False
        await db.commit()
        return {"recovered": True, "trashcan_id": target.trashcan_id, "message": "Trashcan recovered successfully"}

    async def create_trashcan(self, trashcan: TrashcanCreate, db: SessionDep):
        try:
            reachable = await asyncio.to_thread(ping_server, trashcan.server_url)
        except Exception:
            return {"created": False, "message": "Failed to connect to server"}

        if not reachable:
            return {
                "created": False,
                "message": "Failed to connect to server",
            }

        new_trashcan = Trashcan(
            trashcan_name=trashcan.trashcan_name,
            trashcan_capacity=trashcan.trashcan_capacity,
            trashcan_city=trashcan.trashcan_city,
            address_detail=trashcan.address_detail,
            trashcan_latitude=trashcan.trashcan_latitude,
            trashcan_longitude=trashcan.trashcan_longitude,
            server_url=trashcan.server_url,
        )
        db.add(new_trashcan)
        await db.commit()
        await db.refresh(new_trashcan)
        return {
            "created": True,
            "trashcan_id": new_trashcan.trashcan_id,
            "message": "Trashcan created successfully",
        }

    async def get_deleted_trashcans(self, db: SessionDep):
        stmt = (
            select(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                func.coalesce(func.sum(Detection.object_count), 0).label("total_collected"),
            )
            .join(Detection, Detection.trashcan_id == Trashcan.trashcan_id, isouter=True)
            .where(Trashcan.is_deleted == True) 
            .group_by(Trashcan.trashcan_id, Trashcan.trashcan_name, Trashcan.address_detail)
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "trashcan_id": row.trashcan_id,
                "trashcan_name": row.trashcan_name,
                "address_detail": row.address_detail,
                "total_collected": int(row.total_collected or 0),
            }
            for row in rows
        ]

        