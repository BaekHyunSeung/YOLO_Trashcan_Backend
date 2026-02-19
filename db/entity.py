from datetime import datetime, date
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import Boolean, Column, text, DateTime

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
    is_online: bool = Field(default=False, sa_column=Column(Boolean, server_default=text("0")))
    last_connected_at: datetime | None = Field(
        default=datetime.now(),
        sa_column=Column(DateTime, server_default=text("CURRENT_TIMESTAMP")),
    )
    is_deleted: bool = Field(default=False, sa_column=Column(Boolean, server_default=text("0")))
    server_url: str | None  

class Detection(SQLModel, table=True):
    __tablename__ = "detection"
    detection_id: int | None = Field(default=None, primary_key=True)
    trashcan_id: int = Field(foreign_key="trashcan.trashcan_id")
    image_name: str | None
    image_path: str | None
    detected_at: datetime | None
    object_count: int | None

class WasteType(SQLModel, table=True):
    __tablename__ = "wastetype"
    waste_type_id: int | None = Field(default=None, primary_key=True)
    type_name: str

class DetectionDetail(SQLModel, table=True):
    __tablename__ = "detection_detail"
    detail_id: int | None = Field(default=None, primary_key=True)
    detection_id: int = Field(foreign_key="detection.detection_id")
    waste_type_id: int = Field(foreign_key="wastetype.waste_type_id")
    confidence: float | None
    bbox_x1: float | None
    bbox_y1: float | None
    bbox_x2: float | None
    bbox_y2: float | None

class DailyStats(SQLModel, table=True):
    __tablename__ = "dailystats"
    stats_id: int | None = Field(default=None, primary_key=True)
    stats_date: date
    trashcan_city: str | None
    waste_type_id: int = Field(foreign_key="wastetype.waste_type_id")
    detection_count: int | None

class TrashcanErrorLog(SQLModel, table=True):
    __tablename__ = "trashcan_error_log"
    id: int | None = Field(default=None, primary_key=True)
    trashcan_id: int = Field(foreign_key="trashcan.trashcan_id")
    camera_id: int | None
    status_code: int
    message: str | None
    occurred_at: datetime | None
    last_occurred_at: datetime | None
    repeat_count: int | None = Field(default=1)
    created_at: datetime | None = Field(
        default=datetime.now(),
        sa_column=Column(DateTime, server_default=text("CURRENT_TIMESTAMP")),
    )