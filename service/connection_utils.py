import urllib.error
import urllib.request


def ping_server(url: str, timeout: int = 3) -> tuple[int | None, str | None, bool, str | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            status = resp.getcode()
            body = resp.read()
            text = body.decode("utf-8", errors="replace") if body else None
            return status, text, True, None
    except urllib.error.HTTPError as exc:
        body = exc.read()
        text = body.decode("utf-8", errors="replace") if body else None
        return exc.code, text, False, str(exc)
    except Exception as exc:
        return None, None, False, str(exc)
