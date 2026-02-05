from sqlmodel import select
from db.entity import Trashcan
from db.db import SessionDep
from models.request import TrashcanModify
from models.request import TrashcanCreate

class TrashcanManagementService:
    def __init__(self):
        pass

    async def get_trashcans(self, db: SessionDep):
        pass

    async def get_trashcan_health(self, trashcan_id: int):
        pass

    async def modify_trashcan(self, trashcan: TrashcanModify):
        pass

    async def delete_trashcan(self, trashcan_id: int):
        pass

    async def create_trashcan(self, trashcan: TrashcanCreate):
        pass