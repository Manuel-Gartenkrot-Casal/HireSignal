import datetime
from typing import Optional

from .base import HEADERS, TIMEOUT

from ..models import Job

GETONBRD_SEARCH = (
    "https://www.getonbrd.com/api/v0/search/jobs?query={query}"
    "&company_ids={company_ids}&page={page}"
)


class GetonbrdSpider:
    name = "getonbrd"

    def __init__(self):
        self._company_cache: dict[int, str] = {}

    def run(self, companies: list[dict], limit: Optional[int] = None) -> list[Job]:
        import requests

        jobs = []
        company_ids = [c.get("getonbrd_id") for c in companies if c.get("getonbrd_id")]
        cids = ",".join(str(i) for i in company_ids) if company_ids else ""

        for query in _QUERIES:
            page = 1
            while True:
                url = GETONBRD_SEARCH.format(query=query.replace(" ", "+"), company_ids=cids, page=page)
                data = self._fetch_json(url)
                if not data or not data.get("data"):
                    break
                for item in data["data"]:
                    if limit and len(jobs) >= limit:
                        return jobs
                    attrs = item.get("attributes", {})
                    title = attrs.get("title") or ""
                    if not title:
                        continue
                    cid = (attrs.get("company") or {}).get("data", {}).get("id")
                    mid = (attrs.get("modality") or {}).get("data", {}).get("id")
                    sid = (attrs.get("seniority") or {}).get("data", {}).get("id")
                    job = Job(
                        company=self._company_name(cid),
                        title=title,
                        url=f"https://www.getonbrd.com/empleos/{item.get('id', '')}",
                        source="getonbrd",
                        ats="getonbrd",
                        location=_MODALIDADES.get(mid, f"modality-{mid}"),
                        seniority=_SENIORITIES.get(sid, ""),
                        posted_date=_epoch_fecha(attrs.get("published_at")),
                        raw=item,
                    )
                    jobs.append(job)
                page += 1
                if page > 10:
                    break
        return jobs

    def _company_name(self, cid) -> str:
        if not cid:
            return ""
        if cid in self._company_cache:
            return self._company_cache[cid]
        try:
            import requests

            r = requests.get(f"https://www.getonbrd.com/api/v0/companies/{cid}", timeout=TIMEOUT, headers=HEADERS)
            r.raise_for_status()
            name = r.json().get("data", {}).get("attributes", {}).get("name", "")
        except Exception:
            name = ""
        self._company_cache[cid] = name
        return name

    def _fetch_json(self, url: str) -> Optional[dict]:
        import requests

        try:
            r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
            r.raise_for_status()
            return r.json()
        except Exception:
            return self._fetch_json_browser(url)

    def _fetch_json_browser(self, url: str) -> Optional[dict]:
        try:
            from scrapling.fetchers import StealthyFetcher

            pag = StealthyFetcher.fetch(
                url,
                headless=True,
                disable_resources=True,
                timeout=10000,
                extra_flags=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            if hasattr(pag, "body") and pag.body:
                import json

                raw = pag.body.decode("utf-8", errors="replace") if isinstance(pag.body, bytes) else str(pag.body)
                return json.loads(raw)
        except Exception:
            return None
        return None


_QUERIES = ["", "desarrollador", "backend", "frontend", "data", "devops", "qa"]

# Getonbrd devuelve modality y seniority como IDs; mapeo conservador basado
# en el orden del sitio. Si el ID no está, se deja vacío.
_MODALIDADES = {
    1: "Remoto",
    2: "Híbrido",
    3: "Presencial",
    4: "Remoto (LatAm)",
}

_SENIORITIES = {
    1: "Trainee",
    2: "Junior",
    3: "Semi Senior",
    4: "Senior",
    5: "Lead",
    6: "Staff",
}


def _epoch_fecha(ts) -> Optional[datetime.datetime]:
    if not ts:
        return None
    try:
        return datetime.datetime.fromtimestamp(int(ts), tz=datetime.UTC)
    except Exception:
        return None