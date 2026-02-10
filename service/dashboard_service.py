import json
import os
from datetime import date, timedelta

from sqlmodel import select
from sqlalchemy import case, func
from db.entity import DetectionDetail, WasteType, Trashcan, DailyStats
from db.db import SessionDep

class DashboardService:
    def __init__(self):
        self._log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        os.makedirs(self._log_dir, exist_ok=True)

    async def _ensure_trashcan_exists(self, trashcan_id: int, db: SessionDep) -> bool:
        stmt = (
            select(Trashcan.trashcan_id)
            .where(Trashcan.trashcan_id == trashcan_id)
            .where(Trashcan.is_deleted == False)
        )
        return (await db.execute(stmt)).first() is not None

    async def get_total_detection(self, db: SessionDep):
        total_stmt = select(func.count(DetectionDetail.detail_id))
        total_objects = (await db.execute(total_stmt)).scalar() or 0

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
        stmt = (
            select(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                Trashcan.last_connected_at,
            )
            .where(Trashcan.is_deleted == False)
            .where(Trashcan.is_online == False)
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

    async def save_unconnected_trashcan_log(
        self,
        trashcan_id: int,
        status_code: int,
        message: str | None,
        occurred_at: str | None,
        db: SessionDep,
    ):
        if not await self._ensure_trashcan_exists(trashcan_id, db):
            return None

        log_path = os.path.join(self._log_dir, f"trashcan_{trashcan_id}.jsonl")
        payload = {
            "trashcan_id": trashcan_id,
            "status_code": status_code,
            "message": message,
            "occurred_at": occurred_at,
        }
        with open(log_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return {"saved": True}

    async def get_unconnected_trashcan_log(
        self, trashcan_id: int, limit: int, db: SessionDep
    ):
        if not await self._ensure_trashcan_exists(trashcan_id, db):
            return None

        log_path = os.path.join(self._log_dir, f"trashcan_{trashcan_id}.jsonl")
        if not os.path.exists(log_path):
            return {"trashcan_id": trashcan_id, "logs": []}

        logs: list[dict] = []
        with open(log_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        if limit > 0:
            logs = logs[-limit:]

        return {"trashcan_id": trashcan_id, "logs": logs}