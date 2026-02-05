from datetime import datetime

from pydantic import BaseModel

class TrashcanMap(BaseModel):
    trashcan_id: int
    trashcan_name: str
    trashcan_latitude: float
    trashcan_longitude: float