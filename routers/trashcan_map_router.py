from fastapi import FastAPI, Depends, APIRouter
from db.db import SessionDep
from service.trashcan_map_service import TrashcanMapService

map = APIRouter(prefix="/map")
service = TrashcanMapService()

@map.get("/trashcans")
async def get_trashcans(db: SessionDep):
    results = await service.get_trashcans_map(db)
    return results