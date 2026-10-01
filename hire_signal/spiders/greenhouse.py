from typing import Optional

from .base import _coerce_fecha, _get_json, _texto

from ..models import Job

GREENHOUSE_BASE = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


class GreenhouseSpider:
    name = "greenhouse"

    def run(self, companies: list[dict], limit: Optional[int] = None) -> list[Job]:
        jobs = []
        for company in companies:
            if company.get("ats") != "greenhouse":
                continue
            slug = company["slug"]
            try:
                data = _get_json(GREENHOUSE_BASE.format(slug=slug))
            except Exception:
                continue
            if not data or "jobs" not in data:
                continue

            for item in data["jobs"]:
                if limit and len(jobs) >= limit:
                    break
                if not item.get("title"):
                    continue
                url = f"https://boards.greenhouse.io/{slug}/jobs/{item.get('id')}"
                job = Job(
                    company=company["name"],
                    title=item["title"],
                    url=url,
                    source="greenhouse",
                    ats="greenhouse",
                    location=item.get("location", {}).get("name", "") if isinstance(item.get("location"), dict) else item.get("location", ""),
                    posted_date=_coerce_fecha(item.get("updated_at") or item.get("first_published_at")),
                    description=_texto(item.get("content")),
                    raw=item,
                )
                jobs.append(job)
        return jobs