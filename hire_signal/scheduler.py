import datetime
import os

from apscheduler.schedulers.background import BackgroundScheduler

from .db import crear_indices, guardar_jobs, marcar_inactivos
from .pipeline import COMPANIES_PATH, _cargar_companies, run

scheduler = BackgroundScheduler()

# Lunes 8:00 AM (timezone local del contenedor; ajustar con TZ)
CRON_DAY = "mon"
CRON_HOUR = int(os.getenv("CRON_HOUR", "8"))
CRON_MINUTE = int(os.getenv("CRON_MINUTE", "0"))


def run_semanal():
    print(f"[{datetime.datetime.now()}] HireSignal: corrida semanal iniciada", flush=True)
    jobs = run()
    if not jobs:
        # Falla visible (workflow en rojo) en vez de un run "verde" sin datos.
        raise RuntimeError("Ninguna fuente devolvió jobs: no se actualizó nada")
    crear_indices()
    res = guardar_jobs(jobs)
    inactivos = marcar_inactivos(jobs)
    print(
        f"[scheduler] Insertados: {res['insertados']} | Actualizados: {res['actualizados']} | Inactivados: {inactivos}",
        flush=True,
    )

    problemas = _fuentes_vacias(jobs)
    if os.getenv("GOOGLE_SHEET_ID"):
        try:
            from .sheets import exportar

            print(f"[scheduler] Sheet actualizado: {exportar([])} filas.", flush=True)
        except Exception as e:
            problemas.append(f"Sheets: {e}")
    if problemas:
        # Los datos ya quedaron guardados; esto solo marca el run en rojo.
        raise RuntimeError("Corrida incompleta: " + "; ".join(problemas))


def _fuentes_vacias(jobs) -> list[str]:
    """Fuentes con empresas configuradas que no devolvieron ningún job."""
    con_jobs = {j.source for j in jobs}
    return [
        f"{ats} sin jobs"
        for ats in {c["ats"] for c in _cargar_companies(COMPANIES_PATH)}
        if ats not in con_jobs
    ]


def start_scheduler():
    if scheduler.get_job("weekly_hiresignal"):
        return scheduler.get_job("weekly_hiresignal")
    proxima = datetime.datetime.now() + datetime.timedelta(seconds=10)
    job = scheduler.add_job(
        run_semanal,
        "cron",
        day_of_week=CRON_DAY,
        hour=CRON_HOUR,
        minute=CRON_MINUTE,
        id="weekly_hiresignal",
        next_run_time=proxima,
        misfire_grace_time=3600,
    )
    scheduler.start()
    print(f"[scheduler] Programado: lunes {CRON_HOUR:02d}:{CRON_MINUTE:02d} (primera corrida en 10s)", flush=True)
    return job


if __name__ == "__main__":
    start_scheduler()
    try:
        import time

        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass