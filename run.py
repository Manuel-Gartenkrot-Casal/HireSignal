import argparse
import sys

from hire_signal.db import crear_indices, guardar_jobs, marcar_inactivos
from hire_signal.pipeline import run


def main():
    parser = argparse.ArgumentParser(description="HireSignal — feed de inteligencia de contratación")
    parser.add_argument("--sources", nargs="*", default=None,
                        help="Fuentes a ejecutar: greenhouse lever ashby getonbrd (default: todas)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Límite de jobs por fuente (debug)")
    parser.add_argument("--dry-run", action="store_true",
                        help="No escribir en MongoDB, solo imprimir")
    args = parser.parse_args()

    jobs = run(sources=args.sources, limit=args.limit)

    if args.dry_run:
        for job in jobs:
            print(f"  [{job.source}] {job.company} | {job.title} | {job.seniority} | {job.role_category} | {job.tech}")
        print(f"\nTotal: {len(jobs)} jobs")
        return 0

    crear_indices()
    res = guardar_jobs(jobs)
    print(f"  Insertados: {res['insertados']} | Actualizados: {res['actualizados']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())