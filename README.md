# Warsaw Property Ideas Portal

Bilingual public map for browsing Warsaw municipal rental and sale properties and submitting private business-use proposals. Built with React + FastAPI + PostgreSQL and deployed with Docker Compose.

## Features

- Interactive Leaflet map with clustered markers
- Rental/sale toggle, address search, district and area filters
- Property side panel / mobile bottom sheet with proposal form
- Database-managed bilingual proposal categories
- Private admin dashboard: suggestions, CSV export, category/translation management, sync controls, popularity map
- Daily property sync from the official Warsaw map API
- Cloudflare Turnstile, honeypot, and rate limiting
- 12-month suggestion retention job

## Project layout

- `backend/` – FastAPI API, sync jobs, admin auth, Alembic migrations
- `frontend/` – React + TypeScript + Vite UI
- `nginx/` – reverse proxy with rate limits
- `scripts/create_admin.py` – create/update an administrator
- `map_service.py` – offline GeoJSON export CLI

## Quick start (Docker)

1. Copy environment file:

```bash
cp .env.example .env
```

2. Set at least:

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY`  
  For local smoke tests without Turnstile, set `TURNSTILE_BYPASS=true`.

3. Start services:

```bash
docker compose up --build
```

4. Create an admin user:

```bash
docker compose exec api python create_admin.py --username admin --password 'choose-a-strong-password'
```

5. Open `http://localhost:8080`.

6. Trigger an initial property sync from **Admin → Refresh properties**. The first sync calls Warsaw’s list endpoints and one location lookup per property, so it can take several minutes.

## Local development without Docker

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
export DATABASE_URL=postgresql+psycopg://warsaw:warsaw@localhost:5432/warsaw_ideas
export SECRET_KEY=dev-secret
export TURNSTILE_BYPASS=true
export ENVIRONMENT=development
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to `http://localhost:8000`.

## Tests

```bash
cd backend
pytest

cd ../frontend
npm test
npm run build
```

Playwright smoke tests (desktop + mobile) against a running deployment:

```bash
cd frontend
npx playwright install chromium
E2E_BASE_URL=http://localhost:8080 npm run test:e2e
```

## Operations notes

- **Sync schedule:** daily at `SYNC_CRON_HOUR`:`SYNC_CRON_MINUTE` (UTC of the container), plus manual admin refresh.
- **Retention:** suggestions older than `RETENTION_DAYS` (default 365) are deleted daily.
- **Tiles:** default OpenStreetMap tiles; override with `TILE_URL` / `TILE_ATTRIBUTION` if you move to a commercial tile provider.
- **TLS:** terminate TLS on your VPS reverse proxy or extend the included Nginx config with certificates.
- **Backups:** back up the Postgres volume regularly; restore by replacing the volume and restarting Compose.
- **Privacy:** public UI never exposes announcement URLs or suggestion content. Admins can view emails and official announcement links.

## Public API used for properties

Only verified Warsaw endpoints are used:

- `GET https://mapa.um.warszawa.pl/api/modul-mapowy/open/nieruchomosci/wynajem`
- `GET https://mapa.um.warszawa.pl/api/modul-mapowy/open/nieruchomosci/sprzedaz`
- `GET .../wynajem/lokalizacja?id={id}`
- `GET .../sprzedaz/lokalizacja?id={id}`

Records with missing coordinates (`null,null`) are skipped.
# SK_hackathon
