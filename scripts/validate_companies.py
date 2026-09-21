import json
import sys
from pathlib import Path

import requests

BASE = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=5",
}
# ATS sin slug en la URL: valida contra su endpoint booleano.
NO_SLUG = {
    "meli": "https://careers-meli.mercadolibre.com/api/positions?start=0&country=Argentina",
}
TIMEOUT = 12


def validar(companies_path: Path) -> None:
    data = json.loads(companies_path.read_text(encoding="utf-8"))
    companies = data.get("companies", [])
    ok = 0
    falla = 0
    for c in companies:
        ats = c.get("ats")
        slug = c.get("slug", "")
        if not slug:
            if ats in NO_SLUG:
                slug = c.get("country") or "-"
                url = NO_SLUG[ats]
            else:
                print(f"  [SIN SLUG] {c['name']} ({ats})")
                continue
        else:
            url = BASE[ats].format(slug=slug)
        try:
            r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                ok += 1
                print(f"  [OK] {c['name']} ({ats}/{slug}) {r.status_code}")
            else:
                falla += 1
                print(f"  [FAIL] {c['name']} ({ats}/{slug}) {r.status_code}")
        except Exception as e:
            falla += 1
            print(f"  [ERR] {c['name']} ({ats}/{slug}) {e}")
    print(f"\nResumen: {ok} ok, {falla} falla.")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("hire_signal/config/companies.json")
    validar(path)