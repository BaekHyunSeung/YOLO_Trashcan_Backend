from datetime import date, timedelta, datetime

from sqlmodel import select
from sqlalchemy import case, func, desc, exists
from db.entity import DetectionDetail, WasteType, Trashcan, DailyStats, TrashcanErrorLog, Detection
from utils.trashcan_status_utils import mark_offline_if_stale
from utils.waste_type_config import get_waste_type_names
from db.db import SessionDep

class DashboardService:
    def __init__(self):
        pass

    def _cap_fill_rate(self, value: float | None) -> float:
        return round(min(value or 0.0, 100.0), 2)

    async def _ensure_trashcan_exists(self, trashcan_id: int, db: SessionDep) -> bool:
        stmt = (
            select(Trashcan.trashcan_id)
            .where(Trashcan.trashcan_id == trashcan_id)
            .where(Trashcan.is_deleted == False)
        )
        return (await db.execute(stmt)).first() is not None

    async def get_total_detection(self, db: SessionDep):
        total_objects_stmt = (
            select(func.count(DetectionDetail.detail_id))
            .join(WasteType, WasteType.waste_type_id == DetectionDetail.waste_type_id)
            .where(WasteType.is_active == True)
        )
        total_objects = (await db.execute(total_objects_stmt)).scalar() or 0

        total_events_stmt = (
            select(func.count(func.distinct(Detection.detection_id)))
            .join(DetectionDetail, DetectionDetail.detection_id == Detection.detection_id)
            .join(WasteType, WasteType.waste_type_id == DetectionDetail.waste_type_id)
            .where(WasteType.is_active == True)
        )
        total_events = (await db.execute(total_events_stmt)).scalar() or 0

        type_stmt = (
            select(
                WasteType.type_name,
                func.count(DetectionDetail.detail_id).label("type_count"),
            )
            .join(DetectionDetail, DetectionDetail.waste_type_id == WasteType.waste_type_id)
            .where(WasteType.is_active == True)
            .group_by(WasteType.type_name)
            .order_by(WasteType.type_name.asc())
        )
        type_rows = (await db.execute(type_stmt)).all()

        items_by_type = {
            type_name: 0
            for type_name in await get_waste_type_names(db, active_only=True)
        }
        for row in type_rows:
            if row.type_name in items_by_type:
                items_by_type[row.type_name] += int(row.type_count or 0)

        return {
            "total_objects": int(total_objects),
            "total_events": int(total_events),
            "items_by_type": items_by_type,
        }

    async def get_full_trashcans(self, db: SessionDep):
        fill_rate = (
            (func.coalesce(Trashcan.current_volume, 0) * 100.0)
            / func.nullif(Trashcan.trashcan_capacity, 0)
        ).label("fill_rate")
        status_order = case(
            (fill_rate >= 90, 1),
            (fill_rate >= 50, 2),
            else_=3,
        ).label("status_order")

        stmt = (
            select(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                fill_rate,
            )
            .where(Trashcan.is_deleted == False)
            .order_by(status_order.asc(), fill_rate.desc(), Trashcan.trashcan_id.asc())
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "trashcan_id": row.trashcan_id,
                "trashcan_name": row.trashcan_name,
                "fill_rate": self._cap_fill_rate(row.fill_rate),
            }
            for row in rows
        ]

    async def get_stats_charts(
        self,
        db: SessionDep,
        period: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        today = date.today()
        selected_period = period
        if start_date and end_date:
            selected_period = "custom"
        else:
            end_date = today
            if period == "month":
                start_date = date(today.year, today.month, 1)
            elif period == "year":
                start_date = date(today.year, 1, 1)
            else:
                start_date = today - timedelta(days=today.weekday())

        total_stmt = (
            select(func.coalesce(func.sum(DailyStats.detection_count), 0))
            .join(WasteType, WasteType.waste_type_id == DailyStats.waste_type_id)
            .where(DailyStats.stats_date >= start_date)
            .where(DailyStats.stats_date <= end_date)
            .where(WasteType.is_active == True)
        )
        total_count = (await db.execute(total_stmt)).scalar() or 0

        type_stmt = (
            select(
                WasteType.type_name,
                func.coalesce(func.sum(DailyStats.detection_count), 0).label("type_count"),
            )
            .join(WasteType, WasteType.waste_type_id == DailyStats.waste_type_id)
            .where(DailyStats.stats_date >= start_date)
            .where(DailyStats.stats_date <= end_date)
            .where(WasteType.is_active == True)
            .group_by(WasteType.type_name)
            .order_by(WasteType.type_name.asc())
        )
        type_rows = (await db.execute(type_stmt)).all()

        items_by_type = {
            type_name: 0
            for type_name in await get_waste_type_names(db, active_only=True)
        }
        for row in type_rows:
            if row.type_name in items_by_type:
                items_by_type[row.type_name] += int(row.type_count or 0)

        city_stmt = (
            select(
                DailyStats.trashcan_city,
                func.coalesce(func.sum(DailyStats.detection_count), 0).label("city_count"),
            )
            .join(WasteType, WasteType.waste_type_id == DailyStats.waste_type_id)
            .where(DailyStats.stats_date >= start_date)
            .where(DailyStats.stats_date <= end_date)
            .where(WasteType.is_active == True)
            .group_by(DailyStats.trashcan_city)
            .order_by(DailyStats.trashcan_city.asc())
        )
        city_rows = (await db.execute(city_stmt)).all()
        items_by_city = {}
        for row in city_rows:
            key = row.trashcan_city or "unknown"
            items_by_city[key] = int(row.city_count or 0)

        return {
            "period": selected_period,
            "start_date": start_date,
            "end_date": end_date,
            "total_count": int(total_count),
            "items_by_type": items_by_type,
            "items_by_city": items_by_city,
        }

    async def get_unconnected_trashcans_list(self, db: SessionDep):
        await mark_offline_if_stale(db, minutes=5)
        cutoff = datetime.now() - timedelta(minutes=1)
        error_exists = exists(
            select(TrashcanErrorLog.id).where(
                TrashcanErrorLog.trashcan_id == Trashcan.trashcan_id,
                (
                    (TrashcanErrorLog.last_occurred_at >= cutoff)
                    | (TrashcanErrorLog.created_at >= cutoff)
                ),
            )
        )
        stmt = (
            select(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                Trashcan.last_connected_at,
            )
            .where(Trashcan.is_deleted == False)
            .where((Trashcan.is_online == False) | error_exists)
            .order_by(Trashcan.last_connected_at.desc(), Trashcan.trashcan_id.asc())
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "trashcan_id": row.trashcan_id,
                "trashcan_name": row.trashcan_name,
                "address_detail": row.address_detail,
                "last_connected_at": row.last_connected_at,
            }
            for row in rows
        ]

    async def get_trashcan_error_logs(
        self, trashcan_id: int, limit: int, db: SessionDep
    ):
        if not await self._ensure_trashcan_exists(trashcan_id, db):
            return None

        stmt = (
            select(TrashcanErrorLog)
            .where(TrashcanErrorLog.trashcan_id == trashcan_id)
            .order_by(desc(TrashcanErrorLog.created_at), desc(TrashcanErrorLog.id))
        )
        if limit > 0:
            stmt = stmt.limit(limit)
        rows = (await db.execute(stmt)).scalars().all()
        logs = [
            {
                "trashcan_id": row.trashcan_id,
                "camera_id": row.camera_id,
                "status_code": row.status_code,
                "message": row.message,
                "occurred_at": row.occurred_at,
                "last_occurred_at": row.last_occurred_at,
                "repeat_count": row.repeat_count,
                "created_at": row.created_at,
            }
            for row in rows
        ]
        return {"trashcan_id": trashcan_id, "logs": logs}
