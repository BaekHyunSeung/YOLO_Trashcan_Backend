from datetime import date, timedelta, datetime

from sqlmodel import select
from sqlalchemy import case, func, desc, exists
from db.entity import DetectionDetail, WasteType, Trashcan, DailyStats, TrashcanErrorLog, Detection
from service.trashcan_status_utils import mark_offline_if_stale
from db.db import SessionDep

class DashboardService:
    def __init__(self):
        pass

    async def _ensure_trashcan_exists(self, trashcan_id: int, db: SessionDep) -> bool:
        stmt = (
            select(Trashcan.trashcan_id)
            .where(Trashcan.trashcan_id == trashcan_id)
            .where(Trashcan.is_deleted == False)
        )
        return (await db.execute(stmt)).first() is not None

    async def get_total_detection(self, db: SessionDep):
        total_objects_stmt = select(func.count(DetectionDetail.detail_id))
        total_objects = (await db.execute(total_objects_stmt)).scalar() or 0

        total_events_stmt = select(func.count(Detection.detection_id))
        total_events = (await db.execute(total_events_stmt)).scalar() or 0

        type_stmt = (
            select(
                WasteType.type_name,
                func.count(DetectionDetail.detail_id).label("type_count"),
            )
            .join(DetectionDetail, DetectionDetail.waste_type_id == WasteType.waste_type_id)
            .group_by(WasteType.type_name)
            .order_by(WasteType.type_name.asc())
        )
        type_rows = (await db.execute(type_stmt)).all()

        items_by_type = {
            "MetalCan": 0,
            "PetBottle": 0,
            "Plastic": 0,
            "Styrofoam": 0,
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
            func.coalesce(Trashcan.current_volume, 0)
            / func.nullif(Trashcan.trashcan_capacity, 0)
        )
        fill_status = case(
            (fill_rate >= 0.9, "포화"),
            (fill_rate >= 0.5, "보통"),
            else_="여유",
        ).label("fill_status")
        status_order = case(
            (fill_rate >= 0.9, 1),
            (fill_rate >= 0.5, 2),
            else_=3,
        ).label("status_order")

        stmt = (
            select(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                fill_status,
            )
            .where(Trashcan.is_deleted == False)
            .order_by(status_order.asc(), fill_rate.desc(), Trashcan.trashcan_id.asc())
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "trashcan_name": row.trashcan_name,
                "fill_status": row.fill_status,
            }
            for row in rows
        ]

    async def get_stats_charts(self, db: SessionDep, period: str):
        today = date.today()
        if period == "month":
            start_date = date(today.year, today.month, 1)
        elif period == "year":
            start_date = date(today.year, 1, 1)
        else:
            start_date = today - timedelta(days=today.weekday())

        total_stmt = (
            select(func.coalesce(func.sum(DailyStats.detection_count), 0))
            .where(DailyStats.stats_date >= start_date)
            .where(DailyStats.stats_date <= today)
        )
        total_count = (await db.execute(total_stmt)).scalar() or 0

        type_stmt = (
            select(
                WasteType.type_name,
                func.coalesce(func.sum(DailyStats.detection_count), 0).label("type_count"),
            )
            .join(WasteType, WasteType.waste_type_id == DailyStats.waste_type_id)
            .where(DailyStats.stats_date >= start_date)
            .where(DailyStats.stats_date <= today)
            .group_by(WasteType.type_name)
            .order_by(WasteType.type_name.asc())
        )
        type_rows = (await db.execute(type_stmt)).all()

        items_by_type = {
            "MetalCan": 0,
            "PetBottle": 0,
            "Plastic": 0,
            "Styrofoam": 0,
        }
        for row in type_rows:
            if row.type_name in items_by_type:
                items_by_type[row.type_name] += int(row.type_count or 0)

        city_stmt = (
            select(
                DailyStats.trashcan_city,
                func.coalesce(func.sum(DailyStats.detection_count), 0).label("city_count"),
            )
            .where(DailyStats.stats_date >= start_date)
            .where(DailyStats.stats_date <= today)
            .group_by(DailyStats.trashcan_city)
            .order_by(DailyStats.trashcan_city.asc())
        )
        city_rows = (await db.execute(city_stmt)).all()
        items_by_city = {}
        for row in city_rows:
            key = row.trashcan_city or "unknown"
            items_by_city[key] = int(row.city_count or 0)

        return {
            "period": period,
            "start_date": start_date,
            "end_date": today,
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

    async def save_trashcan_error_log(
        self,
        trashcan_id: int | None,
        camera_id: int | None,
        status_code: int,
        message: str | None,
        occurred_at: str | None,
        db: SessionDep,
    ) -> None:
        if trashcan_id is not None:
            if not await self._ensure_trashcan_exists(trashcan_id, db):
                return
        occurred_value = None
        if occurred_at:
            try:
                normalized = occurred_at.replace("Z", "+00:00")
                occurred_value = datetime.fromisoformat(normalized)
            except ValueError:
                occurred_value = None
        effective_time = occurred_value or datetime.now()
        if effective_time.tzinfo is not None:
            effective_time = effective_time.astimezone(tz=None).replace(tzinfo=None)
        base_stmt = (
            select(TrashcanErrorLog)
            .where(TrashcanErrorLog.status_code == status_code)
            .where(TrashcanErrorLog.message == message)
        )
        if trashcan_id is not None:
            base_stmt = base_stmt.where(TrashcanErrorLog.trashcan_id == trashcan_id)
        else:
            base_stmt = base_stmt.where(TrashcanErrorLog.trashcan_id.is_(None))
            base_stmt = base_stmt.where(TrashcanErrorLog.camera_id == camera_id)
        last_log = (
            await db.execute(
                base_stmt.order_by(
                    desc(TrashcanErrorLog.created_at),
                    desc(TrashcanErrorLog.id),
                ).limit(1)
            )
        ).scalar_one_or_none()
        if last_log:
            last_time = last_log.last_occurred_at or last_log.created_at
            if last_time and last_time.tzinfo is not None:
                last_time = last_time.astimezone(tz=None).replace(tzinfo=None)
            if last_time and effective_time - last_time <= timedelta(minutes=1):
                last_log.repeat_count = (last_log.repeat_count or 1) + 1
                last_log.last_occurred_at = effective_time
                await db.commit()
                return
        log = TrashcanErrorLog(
            trashcan_id=trashcan_id,
            camera_id=camera_id,
            status_code=status_code,
            message=message,
            occurred_at=occurred_value,
            last_occurred_at=effective_time,
            repeat_count=1,
        )
        db.add(log)
        await db.commit()
        return

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
