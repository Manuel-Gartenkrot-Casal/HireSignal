# HireSignal

Feed de inteligencia de contratación: scraping de vacantes de empresas target (ATS Greenhouse / Lever / Ashby / GetOnBrd), normalización, dedupe y dashboard web.

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

## API

| Endpoint | Descripción |
| --- | --- |
| `GET /api/jobs?role=&seniority=&source=&q=&limit=` | Vacantes activas filtradas |
| `GET /api/stats` | total, por seniority/rol/fuente, últimos 30 días |
| `GET /api/health` | estado de la conexión a MongoDB |

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