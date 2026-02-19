from fastapi import APIRouter, HTTPException
from db.db import SessionDep
from service.trashcan_detail_service import TrashcanDetail

trashcans_detail = APIRouter(prefix="/trashcans_detail")
service = TrashcanDetail()

#연결 테스트
@trashcans_detail.get("/{trashcan_id}/connection-test")
async def test_trashcan_connection(trashcan_id: int, db: SessionDep):
    result = await service.test_trashcan_connection(trashcan_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Trashcan not found")
    return result

#자세히보기
@trashcans_detail.get("/{trashcan_id}")
async def get_trashcan(trashcan_id: int, db: SessionDep):
    result = await service.get_trashcans_detail(trashcan_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Trashcan not found")
    return result

#쓰레기 상세 데이터
@trashcans_detail.get("/{trashcan_id}/waste-detail")
async def get_trashcan_waste_detail(trashcan_id: int, db: SessionDep):
    result = await service.get_waste_detail(trashcan_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Trashcan not found")
    return result
