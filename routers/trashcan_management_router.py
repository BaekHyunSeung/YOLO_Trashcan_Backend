from fastapi import APIRouter
from models.request import TrashcanModify
from models.request import TrashcanCreate
from db.db import SessionDep
from service.trashcan_management_service import TrashcanManagementService
from service.connection_utils import check_trashcan_connection

management = APIRouter(prefix="/management")
service = TrashcanManagementService()

@management.get("/trashcans")
async def get_trashcans(db: SessionDep):
    results = await service.get_trashcans(db)
    return results

@management.get("/trashcans/{trashcan_id}/health")
async def get_trashcan_health(trashcan_id: int, db: SessionDep):
    result = await check_trashcan_connection(trashcan_id, db)
    return result

@management.put("/trashcans")
async def modify_trashcan(trashcan: TrashcanModify, db: SessionDep):
    result = await service.modify_trashcan(trashcan, db)
    return result

@management.delete("/trashcans/{trashcan_id}")
async def delete_trashcan(trashcan_id: int, db: SessionDep):
    result = await service.delete_trashcan(trashcan_id, db)
    return result
@management.put("/trashcans/{trashcan_id}/recover")
async def recover_trashcan(trashcan_id: int, db: SessionDep):
    result = await service.recover_trashcan(trashcan_id, db)
    return result

@management.post("/trashcans")
async def create_trashcan(trashcan: TrashcanCreate, db: SessionDep):
    result = await service.create_trashcan(trashcan, db)    
    return result

@management.get("/trashcans/deleted")
async def get_deleted_trashcans(db: SessionDep):
    results = await service.get_deleted_trashcans(db)
    return results