import platform
import subprocess
from urllib.parse import urlparse


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
