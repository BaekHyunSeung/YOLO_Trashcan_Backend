import json

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import ValidationError
from db.db import SessionDep
from models.request import DetectionMetadata
from service.detections_service import DetectionService
from service.dashboard_service import DashboardService

detections = APIRouter(prefix="/detect")
service = DetectionService()
log_service = DashboardService()

@detections.post("/result", status_code=204)
async def receive_detection(
    db: SessionDep,
    file: UploadFile = File(...),
    metadata: str = Form(...),
):
    try:
        parsed = DetectionMetadata.model_validate_json(metadata)
    except ValidationError as exc:
        camera_id = None
        try:
            meta_obj = json.loads(metadata)
            camera_id = meta_obj.get("camera_id")
        except (TypeError, ValueError, json.JSONDecodeError):
            camera_id = None
        trashcan_id = None
        if camera_id is not None:
            trashcan_id = await service.get_trashcan_id(camera_id, db)
        error_messages = []
        for err in exc.errors():
            loc = err.get("loc", [])
            loc_str = ".".join(str(part) for part in loc)
            msg = err.get("msg", "validation error")
            input_value = err.get("input")
            error_messages.append(f"{loc_str}: {msg} (input={input_value})")
        message = "; ".join(error_messages) if error_messages else "metadata validation error"
        await log_service.save_trashcan_error_log(
            trashcan_id,
            camera_id,
            422,
            message,
            None,
            db,
        )
        raise HTTPException(status_code=422, detail=exc.errors())
    payload = parsed.model_dump()
    camera_id = payload.get("camera_id")
    trashcan_id = await service.get_trashcan_id(camera_id, db)
    try:
        await service.detection_mapping(payload, file, db, trashcan_id=trashcan_id) 
    except HTTPException as exc:
        await log_service.save_trashcan_error_log(
            trashcan_id,
            camera_id,
            exc.status_code,
            str(exc.detail),
            payload.get("timestamp"),
            db,
        )
        raise
    except Exception as exc:
        await log_service.save_trashcan_error_log(
            trashcan_id,
            camera_id,
            500,
            str(exc),
            payload.get("timestamp"),
            db
        )
        raise
    return None


