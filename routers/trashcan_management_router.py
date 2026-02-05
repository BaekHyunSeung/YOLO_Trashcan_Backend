from fastapi import Depends, FastAPI, HTTPException, APIRouter
from models.request import TrashcanModify
from models.request import TrashcanCreate
from db.db import SessionDep
from service.trashcan_management_service import TrashcanManagementService

management = APIRouter(prefix="/management")
service = TrashcanManagementService()

@management.get("/trashcans")
async def get_trashcans(db: SessionDep):
    results = await service.get_trashcans(db)
    return results

@management.get("/trashcans/{trashcan_id}/health")
async def get_trashcan_health(trashcan_id):
    result = await service.get_trashcan_health(trashcan_id)
    return result

@management.put("/trashcans")
async def modify_trashcan(trashcan: TrashcanModify):
    result = await service.modify_trashcan(trashcan)
    return result

@management.delete("/trashcans/{trashcan_id}")
async def delete_trashcan(trashcan_id: int):
    result = await service.delete_trashcan(trashcan_id)
    return result

@management.post("/trashcans")
async def create_trashcan(trashcan: TrashcanCreate):
    result = await service.create_trashcan(trashcan)    
    return result