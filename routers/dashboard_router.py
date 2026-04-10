from datetime import date
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
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    if (start_date is None) != (end_date is None):
        raise HTTPException(
            status_code=400,
            detail="start_date 와 end_date 모두 입력해야합니다다.",
        )
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date는 end_date보다 이전이어야 합니다.",
        )

    result = await service.get_stats_charts(db, period, start_date, end_date)
    return result

@dashboard.get("/trashcans/error")
async def get_unconnected_trashcans(db: SessionDep):
    result = await service.get_unconnected_trashcans_list(db)
    return result

@dashboard.get("/trashcans/error/unregistered")
async def get_unregistered_trashcan_error_logs(
    db: SessionDep,
    limit: int = Query(50, ge=1, le=200),
):
    result = await service.get_unregistered_trashcan_error_logs(limit, db)
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

