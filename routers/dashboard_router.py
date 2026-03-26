from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from db.db import SessionDep
from service.dashboard_service import DashboardService

dashboard = APIRouter(prefix="/dashboard")
service = DashboardService()


@dashboard.get("/detections")
async def get_total_detection_count(db: SessionDep):
    result = await service.get_total_detection(db)
    return result

@dashboard.get("/trashcans/full")
async def get_full_trashcans(db: SessionDep):
    result = await service.get_full_trashcans(db)
    return result

@dashboard.get("/charts")
async def get_charts(
    db: SessionDep,
    period: Literal["week", "month", "year"] = Query("week"),
):
    result = await service.get_stats_charts(db, period)
    return result

@dashboard.get("/trashcans/error")
async def get_unconnected_trashcans(db: SessionDep):
    result = await service.get_unconnected_trashcans_list(db)
    return result

@dashboard.get("/trashcans/error/{trashcan_id}")
async def get_trashcan_error_logs(
    trashcan_id: int,
    db: SessionDep,
    limit: int = Query(50, ge=1, le=200),
):
    result = await service.get_trashcan_error_logs(trashcan_id, limit, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Trashcan not found")
    return result

