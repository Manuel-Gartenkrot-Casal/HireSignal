import json
from pathlib import Path
from typing import Optional

from .filters import aplicar_a_job
from .models import Job
from .spiders import ALL_SPIDERS


COMPANIES_PATH = "hire_signal/config/companies.json"


def _cargar_companies(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("companies", [])


def _dedupe(jobs: list[Job], max_ubicaciones: int = 5) -> list[Job]:
    """Un solo Job por (empresa, título); el mismo puesto publicado en varias
    ciudades conserva todas las ubicaciones en vez de perderlas."""
    unicos: dict[str, Job] = {}
    ubicaciones: dict[str, list[str]] = {}
    for job in jobs:
        k = job.dedup_key
        unicos.setdefault(k, job)
        lista = ubicaciones.setdefault(k, [])
        if job.location and job.location not in lista:
            lista.append(job.location)
    for k, job in unicos.items():
        lista = ubicaciones[k]
        extra = f" (+{len(lista) - max_ubicaciones})" if len(lista) > max_ubicaciones else ""
        job.location = "; ".join(lista[:max_ubicaciones]) + extra
    return list(unicos.values())


def run(
    companies_path: str | Path = COMPANIES_PATH,
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

    return _dedupe(jobs)


__all__ = ["run"]