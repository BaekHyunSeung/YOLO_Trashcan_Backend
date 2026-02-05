from fastapi import FastAPI, APIRouter, Depends, HTTPException
from db.db import SessionDep
from service.trashcan_list_service import TrashcanList

trashcans_list = APIRouter(prefix="/trashcans_list")
service = TrashcanList()

#목록 조회
@trashcans_list.get("/trashcans")
async def list_trashcans(db: SessionDep):
    results = await service.get_trashcans_list(db)
    return results

#자세히보기
@trashcans_list.get("/trashcans/{trashcan_id}")
async def get_trashcan(trashcan_id):
    result = await service.get_trashcans_detail(trashcan_id)
    return result

#정렬
@trashcans_list.get("/trashcans/sorting")
async def sort_trashcans(db: SessionDep):
    results = await service.sort_trashcans_list(db)
    return results

#검색
@trashcans_list.get("/trashcans/search")
async def search_trashcans(db: SessionDep):
    results = await service.search_trashcans_list(db)
    return results