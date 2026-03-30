from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from db.db import SessionDep
from utils.connection_utils import check_trashcan_connection
from service.trashcan_detail_service import TrashcanDetail
from utils.waste_type_config import get_waste_type_query_enum

trashcans_detail = APIRouter()
service = TrashcanDetail()
WasteTypeQueryEnum = get_waste_type_query_enum()

#연결 테스트
@trashcans_detail.get("/trashcans_detail/{trashcan_id}/connection-test")
async def test_trashcan_connection(trashcan_id: int, db: SessionDep):
    return await check_trashcan_connection(trashcan_id, db)

#자세히보기
@trashcans_detail.get("/trashcans_detail/{trashcan_id}")
async def get_trashcan(trashcan_id: int, db: SessionDep):
    result = await service.get_trashcans_detail(trashcan_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Trashcan not found")
    return result

#쓰레기 상세 데이터
@trashcans_detail.get("/trashcans_detail/{trashcan_id}/waste-detail")
async def get_trashcan_waste_detail(
    trashcan_id: int,
    db: SessionDep,
    type_name: WasteTypeQueryEnum | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    selected_type_name = type_name.value if type_name else None
    result = await service.get_waste_detail(trashcan_id, db, selected_type_name, offset, limit)
    if result is None:
        raise HTTPException(status_code=404, detail="Trashcan not found")
    return result


@trashcans_detail.get("/trashcans_detail/{trashcan_id}/waste-detail/{detection_id}")
async def get_trashcan_waste_image(
    trashcan_id: int,
    detection_id: int,
    db: SessionDep,
):
    image_path = await service.get_detection_image_path(trashcan_id, detection_id, db)
    if image_path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)


@trashcans_detail.get("/detect_img/{image_name:path}")
async def get_trashcan_waste_image_by_path(image_name: str):
    image_path = service.get_detection_image_by_relative_path(image_name)
    if image_path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)
