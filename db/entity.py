from datetime import datetime, date
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import Column, JSON

class Trashcan(SQLModel, table=True):
    __tablename__ = "trashcan"
    trashcan_id: int | None = Field(default=None, primary_key=True)
    trashcan_name: str | None
    trashcan_capacity: int | None
    current_volume: int | None
    trashcan_city: str | None
    address_detail: str | None
    trashcan_latitude: float | None
    trashcan_longitude: float | None
    is_online: bool = True
    last_connected_at: datetime = Field(default_factory=datetime.now)

class Detection(SQLModel, table=True):
    __tablename__ = "detection"
    detection_id: int | None = Field(default=None, primary_key=True)
    trashcan_id: int = Field(foreign_key="trashcan.trashcan_id")
    image_name: str | None
    image_path: str | None
    detected_at: datetime | None
    object_count: int | None

class WasteType(SQLModel, table=True):
    __tablename__ = "waste_type"
    waste_type_id: int | None = Field(default=None, primary_key=True)
    type_name: str

class DetectionDetail(SQLModel, table=True):
    __tablename__ = "detection_detail"
    detail_id: int | None = Field(default=None, primary_key=True)
    detection_id: int = Field(foreign_key="detection.detection_id")
    waste_type_id: int = Field(foreign_key="waste_type.waste_type_id")
    confidence: float | None
    bbox_info: dict | None = Field(default=None, sa_column=Column(JSON))

class DailyStats(SQLModel, table=True):
    __tablename__ = "daily_stats"
    stats_id: int | None = Field(default=None, primary_key=True)
    stats_date: date
    trashcan_city: str | None
    waste_type_id: int = Field(foreign_key="waste_type.waste_type_id")
    detection_count: int | None