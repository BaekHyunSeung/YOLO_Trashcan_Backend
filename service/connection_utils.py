import asyncio
from datetime import datetime
import platform
import subprocess
from urllib.parse import urlparse

from sqlmodel import select

from db.db import SessionDep
from db.entity import Trashcan


def _normalize_host(raw: str) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    if not value:
        return None
    if "://" not in value:
        parsed = urlparse(f"http://{value}")
    else:
        parsed = urlparse(value)
    return parsed.hostname or value


def ping_server(url: str, timeout: int = 3) -> bool:
    host = _normalize_host(url)
    if not host:
        return False
    system = platform.system().lower()
    if system.startswith("win"):
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout), host]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


async def check_trashcan_connection(trashcan_id: int, db: SessionDep) -> dict:
    stmt = select(Trashcan).where(Trashcan.trashcan_id == trashcan_id)
    trashcan = (await db.execute(stmt)).scalar_one_or_none()
    if not trashcan or not trashcan.server_url:
        return {
            "trashcan_id": trashcan_id,
            "status": "error",
            "message": "Server URL not found",
        }

    reachable = await asyncio.to_thread(ping_server, trashcan.server_url)
    if reachable:
        trashcan.is_online = True
        trashcan.last_connected_at = datetime.now()
        await db.commit()
        return {"trashcan_id": trashcan_id, "status": "ok", "message": "Server is healthy"}

    trashcan.is_online = False
    await db.commit()
    return {
        "trashcan_id": trashcan_id,
        "status": "error",
        "message": "Failed to connect to server",
    }
