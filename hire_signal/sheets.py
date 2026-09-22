import json
import os
import tempfile

from dotenv import load_dotenv

load_dotenv()

COLUMNAS = ["Empresa", "Rol", "Seniority", "Tech", "Fuente", "Fecha", "Link"]


def _credenciales_path() -> str:
    """Devuelve una ruta a un service-account JSON.

    Soporta dos modos:
    - GOOGLE_SHEETS_CREDS_PATHS: ruta a un archivo existente (local).
    - GOOGLE_SHEETS_CREDS: contenido JSON completo (secret de GitHub Actions).
    """
    path = os.getenv("GOOGLE_SHEETS_CREDS_PATH")
    content = os.getenv("GOOGLE_SHEETS_CREDS")
    if path and os.path.exists(path):
        return path
    if content:
        try:
            json.loads(content)
        except json.JSONDecodeError:
            raise ValueError("GOOGLE_SHEETS_CREDS no es un JSON service-account válido")
        tmp = os.path.join(tempfile.gettempdir(), "hs-service-account.json")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        return tmp
    if os.path.exists("service-account.json"):
        return "service-account.json"
    raise ValueError(
        "Credenciales de Google Sheets no encontradas: definí GOOGLE_SHEETS_CREDS "
        "(JSON) o GOOGLE_SHEETS_CREDS_PATH (ruta a archivo)"
    )


def conectar_sheet():
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(_credenciales_path(), scopes=scopes)
    gc = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID no configurado en .env")
    return gc.open_by_key(sheet_id)


def exportar(jobs: list[dict], sheet_id: str | None = None):
    """Escribe los jobs (dicts con la misma forma que col_jobs) en el sheet.

    Columnas (del plan): Empresa, Rol, Seniority, Tech, Fuente, Fecha, Link.
    """
    from .db import col_jobs

    if sheet_id is not None:
        os.environ["GOOGLE_SHEET_ID"] = sheet_id

    filas = []
    for doc in col_jobs.find({"active": True}).sort("posted_date", -1):
        filas.append(
            [
                doc.get("company", ""),
                doc.get("title", ""),
                doc.get("seniority", ""),
                doc.get("tech", ""),
                ", ".join(doc.get("sources", [doc.get("source", "")])),
                (doc.get("posted_date") or "")[:10],
                doc.get("url", ""),
            ]
        )

    sh = conectar_sheet()
    ws = sh.worksheet("Feed") if "Feed" in [w.title for w in sh.worksheets()] else sh.add_worksheet("Feed", 1000, 20)
    ws.clear()
    ws.append_row(COLUMNAS)
    if filas:
        ws.append_rows(filas, value_input_option="USER_ENTERED")
    return len(filas)


if __name__ == "__main__":
    n = exportar([])
    print(f"Sheet actualizado con {n} filas.")