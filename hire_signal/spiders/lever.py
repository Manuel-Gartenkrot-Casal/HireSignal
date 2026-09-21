from typing import Optional

from .base import _coerce_fecha, _get_json

from ..models import Job

LEVER_BASE = "https://api.lever.co/v0/postings/{slug}?mode=json"


class LeverSpider:
    name = "lever"

    def run(self, companies: list[dict], limit: Optional[int] = None) -> list[Job]:
        jobs = []
        for company in companies:
            if company.get("ats") != "lever":
                continue
            slug = company["slug"]
            try:
                data = _get_json(LEVER_BASE.format(slug=slug))
            except Exception:
                continue
            if not data or not isinstance(data, list):
                continue

            for item in data:
                if limit and len(jobs) >= limit:
                    break
                if not item.get("text"):
                    continue
                url = item.get("hostedUrl") or f"https://jobs.lever.co/{slug}/{item.get('id')}"
                job = Job(
                    company=company["name"],
                    title=item["text"],
                    url=url,
                    source="lever",
                    ats="lever",
                    location=item.get("categories", {}).get("location", "") or item.get("workplaceType", ""),
                    posted_date=_coerce_fecha(item.get("createdAt")),
                    description=item.get("descriptionPlain", ""),
                    raw=item,
                )
                jobs.append(job)
        return jobs