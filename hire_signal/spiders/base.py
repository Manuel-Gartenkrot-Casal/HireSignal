import datetime
import json
import os
import sys
from typing import Optional, Protocol

import requests

from ..models import Job

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


def _get_json(url: str) -> Optional[object]:
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _url_is_ats(json_url: str) -> bool:
    return any(
        d in json_url
        for d in ["boards-api.greenhouse.io", "lever.co", "ashbyhq.com", "api.smartrecruiters.com"]
    )


class BaseSpider(Protocol):
    name: str

    def run(self, companies: list[dict], limit: Optional[int] = None) -> list[Job]:
        ...


def to_dict(job: Job) -> dict:
    return dataclasses_as_dict(job)


def dataclasses_as_dict(job: Job) -> dict:
    return {
        "company": job.company,
        "title": job.title,
        "url": job.url,
        "source": job.source,
        "ats": job.ats,
        "role_category": job.role_category,
        "seniority": job.seniority,
        "tech": job.tech,
        "location": job.location,
        "posted_date": job.posted_date.isoformat() if job.posted_date else None,
        "first_seen": job.first_seen.isoformat(),
        "dedup_key": job.dedup_key,
    }