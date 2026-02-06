from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import json
from db.db import SessionDep
from service.detections_service import DetectionService

detections = APIRouter(prefix="/detect")
service = DetectionService()

@detections.post("/result")
async def receive_detection(
    db: SessionDep,
    file: UploadFile = File(...),
    metadata: str = Form(...),
):
    try:
        data = json.loads(metadata)
    except Exception:
        raise HTTPException(status_code=400, detail="파싱 실패")

    return await service.detection_mapping(data, file, db)


