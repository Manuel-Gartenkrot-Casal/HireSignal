import os

from dotenv import load_dotenv

load_dotenv()

COLUMNAS = ["Empresa", "Rol", "Seniority", "Tech", "Fuente", "Fecha", "Link"]


def conectar_sheet():
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_path = os.getenv("GOOGLE_SHEETS_CREDS", "service-account.json")
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
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