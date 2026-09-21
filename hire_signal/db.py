import datetime
import os

from dotenv import load_dotenv
from pymongo import MongoClient

from .models import Job

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/hiresignal")
DB_NAME = os.getenv("MONGO_DB", "hiresignal")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=15000, connectTimeoutMS=15000)
db = client[DB_NAME]
col_jobs = db["jobs"]


def crear_indices():
    col_jobs.create_index("dedup_key", unique=True, name="uq_dedup")
    col_jobs.create_index("company", name="idx_company")
    col_jobs.create_index("source", name="idx_source")
    col_jobs.create_index("sources", name="idx_sources")
    col_jobs.create_index("seniority", name="idx_seniority")
    col_jobs.create_index("role_category", name="idx_role")
    col_jobs.create_index("posted_date", name="idx_posted")
    col_jobs.create_index("first_seen", name="idx_first_seen")
    col_jobs.create_index("active", name="idx_active")


def _doc(job: Job) -> dict:
    ahora = datetime.datetime.now(datetime.UTC)
    return {
        "dedup_key": job.dedup_key,
        "company": job.company,
        "title": job.title,
        "url": job.url,
        "source": job.source,
        "ats": job.ats,
        "location": job.location,
        "seniority": job.seniority,
        "role_category": job.role_category,
        "tech": job.tech,
        "posted_date": job.posted_date.isoformat() if job.posted_date else None,
        "last_seen": ahora.isoformat(),
    }


def guardar_jobs(jobs: list[Job]) -> dict:
    """Upsert por dedup_key. Si el puesto ya existe, acumula la fuente nueva
    en `sources` y refresca last_seen sin pisar first_seen."""
    if not jobs:
        return {"insertados": 0, "actualizados": 0}

    insertados = 0
    actualizados = 0
    for job in jobs:
        key = job.dedup_key
        result = col_jobs.update_one(
            {"dedup_key": key},
            {
                "$set": _doc(job),
                "$setOnInsert": {
                    "first_seen": datetime.datetime.now(datetime.UTC).isoformat(),
                    "active": True,
                },
                "$addToSet": {"sources": job.source},
            },
            upsert=True,
        )
        if result.upserted_id is not None:
            insertados += 1
        elif result.modified_count > 0:
            actualizados += 1
    return {"insertados": insertados, "actualizados": actualizados}


def marcar_inactivos(activos_por_fuente: dict[str, set[str]] | set[str]):
    """Marca como inactivos los jobs de cada fuente que ya no aparecen.

    En vez de comparar contra el set global (que desactivaría TODOS los jobs
    de un spider que falló u omisión), compara fuente por fuente: cada spider
    es dueño de su propia información de vigencia.

    Acepta dict {fuente: set(dedup_keys)} o un simple set (caso legacy: se
    asume una sola fuente "source").
    """
    if isinstance(activos_por_fuente, set):
        activos_por_fuente = {"source": activos_por_fuente}

    contados = 0
    for fuente, keys in activos_por_fuente.items():
        resultado = col_jobs.update_many(
            {"source": fuente, "dedup_key": {"$nin": list(keys)}, "active": True},
            {"$set": {"active": False, "last_seen": datetime.datetime.now(datetime.UTC).isoformat()}},
        )
        contados += resultado.modified_count
    return contados


def activos() -> list[dict]:
    return list(col_jobs.find({"active": True}).sort("posted_date", -1))


def resumen() -> dict:
    return {
        "total": col_jobs.count_documents({}),
        "activos": col_jobs.count_documents({"active": True}),
        "por_fuente": col_jobs.aggregate([{"$group": {"_id": "$source", "n": {"$sum": 1}}}]),
    }