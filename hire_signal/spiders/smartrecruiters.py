from typing import Optional

from .base import _coerce_fecha, _get_json

from ..models import Job

SR_API = "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100"
SR_JOB = "https://jobs.smartrecruiters.com/{slug}/{id}"


class SmartRecruitersSpider:
    name = "smartrecruiters"

    def run(self, companies: list[dict], limit: Optional[int] = None) -> list[Job]:
        jobs = []
        for company in companies:
            if company.get("ats") != "smartrecruiters":
                continue
            slug = company["slug"]
            try:
                data = _get_json(SR_API.format(slug=slug))
            except Exception:
                continue
            if not data or not isinstance(data, dict):
                continue

            for item in data.get("content", []):
                if limit and len(jobs) >= limit:
                    break
                if not item.get("name"):
                    continue
                job = Job(
                    company=company["name"],
                    title=item["name"],
                    url=item.get("ref") or SR_JOB.format(slug=slug, id=item.get("id", "")),
                    source="smartrecruiters",
                    ats="smartrecruiters",
                    location=item.get("location", "") if isinstance(item.get("location"), str) else (
                        ", ".join(filter(None, item.get("location", {}).get("city", []) or [])) or ""
                    ),
                    posted_date=_coerce_fecha(item.get("releasedDate")),
                    description=item.get("jobDescription", ""),
                    raw=item,
                )
                jobs.append(job)
        return jobs