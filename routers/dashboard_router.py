from fastapi import APIRouter

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
async def get_charts(db: SessionDep):
    result = await service.get_stats_charts(db)
    return result

@dashboard.get("/trashcan/unconnected")
async def get_unconnected_trashcans(db: SessionDep):
    result = await service.get_unconnected_trashcans_list(db)
    return result