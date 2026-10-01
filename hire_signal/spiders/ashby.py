from typing import Optional

from .base import _coerce_fecha, _get_json, _texto

from ..models import Job

ASHBY_API = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


class AshbySpider:
    name = "ashby"

    def run(self, companies: list[dict], limit: Optional[int] = None) -> list[Job]:
        jobs = []
        for company in companies:
            if company.get("ats") != "ashby":
                continue
            slug = company["slug"]
            try:
                data = _get_json(ASHBY_API.format(slug=slug))
            except Exception:
                continue
            if not data or not isinstance(data, dict) or not data.get("jobs"):
                continue

            for item in data["jobs"]:
                if limit and len(jobs) >= limit:
                    break
                if not item.get("title"):
                    continue
                url = item.get("jobUrl") or (item.get("jobUrl") or "")
                job = Job(
                    company=company["name"],
                    title=item["title"],
                    url=url,
                    source="ashby",
                    ats="ashby",
                    location=item.get("location", ""),
                    posted_date=_coerce_fecha(item.get("publishedAt")),
                    description=_texto(item.get("descriptionHtml")),
                    raw=item,
                )
                jobs.append(job)
        return jobs