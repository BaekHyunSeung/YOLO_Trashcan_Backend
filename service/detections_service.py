from datetime import datetime, date
from sqlmodel import select
from db.db import SessionDep
from db.entity import Detection, DetectionDetail, DailyStats, Trashcan, WasteType
from models.request import DetectionCreate


class DetectionService:
    async def save_detection(self, payload: DetectionCreate, db: SessionDep):
        pass
