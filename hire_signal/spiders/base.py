import datetime
import html
import re
import time
from typing import Optional

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}

TIMEOUT = 15


def _coerce_fecha(val) -> Optional[datetime.datetime]:
    """Acepta ISO string o epoch ms/s y devuelve datetime UTC."""
    if not val:
        return None
    if isinstance(val, (int, float)):
        ms = val if val > 1e12 else val * 1000
        return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC)
    if isinstance(val, str):
        try:
            return datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _texto(raw: str) -> str:
    """HTML (posiblemente escapado) -> texto plano, para que los regex de filters funcionen."""
    return re.sub(r"<[^>]+>", " ", html.unescape(html.unescape(raw or "")))


def _get_json(url: str) -> Optional[object]:
    """GET con 3 intentos ante errores de red / 5xx / 429. 4xx (slug inválido) no reintenta."""
    for intento in range(3):
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
            if r.status_code < 500 and r.status_code != 429:
                r.raise_for_status()
                return r.json()
        except requests.HTTPError:
            return None
        except Exception:
            pass
        if intento < 2:
            time.sleep(2**intento)
    return None
