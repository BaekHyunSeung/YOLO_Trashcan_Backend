import asyncio
from datetime import datetime
import platform
import subprocess
from urllib.parse import urlparse

from sqlmodel import select

from db.db import SessionDep
from db.entity import Trashcan

#URL 정규화
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

#서버 연결 테스트
def ping_server(url: str, timeout: int = 3) -> bool:
    host = _normalize_host(url)
    if not host:
        return False
    system = platform.system().lower()
    if system.startswith("win"):
        #Windows 환경
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
    else:
        #Linux 환경
        cmd = ["ping", "-c", "1", "-W", str(timeout), host]
    try:
        #서버 연결 테스트
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0 #연결 성공 여부
    except Exception:
        return False


#쓰레기통 연결 테스트
async def check_trashcan_connection(trashcan_id: int, db: SessionDep) -> dict:
    #쓰레기통 정보 조회
    stmt = select(Trashcan).where(Trashcan.trashcan_id == trashcan_id)
    trashcan = (await db.execute(stmt)).scalar_one_or_none()
    if not trashcan or not trashcan.server_url:
        #쓰레기통 정보 없음
        return {
            "trashcan_id": trashcan_id,
            "status": "error",
            "message": "Server URL not found",
        }

    #서버 연결 테스트
    reachable = await asyncio.to_thread(ping_server, trashcan.server_url)
    #연결 성공 시
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
