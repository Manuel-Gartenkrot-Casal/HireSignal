from typing import Optional

from .base import _coerce_fecha, _get_json

from ..models import Job

MELI_API = "https://careers-meli.mercadolibre.com/api/positions"
MELI_BASE = "https://careers-meli.mercadolibre.com"

# Filtros: solo roles remotos/híbridos relevantes no-imposible; el board
# publica mucho warehouse/logística onsite. Se trae todo y se filtra después.
MELI_COUNTRIES = ["Argentina", "Brazil", "Mexico", "Uruguay", "Chile", "Colombia", "Peru"]


class MeliSpider:
    name = "meli"

    def run(self, companies: list[dict], limit: Optional[int] = None) -> list[Job]:
        jobs = []
        for company in companies:
            if company.get("ats") != "meli":
                continue
            company_name = company["name"]
            offset = 0
            while True:
                if limit and len(jobs) >= limit:
                    break
                try:
                    data = _get_json(
                        MELI_API + "?" + "&".join(
                            [
                                "start=" + str(offset),
                                "country=" + (company.get("country") or "Argentina"),
                            ]
                        )
                    )
                except Exception:
                    break
                if not data or not isinstance(data, dict) or not data.get("positions"):
                    break
                for item in data["positions"]:
                    if limit and len(jobs) >= limit:
                        break
                    if not item.get("name"):
                        continue
                    job = Job(
                        company=company_name,
                        title=item["name"],
                        url=MELI_BASE + (item.get("positionUrl") or f"/careers/job/{item['id']}"),
                        source="meli",
                        ats="meli",
                        location=", ".join(item.get("locations") or []) or "",
                        posted_date=_coerce_fecha(item.get("postedTs")),
                        description="",
                        raw=item,
                    )
                    jobs.append(job)
                if not data.get("hasMore"):
                    break
                offset += len(data["positions"])
        return jobs