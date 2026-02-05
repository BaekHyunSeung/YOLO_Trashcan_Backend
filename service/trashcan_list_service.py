from sqlmodel import select
from db.entity import Trashcan
from db.db import SessionDep

class TrashcanList:
    def __init__(self):
        pass

    async def get_trashcans_list(self, db: SessionDep):
        statement = select(
            Trashcan.trashcan_id,
            Trashcan.trashcan_name,
            Trashcan.address_detail,
            Trashcan.trashcan_capacity
        )
        result = await db.execute(statement)
        trashcans = result.mappings().all()
        return trashcans
    
    async def get_trashcans_detail(self, trashcan_id: int):
        pass

    async def sort_trashcans_list(self, db: SessionDep):
        pass

    async def search_trashcans_list(self, db: SessionDep):
        pass