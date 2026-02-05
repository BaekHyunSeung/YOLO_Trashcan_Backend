from sqlmodel import select
from db.entity import Trashcan
from db.db import SessionDep

class TrashcanMapService:
    def __init__(self):
        pass

    async def get_trashcans_map(self, db: SessionDep):
        statement = select(Trashcan.trashcan_id, Trashcan.trashcan_name, Trashcan.trashcan_latitude, Trashcan.trashcan_longitude)
        result = await db.execute(statement)
        trashcans = result.mappings().all()
        return trashcans