from fastapi import APIRouter
from db.db import SessionDep
from models.request import DetectionCreate
from service.detections_service import DetectionService

detections = APIRouter(prefix="/detections")
service = DetectionService()

@detections.post("/")
async def save_detection(payload: DetectionCreate, db: SessionDep):
    return await service.save_detection(payload, db)