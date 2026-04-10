from pydantic import BaseModel, Field

#---------------------------------
## 메타데이터 검증(JSON 검증)
# 디텍션 메타데이터 항목(세부정보)
class DetectionMetadataItem(BaseModel):
    class_id: int
    bbox: list[float]
    score: float

# 디텍션 메타데이터 요청(JSON 검증)
class DetectionMetadata(BaseModel):
    camera_id: int
    frame_id: str | None = None
    detections: list[DetectionMetadataItem] = []
    timestamp: str | None = None    
#---------------------------------
## 메타데이터 가공
# 박스 정보(세부정보)
class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

# 디텍션 객체 정보(세부정보)
class DetectionObject(BaseModel):
    waste_type_id: int
    type_name: str
    confidence: float
    box: BBox

# 메타데이터 정리(디텍션 생성 요청)
class DetectionCreate(BaseModel):
    trashcan_id: int
    filename: str | None = None
    saved_path: str | None = None
    object_count: int
    objects: list[DetectionObject]
#---------------------------------
## 쓰레기통 관리 요청
# 쓰레기통 생성 요청
class TrashcanCreate(BaseModel):
    """trashcan_id 생략 시 DB 자동 증가. 지정 시 카메라 ID와 동일한 PK로 등록 가능(미사용 ID만)."""
    trashcan_id: int | None = Field(default=None, ge=1)
    trashcan_name: str
    trashcan_capacity: int
    trashcan_city: str
    address_detail: str
    trashcan_latitude: float
    trashcan_longitude: float
    server_url: str | None = None

# 쓰레기통 수정 요청
class TrashcanModify(BaseModel):
    trashcan_id: int
    trashcan_name: str
    trashcan_city: str
    address_detail: str
    trashcan_latitude: float
    trashcan_longitude: float

