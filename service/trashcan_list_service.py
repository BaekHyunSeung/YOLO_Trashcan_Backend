from sqlmodel import select
from sqlalchemy import func
from db.entity import Trashcan, Detection
from db.db import SessionDep
from service.trashcan_status_utils import mark_offline_if_stale

class TrashcanList:
    def __init__(self):
        pass

    async def get_trashcans_list(self, db: SessionDep, offset: int, limit: int):
        await mark_offline_if_stale(db, minutes=5)
        total_stmt = select(func.count(Trashcan.trashcan_id)).where(
            Trashcan.is_deleted == False
        )
        total = (await db.execute(total_stmt)).scalar() or 0
        fill_rate = (
            (func.coalesce(Trashcan.current_volume, 0) * 100.0)
            / func.nullif(Trashcan.trashcan_capacity, 0)
        ).label("fill_rate")
        stmt = (
            select(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                Trashcan.is_online,
                fill_rate,
                func.coalesce(func.sum(Detection.object_count), 0).label("total_collected"),
            )
            .join(Detection, Detection.trashcan_id == Trashcan.trashcan_id, isouter=True)
            .where(Trashcan.is_deleted == False)
            .group_by(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                Trashcan.is_online,
                Trashcan.trashcan_capacity,
                Trashcan.current_volume,
            )
            .offset(offset)
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        items = [
            {
                "trashcan_id": row.trashcan_id,
                "trashcan_name": row.trashcan_name,
                "address_detail": row.address_detail,
                "is_online": row.is_online,
                "fill_rate": round(float(row.fill_rate or 0), 2),
                "total_collected": int(row.total_collected or 0),
            }
            for row in rows
        ]
        return {"total": int(total), "items": items}
    
    async def sort_trashcans_list(
        self,
        db: SessionDep,
        sort_by: str,
        order: str,
        city: str | None,
        name: str | None,
        offset: int,
        limit: int,
    ):
        await mark_offline_if_stale(db, minutes=5)
        total_collected = func.coalesce(func.sum(Detection.object_count), 0).label(
            "total_collected"
        )
        free_capacity = (
            func.coalesce(Trashcan.trashcan_capacity, 0)
            - func.coalesce(Trashcan.current_volume, 0)
        ).label("free_capacity")
        fill_rate = (
            (func.coalesce(Trashcan.current_volume, 0) * 100.0)
            / func.nullif(Trashcan.trashcan_capacity, 0)
        ).label("fill_rate")
        sort_map = {
            "collected": total_collected,
            "free_capacity": free_capacity,
            "is_online": Trashcan.is_online,
        }
        sort_expr = sort_map.get(sort_by, total_collected)
        sort_expr = sort_expr.desc() if order == "desc" else sort_expr.asc()

        stmt = (
            select(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                Trashcan.is_online,
                total_collected,
                free_capacity,
                fill_rate,
            )
            .join(Detection, Detection.trashcan_id == Trashcan.trashcan_id, isouter=True)
            .where(Trashcan.is_deleted == False)
        )
        if city:
            stmt = stmt.where(Trashcan.trashcan_city.ilike(f"%{city}%"))
        if name:
            stmt = stmt.where(Trashcan.trashcan_name.ilike(f"%{name}%"))

        total_stmt = select(func.count(Trashcan.trashcan_id)).where(
            Trashcan.is_deleted == False
        )
        if city:
            total_stmt = total_stmt.where(Trashcan.trashcan_city.ilike(f"%{city}%"))
        if name:
            total_stmt = total_stmt.where(Trashcan.trashcan_name.ilike(f"%{name}%"))
        total = (await db.execute(total_stmt)).scalar() or 0

        stmt = (
            stmt.group_by(
                Trashcan.trashcan_id,
                Trashcan.trashcan_name,
                Trashcan.address_detail,
                Trashcan.is_online,
                Trashcan.trashcan_capacity,
                Trashcan.current_volume,
            )
            .order_by(sort_expr, Trashcan.trashcan_id.asc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        items = [
            {
                "trashcan_id": row.trashcan_id,
                "trashcan_name": row.trashcan_name,
                "address_detail": row.address_detail,
                "is_online": row.is_online,
                "total_collected": int(row.total_collected or 0),
                "free_capacity": int(row.free_capacity or 0),
                "fill_rate": round(float(row.fill_rate or 0), 2),
            }
            for row in rows
        ]
        return {"total": int(total), "items": items}
        

