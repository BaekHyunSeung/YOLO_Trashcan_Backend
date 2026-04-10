"""서비스 계층에서 공통으로 쓰는 순수 헬퍼(표시용 비율, DB 존재 확인, 이미지 루트)."""

from __future__ import annotations

import os
from pathlib import Path

from sqlmodel import select

from db.db import SessionDep
from db.entity import Trashcan


def cap_fill_rate(value: float | None) -> float:
    """용적 대비 표시용 % (상한 100)."""
    return round(min(value or 0.0, 100.0), 2)


async def trashcan_exists(trashcan_id: int, db: SessionDep) -> bool:
    """삭제되지 않은 쓰레기통 행이 있으면 True."""
    stmt = (
        select(Trashcan.trashcan_id)
        .where(Trashcan.trashcan_id == trashcan_id)
        .where(Trashcan.is_deleted == False)
    )
    return (await db.execute(stmt)).first() is not None


async def trashcan_pk_exists(trashcan_id: int, db: SessionDep) -> bool:
    """PK 행 존재(삭제 여부 무관). 에러 로그 FK 검증 등에 사용."""
    stmt = select(Trashcan.trashcan_id).where(Trashcan.trashcan_id == trashcan_id)
    return (await db.execute(stmt)).first() is not None


def image_storage_root() -> Path:
    """IMAGE_PATH 기준 저장소 루트 (디텍션 이미지 등)."""
    configured_path = os.getenv("IMAGE_PATH", ".")
    return Path(configured_path.strip().strip('"'))
