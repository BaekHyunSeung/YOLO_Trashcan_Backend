"""
YOLO 탐지 결과를 저장하기 위한 모델 정의.

정규화 구조:
- detections: 이미지 단위 이벤트
- detection_objects: 개별 객체(박스/클래스) 단위
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Detection(Base):
    """이미지 단위 탐지 이벤트."""

    __tablename__ = "detections"

    # 내부 식별자
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 원본 이미지 파일명/경로
    source_image = Column(String(255), nullable=False)
    # 이미지 내 탐지 객체 수
    total_objects = Column(Integer, nullable=False)
    # 탐지 시각 (기본값: 현재 시각)
    detected_at = Column(DateTime, nullable=False, index=True, default=func.now())
    # 생성 시각
    created_at = Column(DateTime, nullable=False, default=func.now())

    # 1:N 관계 (탐지 이벤트 -> 객체들)
    objects = relationship("DetectionObject", back_populates="detection")


class DetectionObject(Base):
    """탐지된 개별 객체(플라스틱/유리/캔/스티로폼 등)."""

    __tablename__ = "detection_objects"

    # 내부 식별자
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 탐지 이벤트 FK
    detection_id = Column(Integer, ForeignKey("detections.id"), nullable=False, index=True)
    # 모델이 예측한 클래스 정보
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(64), nullable=False, index=True)
    # 신뢰도
    confidence = Column(Float, nullable=False)
    # 바운딩 박스 좌표
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    # 생성 시각
    created_at = Column(DateTime, nullable=False, default=func.now())

    # N:1 관계 (객체 -> 탐지 이벤트)
    detection = relationship("Detection", back_populates="objects")
