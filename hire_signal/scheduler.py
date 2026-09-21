import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from .db import crear_indices, guardar_jobs, marcar_inactivos
from .pipeline import run

scheduler = BackgroundScheduler()

# Lunes 8:00 AM (timezone local del contenedor; ajustar con TZ)
CRON_DAY = "mon"
CRON_HOUR = int(__import__("os").getenv("CRON_HOUR", "8"))
CRON_MINUTE = int(__import__("os").getenv("CRON_MINUTE", "0"))


def run_semanal():
    print(f"[{datetime.datetime.now()}] HireSignal: corrida semanal iniciada", flush=True)
    jobs = run()
    if not jobs:
        print("[scheduler] Sin jobs. Guardado omitido.", flush=True)
        return
    crear_indices()
    res = guardar_jobs(jobs)
    activos_por_fuente: dict[str, set[str]] = {}
    for j in jobs:
        activos_por_fuente.setdefault(j.source, set()).add(j.dedup_key)
    inactivos = marcar_inactivos(activos_por_fuente)
    print(
        f"[scheduler] Insertados: {res['insertados']} | Actualizados: {res['actualizados']} | Inactivados: {inactivos}",
        flush=True,
    )

    if __import__("os").getenv("GOOGLE_SHEET_ID"):
        try:
            from .sheets import exportar

            n = exportar([])
            print(f"[scheduler] Sheet actualizado: {n} filas.", flush=True)
        except Exception as e:
            print(f"[scheduler] Error exportando a Sheets: {e}", flush=True)


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