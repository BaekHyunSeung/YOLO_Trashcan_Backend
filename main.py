"""
FastAPI 진입점.

- /detections: YOLO 결과 저장
- /health: 헬스체크
"""

from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from model import Detection, DetectionObject

# FastAPI 앱 인스턴스 (자동 문서화 포함)
app = FastAPI(title="Trash Detection API")


class BoxSchema(BaseModel):
    """바운딩 박스 좌표."""

    x1: float
    y1: float
    x2: float
    y2: float


class PredictionSchema(BaseModel):
    """YOLO 예측 결과의 단일 객체 스키마."""

    class_id: int
    class_name: str
    confidence: float
    box: BoxSchema


class DetectionIn(BaseModel):
    """탐지 이벤트 입력 스키마 (이미지 단위)."""

    source_image: str
    detected_at: Optional[datetime] = None
    total_objects: Optional[int] = None
    predictions: List[PredictionSchema]


def get_db():
    """요청마다 DB 세션을 생성/종료하는 의존성."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    """앱 시작 시 테이블 자동 생성."""

    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    """헬스체크."""

    return {"status": "ok"}


@app.post("/detections")
def create_detection(payload: DetectionIn, db: Session = Depends(get_db)) -> dict:
    """탐지 이벤트를 저장하고 생성된 ID를 반환."""

    # 탐지 시각이 없으면 현재 시각으로 대체
    detected_at = payload.detected_at or datetime.utcnow()
    # total_objects가 없으면 predictions 길이로 계산
    total_objects = payload.total_objects
    if total_objects is None:
        total_objects = len(payload.predictions)

    # 이미지 단위 이벤트 저장
    detection = Detection(
        source_image=payload.source_image,
        total_objects=total_objects,
        detected_at=detected_at,
    )
    db.add(detection)
    db.flush()

    # 예측 객체들을 개별로 저장
    for pred in payload.predictions:
        obj = DetectionObject(
            detection_id=detection.id,
            class_id=pred.class_id,
            class_name=pred.class_name,
            confidence=pred.confidence,
            x1=pred.box.x1,
            y1=pred.box.y1,
            x2=pred.box.x2,
            y2=pred.box.y2,
        )
        db.add(obj)

    # 트랜잭션 커밋
    db.commit()
    return {"detection_id": detection.id, "total_objects": total_objects}
