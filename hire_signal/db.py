import datetime
import os

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.errors import OperationFailure

from .models import Job

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/hiresignal")
DB_NAME = os.getenv("MONGO_DB", "hiresignal")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=15000, connectTimeoutMS=15000)
db = client[DB_NAME]
col_jobs = db["jobs"]


def crear_indices():
    col_jobs.create_index("dedup_key", unique=True, name="uq_dedup")
    for campo in ("source", "sources", "seniority", "role_category", "posted_date", "active"):
        try:
            col_jobs.create_index(campo, name=f"idx_{campo}")
        except OperationFailure as e:
            # 85 = ya existe el mismo índice con otro nombre (bases creadas
            # antes del renombre idx_role -> idx_role_category). Sirve igual.
            if e.code != 85:
                raise


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
        "active": True,  # reaparece en la fuente => se reactiva
    }


def guardar_jobs(jobs: list[Job]) -> dict:
    """Upsert por dedup_key. Si el puesto ya existe, acumula la fuente nueva
    en `sources` y refresca last_seen sin pisar first_seen."""
    if not jobs:
        return {"insertados": 0, "actualizados": 0}
    ahora = datetime.datetime.now(datetime.UTC).isoformat()
    ops = [
        UpdateOne(
            {"dedup_key": j.dedup_key},
            {
                "$set": _doc(j),
                "$setOnInsert": {"first_seen": ahora},
                "$addToSet": {"sources": j.source},
            },
            upsert=True,
        )
        for j in jobs
    ]
    res = col_jobs.bulk_write(ops, ordered=False)
    return {"insertados": res.upserted_count, "actualizados": res.modified_count}


MAX_CIERRE = 0.5


def _debe_cerrar(previos: int, a_cerrar: int) -> bool:
    """False si cerraría más de la mitad de lo activo: casi seguro es una
    fuente que respondió incompleta, no que cerró la mitad de sus puestos."""
    return not previos or a_cerrar / previos <= MAX_CIERRE


def marcar_inactivos(jobs: list[Job]) -> int:
    """Inactiva los puestos que ya no aparecen, solo para (fuente, empresa)
    que SÍ devolvieron algo en esta corrida: una empresa cuyo board falló no
    se toca. # ponytail: una empresa que cierra TODOS sus puestos queda activa
    hasta que publique uno nuevo; agregar un registro de empresas leídas OK
    por spider si importa."""
    vistos: dict[str, tuple[set[str], set[str]]] = {}
    for j in jobs:
        empresas, keys = vistos.setdefault(j.source, (set(), set()))
        empresas.add(j.company)
        keys.add(j.dedup_key)

    for fuente, (empresas, keys) in vistos.items():
        base = {"sources": fuente, "company": {"$in": list(empresas)}, "active": True}
        filtro = {**base, "dedup_key": {"$nin": list(keys)}}
        if not _debe_cerrar(col_jobs.count_documents(base), col_jobs.count_documents(filtro)):
            print(f"[db] {fuente}: cerraría >{MAX_CIERRE:.0%} de sus puestos activos, se omite (¿respuesta incompleta?)", flush=True)
            continue
        # Un puesto en varias fuentes solo se cierra cuando ya no queda ninguna.
        col_jobs.update_many(filtro, {"$pull": {"sources": fuente}})
    ahora = datetime.datetime.now(datetime.UTC).isoformat()
    cerrados = col_jobs.update_many(
        {"active": True, "sources": {"$size": 0}}, {"$set": {"active": False, "last_seen": ahora}}
    ).modified_count
    return cerrados


def activos() -> list[dict]:
    return list(col_jobs.find({"active": True}).sort("posted_date", -1))


def resumen() -> dict:
    return {
        "total": col_jobs.count_documents({}),
        "activos": col_jobs.count_documents({"active": True}),
        "por_fuente": col_jobs.aggregate([{"$group": {"_id": "$source", "n": {"$sum": 1}}}]),
    }