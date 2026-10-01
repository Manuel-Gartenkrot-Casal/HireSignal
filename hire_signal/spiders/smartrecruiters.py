from typing import Optional

from ..models import Job
from .base import _coerce_fecha, _get_json

SR_API = "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset={offset}"
SR_JOB = "https://jobs.smartrecruiters.com/{company}/{id}"

# Solo los niveles inequívocos; "mid_senior_level" no distingue mid de senior,
# ahí manda el clasificador por título.
EXPERIENCE_TO_SENIORITY = {
    "internship": "junior",
    "entry_level": "junior",
    "director": "lead",
    "executive": "lead",
}


def _ubicacion(loc) -> str:
    if isinstance(loc, str):
        return loc
    if not isinstance(loc, dict):
        return ""
    return ", ".join(p for p in (loc.get("city"), (loc.get("country") or "").upper()) if p)


class SmartRecruitersSpider:
    name = "smartrecruiters"

    def run(self, companies: list[dict], limit: Optional[int] = None) -> list[Job]:
        jobs = []
        for company in companies:
            if company.get("ats") != "smartrecruiters":
                continue
            slug = company["slug"]
            offset = 0
            while not (limit and len(jobs) >= limit):
                data = _get_json(SR_API.format(slug=slug, offset=offset))
                if not isinstance(data, dict) or not data.get("content"):
                    break
                for item in data["content"]:
                    if not item.get("name"):
                        continue
                    ident = (item.get("company") or {}).get("identifier") or slug
                    nivel = (item.get("experienceLevel") or {}).get("id")
                    jobs.append(
                        Job(
                            company=company["name"],
                            title=item["name"],
                            url=SR_JOB.format(company=ident, id=item.get("id", "")),
                            source="smartrecruiters",
                            ats="smartrecruiters",
                            seniority=EXPERIENCE_TO_SENIORITY.get(nivel, ""),
                            location=_ubicacion(item.get("location")),
                            posted_date=_coerce_fecha(item.get("releasedDate")),
                            raw=item,
                        )
                    )
                offset += len(data["content"])
                if offset >= data.get("totalFound", 0):
                    break
        return jobs
