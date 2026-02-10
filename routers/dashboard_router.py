from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from db.db import SessionDep
from service.dashboard_service import DashboardService

dashboard = APIRouter(prefix="/dashboard")
service = DashboardService()


class TrashcanErrorLog(BaseModel):
    status_code: int
    message: str | None = None
    occurred_at: str | None = None

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

@dashboard.get("/trashcan/unconnected")
async def get_unconnected_trashcans(db: SessionDep):
    result = await service.get_unconnected_trashcans_list(db)
    return result

@dashboard.get("/trashcan/unconnected/{trashcan_id}/log")
async def get_unconnected_trashcan_log(
    trashcan_id: int,
    db: SessionDep,
    limit: int = 50,
):
    result = await service.get_unconnected_trashcan_log(trashcan_id, limit, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Trashcan not found")
    return result


@dashboard.post("/trashcan/unconnected/{trashcan_id}/log")
async def create_unconnected_trashcan_log(
    trashcan_id: int,
    payload: TrashcanErrorLog,
    db: SessionDep,
):
    result = await service.save_unconnected_trashcan_log(
        trashcan_id,
        payload.status_code,
        payload.message,
        payload.occurred_at,
        db,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Trashcan not found")
    return result