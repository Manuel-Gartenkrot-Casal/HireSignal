import json
import os
import tempfile
from collections import Counter

from dotenv import load_dotenv

load_dotenv()

COLUMNAS = ["Empresa", "Rol", "Seniority", "Tech", "Fuente", "Fecha", "Link"]

# Métricas que el modelo agencies necesita ver en el "Resumen"
METRICAS_RESUMEN = [
    "Total vacantes activas",
    "Distribución seniority",
    "Top 5 roles",
    "Top 5 tech stack",
    "Top 5 empresas contratando",
]


def _credenciales_path() -> str:
    """Devuelve una ruta a un service-account JSON.

    Soporta dos modos:
    - GOOGLE_SHEETS_CREDS_PATH: ruta a un archivo existente (local).
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


def _contar_seniority(seniority_list: list[str]) -> dict[str, int]:
    """Cuenta la distribución de seniority, normalizando 'unknown'."""
    distrib = {"junior": 0, "mid": 0, "senior": 0, "lead": 0, "unknown": 0}
    for s in seniority_list:
        si = (s or "").lower().strip()
        if si in distrib:
            distrib[si] += 1
        else:
            distrib["unknown"] += 1
    return distrib


def _top_k(lst: list[str], k: int = 5) -> list[tuple[str, int]]:
    c = Counter(lst)
    return c.most_common(k)


def _obtener_top_empresas(docs) -> list[tuple[str, int]]:
    empresas = [doc.get("company", "") for doc in docs if doc.get("company")]
    return Counter(empresas).most_common(5)


def _obtener_datos_desde_sheet(sh) -> list[dict]:
    """Extrae los rows de la hoja principal 'Feed'."""
    rows = sh.worksheet("Feed").get_all_records()
    return rows


def crear_hoja_resumen(sh) -> None:
    """Crea o actualiza la hoja 'Resumen' con métricas clave.

    Se ejecuta sobre los datos de la hoja 'Feed'.
    """
    docs = _obtener_datos_desde_sheet(sh)
    if not docs:
        return

    total = len(docs)
    seniority_dist = _contar_seniority([d.get("seniority", "") for d in docs])
    top_roles = _top_k([d.get("role_category", "") for d in docs], 5)
    top_stacks = _top_k([d.get("tech", "") for d in docs], 5)
    top_empresas = _obtener_top_empresas(docs)

    # Buscar o crear la hoja "Resumen"
    hoja_nombre = "Resumen"
    existentes = [w.title for w in sh.worksheets()]
    if hoja_nombre in existentes:
        ws = sh.worksheet(hoja_nombre)
        ws.clear()
    else:
        ws = sh.add_worksheet(hoja_nombre, 20, 20)

    # Escribir encabezados
    ws.update_cell(1, 1, "Métrica")
    ws.update_cell(1, 2, "Valor")

    # Fila 2: Total vacantes
    ws.update_cell(2, 1, "Total vacantes activas")
    ws.update_cell(2, 2, total)

    # Fila 3: Distribución seniority
    ws.update_cell(3, 1, "Distribución seniority")
    # Escribir los valores en la columna 2, filas 3-7
    ws.update_cell(3, 2, seniority_dist.get("junior", 0))
    ws.update_cell(4, 2, seniority_dist.get("mid", 0))
    ws.update_cell(5, 2, seniority_dist.get("senior", 0))
    ws.update_cell(6, 2, seniority_dist.get("lead", 0))
    ws.update_cell(7, 2, seniority_dist.get("unknown", 0))

    # Fila 8: Top 5 roles
    ws.update_cell(8, 1, "Top 5 roles")
    roles_texto = ", ".join([f"{r[0]} ({r[1]})" for r in top_roles])
    ws.update_cell(8, 2, roles_texto)

    # Fila 9: Top 5 tech stack
    ws.update_cell(9, 1, "Top 5 tech stack")
    stacks_texto = ", ".join([f"{s[0]} ({s[1]})" for s in top_stacks])
    ws.update_cell(9, 2, stacks_texto)

    # Fila 10: Top 5 empresas contratando
    ws.update_cell(10, 1, "Top 5 empresas contratando")
    empresas_texto = ", ".join([f"{e[0]} ({e[1]})" for e in top_empresas])
    ws.update_cell(10, 2, empresas_texto)


def exportar(jobs: list[dict], sheet_id: str | None = None):
    """Escribe los jobs (dicts con la misma forma que col_jobs) en el sheet.

    Columnas (del plan): Empresa, Rol, Seniority, Tech, Fuente, Fecha, Link.

    Además, crea o actualiza automáticamente una hoja "Resumen" con métricas
    clave para agencias de recruiting: total vacantes, distribución seniority,
    top roles, top tech stack y top empresas contratando.
    """
    from .db import col_jobs

    if sheet_id is not None:
        os.environ["GOOGLE_SHEET_ID"] = sheet_id

    sh = conectar_sheet()

    # 1. Escribir la hoja "Feed" con todos los jobs (como antes)
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

    ws_feed = sh.worksheet("Feed") if "Feed" in [w.title for w in sh.worksheets()] else sh.add_worksheet("Feed", 1000, 20)
    ws_feed.clear()
    ws_feed.append_row(COLUMNAS)
    if filas:
        ws_feed.append_rows(filas, value_input_option="USER_ENTERED")

    # 2. Crear/actualizar la hoja "Resumen" con métricas para agencies
    crear_hoja_resumen(sh)

    return len(filas)


if __name__ == "__main__":
    n = exportar([])
    print(f"Sheet actualizado con {n} filas.")