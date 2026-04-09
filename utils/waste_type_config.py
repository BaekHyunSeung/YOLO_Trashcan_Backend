from enum import Enum
import os
import re

from sqlalchemy.orm import sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db.entity import WasteType

#기본 설정(환경 변수 없는 경우)
DEFAULT_WASTE_TYPES = {
    1: "MetalCan",
    2: "PetBottle",
    3: "Plastic",
    4: "Styrofoam",
}

#쓰레기타입 환경 변수 패턴
WASTE_TYPE_KEY_PATTERN = re.compile(r"^WASTE_TYPE_(\d+)$")


#쓰레기타입 설정 조회
def get_waste_type_config() -> dict[int, str]:
    #설정된 쓰레기타입 목록
    configured: dict[int, str] = {}

    for key, value in os.environ.items():
        match = WASTE_TYPE_KEY_PATTERN.match(key)
        if not match:
            continue
        type_name = value.strip()
        if not type_name:
            continue
        type_id = int(match.group(1))
        configured[type_id] = type_name

    return configured or DEFAULT_WASTE_TYPES.copy()


def get_class_id_to_waste_type_id_map() -> dict[int, int]:
    raw_mapping = os.getenv("CLASS_ID_TO_WASTE_TYPE_ID", "").strip()
    configured_ids = set(get_waste_type_config().keys())

    if raw_mapping:
        mapping: dict[int, int] = {}
        for item in raw_mapping.split(","):
            pair = item.strip()
            if not pair or ":" not in pair:
                continue
            class_id_text, type_id_text = pair.split(":", 1)
            try:
                class_id = int(class_id_text.strip())
                waste_type_id = int(type_id_text.strip())
            except ValueError:
                continue
            if waste_type_id in configured_ids:
                mapping[class_id] = waste_type_id
        if mapping:
            return mapping

    return {
        type_id - 1: type_id
        for type_id in sorted(configured_ids)
    }


def get_class_id_to_type_name(class_id: int) -> str | None:
    waste_types = get_waste_type_config()
    class_mapping = get_class_id_to_waste_type_id_map()
    waste_type_id = class_mapping.get(class_id)
    if waste_type_id is None:
        return None
    return waste_types.get(waste_type_id)

#쓰레기 타입 enum 조회
def get_waste_type_query_enum() -> type[Enum]:
    return Enum(
        "WasteTypeQueryEnum",
        {
            f"TYPE_{type_id}": type_name
            for type_id, type_name in sorted(get_waste_type_config().items())
        },
        type=str,
    )

#쓰레기타입 동기화
async def sync_waste_types(engine) -> None:
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    #쓰레기타입 설정 조회
    async with async_session_factory() as session:
        configured_types = get_waste_type_config()
        #쓰레기타입 조회
        existing_rows = (
            await session.execute(select(WasteType).order_by(WasteType.waste_type_id.asc()))
        ).scalars().all()
        existing_by_id = {
            row.waste_type_id: row
            for row in existing_rows
            if row.waste_type_id is not None
        }

        changed = False
        for waste_type_id, type_name in configured_types.items():
            existing = existing_by_id.get(waste_type_id)
            if existing is None:
                session.add(
                    WasteType(
                        waste_type_id=waste_type_id,
                        type_name=type_name,
                        is_active=True,
                    )
                )
                changed = True
                continue

            if existing.type_name != type_name:
                existing.type_name = type_name
                changed = True
            if not existing.is_active:
                existing.is_active = True
                changed = True

        configured_ids = set(configured_types.keys())
        for waste_type_id, existing in existing_by_id.items():
            if waste_type_id not in configured_ids and existing.is_active:
                existing.is_active = False
                changed = True

        if changed:
            await session.commit()


async def get_waste_type_names(db, active_only: bool = False) -> list[str]:
    stmt = select(WasteType.type_name).order_by(WasteType.waste_type_id.asc())
    if active_only:
        stmt = stmt.where(WasteType.is_active == True)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)
