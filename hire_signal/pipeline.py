import json
import os
from pathlib import Path
from typing import Optional

from .filters import aplicar_a_job
from .models import Job
from .spiders import ALL_SPIDERS


def _cargar_companies(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("companies", [])


def _coerce_job(job: Job) -> Job:
    if isinstance(job, Job):
        return job
    return Job(**job)


def run(
    companies_path: str | Path = "hire_signal/config/companies.json",
    sources: Optional[list[str]] = None,
    limit: Optional[int] = None,
) -> list[Job]:
    companies = _cargar_companies(companies_path)
    if not companies:
        print("[pipeline] companies.json vacío o no encontrado")
        return []

    spiders = [s for s in ALL_SPIDERS if not sources or s.name in sources]
    jobs: list[Job] = []

    for spider_cls in spiders:
        spider = spider_cls()
        try:
            encontrados = spider.run(companies, limit=limit)
        except Exception as e:
            print(f"[pipeline] {spider.name} falló: {e}")
            continue
        for job in encontrados:
            aplicar_a_job(job)
            jobs.append(job)
        print(f"[pipeline] {spider.name}: {len(encontrados)} jobs")

    # Dedupe intra-ejecución (misma fuente + mismo título)
    unicos: dict[str, Job] = {}
    for job in jobs:
        unicos[job.dedup_key] = job
    return list(unicos.values())


__all__ = ["run"]