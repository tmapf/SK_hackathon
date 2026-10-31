# VPS deployment checklist

## 1. Prepare the host

- Install Docker Engine and the Compose plugin.
- Open ports `80`/`443` (or the host port mapped by `HTTP_PORT`).
- Point your domain DNS A/AAAA records at the VPS.

## 2. Configure secrets

```bash
cp .env.example .env
```

Required values:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Session signing secret |
| `POSTGRES_PASSWORD` | Database password |
| `CORS_ORIGINS` | Public site origin(s), comma-separated |
| `COOKIE_SECURE` | `true` behind HTTPS |
| `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile |
| `CONTACT_EMAIL` | Shown in privacy/config if desired |

Never commit the real `.env`.

## 3. Start the stack

```bash
docker compose up --build -d
docker compose ps
curl -f http://localhost:8080/api/health
```

## 4. Bootstrap

```bash
docker compose exec api python create_admin.py --username admin --password 'replace-me'
```

Then sign in at `/admin` and click **Refresh properties**.

The first Warsaw sync is N+1 (list + one location request per property) and can take several minutes.

## 5. TLS

Recommended: put Caddy/Traefik/Nginx on the host in front of Compose port `8080`, or extend `nginx/default.conf` with certificate mounts.

Set:

```env
COOKIE_SECURE=true
CORS_ORIGINS=https://your-domain.example
```

## 6. Backups

Postgres data lives in the `postgres_data` volume.

Example dump:

```bash
docker compose exec db pg_dump -U warsaw warsaw_ideas > backup-$(date +%F).sql
```

Restore into a fresh volume with `psql`.

## 7. Ongoing jobs

- Daily property sync: APScheduler inside the API container
- Daily retention purge for suggestions older than `RETENTION_DAYS`
- Manual sync available in the admin UI

## 8. Smoke verification

```bash
cd frontend
npm install
npx playwright install chromium
E2E_BASE_URL=https://your-domain.example npm run test:e2e
```

Desktop and mobile Playwright projects cover the public shell and admin login route.
