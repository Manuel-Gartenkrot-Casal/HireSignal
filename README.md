# HireSignal

Señales de compra para software factories y agencias de staffing IT: qué empresas tech
están acelerando su contratación y en qué áreas (data, backend, DevOps…), a partir de sus vacantes públicas
(ATS Greenhouse / Lever / Ashby / SmartRecruiters / GetOnBrd). Normalización, dedupe,
dashboard con ranking por empresa y export CSV para el CRM.

## Vender (modelo concierge)

- Sin clave, el dashboard muestra el top 10 del ranking y un formulario de prueba gratis
  (`POST /api/leads` → colección `leads`).
- Con clave (`?key=` una vez; queda en el navegador) se ven todas las empresas y el export CSV.
- Altas y bajas a mano con un link de pago (Stripe o Mercado Pago):

```bash
python scripts/clave.py nueva cliente@agencia.com   # imprime la clave y el link
python scripts/clave.py revocar cliente@agencia.com
python scripts/clave.py listar
```

## Arquitectura

```
hire_signal/   Scrapers Python + pipeline + scheduler
dashboard/     API Express (MongoDB) + frontend React/Vite (shadcn/ui + charts Bklit + KokonutUI + motion)
docker-compose.yml   mongo + scrapers + dashboard
```

## Requisitos

- Python 3.12+ (`pip install -r requirements.txt`)
- Node 22+ (solo para el dashboard)
- MongoDB local en `localhost:27017` (o `docker compose up mongo`)

## 1. Pipeline de scraping

```bash
# todo (todas las fuentes activas)
python run.py

# fuentes puntuales y dry-run
python run.py --sources getonbrd --dry-run
python run.py --sources greenhouse --limit 30
```

Guarda en MongoDB (DB `hiresignal`, colección `jobs`), con dedupe por empresa+cargo y
fusión de fuentes (`sources[]`). Se marca como `active: false` lo que desaparece del feed.

Scheduler semanal (lunes 8:00):

```bash
python -m hire_signal.scheduler
```

Exportar a Google Sheets (Fase 2, requiere credenciales):

```bash
python scripts/export_sheet.py
```

## 2. Dashboard (MVP)

### A) Con Docker Compose (recomendado)

```bash
cp .env.example .env
docker compose up --build
# dashboard en http://localhost:3000
```

### B) Local (dev)

```bash
# backend API (Express) en :3000
cd dashboard
npm install
npm run dev

# frontend (Vite con proxy /api -> :3000) en :5173
cd dashboard/web
npm install
npm run dev
```

### C) Local (producción estática servida por Express)

```bash
cd dashboard
npm run setup   # instala deps + build web/dist
npm start       # sirve UI + API en :3000
```

Variables de entorno del dashboard (`dashboard/.env`):

```
PORT=3000
MONGO_URI=mongodb://localhost:27017/hiresignal
MONGO_DB=hiresignal
```

## 3. Deploy híbrido (Vercel + MongoDB Atlas + GitHub Actions)

Arquitectura sin servidor propio: el dashboard (frontend + API) corre en Vercel y los
scrapers corren como cron de GitHub Actions, ambos compartiendo un clúster MongoDB Atlas.

```
GitHub Actions (cron semanal)
        │   scrape → guarda
        ▼
   ┌─────────┐        ┌──────────┐        ┌──────────┐
   │  Atlas   │◄──────│  Vercel   │◄──────│ Browser  │
   │  MongoDB │   API │  /api/*   │  UI   │          │
   └─────────┘        └──────────┘        └──────────┘
```

### 3.1 MongoDB Atlas

1. Crear clúster **M0 free** en https://www.mongodb.com/atlas (DB `hire_signal`).
2. Database Access → crear usuario con contraseña.
3. Network Access → `Allow access from anywhere` (`0.0.0.0/0`, necesario para GH Actions y Vercel).
4. Copiar la URI `mongodb+srv://...` — esa será `MONGO_URI`.

### 3.2 Vercel (frontend + API)

```bash
cd dashboard
npx vercel        # login + link al proyecto
npx vercel --prod
```

En el dashboard de Vercel (Proyecto → Settings → Environment Variables) agregar en
Production/Preview/Development:

| Variable | Valor |
| --- | --- |
| `MONGO_URI` | `mongodb+srv://...` de Atlas |
| `MONGO_DB` | `hiresignal` |

La config de `dashboard/vercel.json` ya genera `web/dist` como salida estática y
monta `api/index.js` (función serverless Express) para `/api/*`.

### 3.3 GitHub Actions (scrapers semanales)

Agregar los **secrets** del repo (Settings → Secrets and variables → Actions):

| Secret | Valor |
| --- | --- |
| `MONGO_URI` | la misma URI `mongodb+srv://...` |
| `MONGO_DB` | `hiresignal` |
| `GOOGLE_SHEET_ID` | (opcional) id del sheet para exportar |

El workflow `.github/workflows/scrape.yml` corre:
- todos los **lunes 08:00 UTC** (cron);
- al hacer **push** en `hire_signal/**` o `requirements.txt`;
- manualmente desde la pestaña *Actions* → *Run workflow*.

Ejecuta `hire_signal.scheduler.run_semanal()`, que scrapea todas las fuentes, hace upsert
por `dedup_key`, marca inactivos lo que desaparece y (si hay `GOOGLE_SHEET_ID`) exporta a Sheets.

## Tests y CI

```bash
pip install pytest ruff
ruff check . --exclude dashboard
PYTHONPATH=. python -m pytest -q tests
```

GitHub Actions (`ci.yml`) corre lo mismo más `tsc` y el build del dashboard en cada PR.

## API del dashboard

| Endpoint | Parámetros | Devuelve |
|---|---|---|
| `GET /api/companies` | `days` (default 7); header `x-hs-key` | `{ completo, total, acelerando, empresas }`; sin clave válida, solo las 10 primeras. Por empresa: `activas`, `nuevas` (vistas por primera vez en `days`, sin contar la primera carga de la empresa), `senior` y top 3 `areas` (sin `other`); ordenado por `nuevas` |
| `GET /api/jobs` | `company` (exacto), `q` (título), `role`, `seniority`, `source`, `days` (publicadas en los últimos N días), `limit` (máx. 1000 con clave `x-hs-key`, 25 sin ella) | vacantes activas, más recientes primero |
| `POST /api/leads` | JSON `{ email, empresa }` | 201; 400 si el email no es válido; 429 pasadas 5 solicitudes por hora desde la misma IP |
| `GET /api/stats` | - | totales por seniority, rol y fuente, publicaciones de los últimos 30 días y `actualizado` (último `last_seen`) |
| `GET /api/health` | - | `{ ok, db }` |

Todos los parámetros se tratan como texto (sin operadores de Mongo) y los errores no exponen detalles internos.

## Refresco semanal

Cada lunes el workflow `scrape.yml` vuelve a scrapear todo y hace upsert por `dedup_key` (empresa + título).
Los puestos que dejan de aparecer se marcan inactivos solo para las empresas que respondieron en esa corrida, y
si una fuente cerraría más de la mitad de sus puestos se omite el cierre (probable respuesta incompleta).
El run termina en rojo si ninguna fuente devolvió jobs o si una fuente configurada vino vacía.
