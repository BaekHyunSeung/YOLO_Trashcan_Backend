from sqlmodel import select
from db.entity import Trashcan
from db.db import SessionDep

class TrashcanMapService:
    def __init__(self):
        pass

    async def get_trashcans_map(self, db: SessionDep):
        statement = select(
            Trashcan.trashcan_id,
            Trashcan.trashcan_name,
            Trashcan.trashcan_latitude,
            Trashcan.trashcan_longitude,
            Trashcan.is_deleted,
        )
        result = await db.execute(statement)
        trashcans = result.mappings().all()
        active = []
        deleted = []
        for row in trashcans:
            item = {
                "trashcan_id": row["trashcan_id"],
                "trashcan_name": row["trashcan_name"],
                "trashcan_latitude": row["trashcan_latitude"],
                "trashcan_longitude": row["trashcan_longitude"],
            }
            if row["is_deleted"]:
                deleted.append(item)
            else:
                active.append(item)
        return {"active": active, "deleted": deleted}