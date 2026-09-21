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