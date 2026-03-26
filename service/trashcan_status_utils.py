from datetime import datetime, timedelta

from sqlmodel import update

from db.db import SessionDep
from db.entity import Trashcan


async def mark_offline_if_stale(db: SessionDep, minutes: int = 5) -> None:
    cutoff = datetime.now() - timedelta(minutes=minutes)
    stmt = (
        update(Trashcan)
        .where(Trashcan.is_online == True)
        .where(Trashcan.last_connected_at != None)
        .where(Trashcan.last_connected_at < cutoff)
        .values(is_online=False)
    )
    await db.execute(stmt)
    await db.commit()
