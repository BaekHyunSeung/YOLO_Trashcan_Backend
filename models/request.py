from datetime import datetime

from pydantic import BaseModel

class TrashcanModify(BaseModel):
    trashcan_id: int
    trashcan_name: str
    trashcan_city: str
    address_detail: str
    trashcan_latitude: float
    trashcan_longitude: float

class TrashcanCreate(BaseModel):
    trashcan_name: str
    trashcan_capacity: int
    trashcan_city: str
    address_detail: str
    trashcan_latitude: float
    trashcan_longitude: float
    server_url: str | None = None

class Trashcan(BaseModel):
    trashcan_id: int
    trashcan_name: str
    trashcan_capacity: int
    trashcan_city: str
    address_detail: str
    trashcan_latitude: float
    trashcan_longitude: float
    is_online: bool
    last_connected_at: datetime

class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class DetectionObject(BaseModel):
    waste_type_id: int
    type_name: str
    confidence: float
    box: BBox

class DetectionCreate(BaseModel):
    trashcan_id: int
    filename: str
    saved_path: str
    object_count: int
    objects: list[DetectionObject]

class DetectionMetadataItem(BaseModel):
    class_id: int
    bbox: list[float]
    score: float

class DetectionMetadata(BaseModel):
    camera_id: int
    frame_id: str | None = None
    detections: list[DetectionMetadataItem] = []
    timestamp: str | None = None