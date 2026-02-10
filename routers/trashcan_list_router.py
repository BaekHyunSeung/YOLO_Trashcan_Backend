from typing import Literal
from fastapi import APIRouter, Query
from db.db import SessionDep
from service.trashcan_list_service import TrashcanList

trashcans_list = APIRouter(prefix="/trashcans_list")
service = TrashcanList()

#목록 조회
@trashcans_list.get("/trashcans")
async def list_trashcans(db: SessionDep, offset: int = 0, limit: int = 20):
    results = await service.get_trashcans_list(db, offset, limit)
    return results

#정렬
@trashcans_list.get("/sorting")
async def sort_trashcans(
    db: SessionDep,
    sort_by: Literal["collected", "free_capacity", "fill_rate", "is_online"] = Query(
        "collected"
    ),
    order: Literal["asc", "desc"] = Query("desc"),
    city: str | None = Query(None),
    name: str | None = Query(None),
    offset: int = 0,
    limit: int = 20,
):
    results = await service.sort_trashcans_list(
        db, sort_by, order, city, name, offset, limit
    )
    return results

#검색
@trashcans_list.get("/search")
async def search_trashcans(
    db: SessionDep,
    city: str | None = Query(None),
    name: str | None = Query(None),
    offset: int = 0,
    limit: int = 20,
):
    results = await service.search_trashcans_list(db, city, name, offset, limit)
    return results