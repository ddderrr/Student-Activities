# Student Activities

Run from the project root in PowerShell or WSL, with Docker Desktop running:

```sh
docker compose up -d --build
```

Open http://localhost:5174 and http://127.0.0.1:8000/docs.
All three services run in Docker; do not start a local Vite or Uvicorn server
on the same ports. Docker keeps Linux dependencies separate from host installations.

For a new checkout, copy `.env.example` to `.env` and set `POSTGRES_PASSWORD`.
Existing `.env` files and PostgreSQL volumes must be preserved.

Development settings in root `.env`:

```dotenv
POSTGRES_PORT=5433
FRONTEND_PORT=5174
VITE_API_URL=http://127.0.0.1:8000
ADMIN_BYPASS_ENABLED=true
```

`VITE_API_URL` is a browser URL, not a Docker service hostname. Compose passes
it to the development server and production build. Rebuild after changing it.
The backend connects to `db:5432`; the host DB port is for tools outside Docker.
Explicit process environment variables take precedence over `backend/.env`,
which takes precedence over root `.env` when running Python locally.

The development override enables reload and applies the existing idempotent,
non-destructive schema upgrades at startup. It does not seed demo records or
reset the database. Production (`docker compose -f compose.yml up -d --build`)
does not enable development schema updates; apply reviewed migrations separately
and disable the development admin bypass in the production environment.

```sh
docker compose ps
docker compose logs --tail 100 backend frontend
docker compose exec -T backend pytest -q -p no:cacheprovider
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run build
docker compose stop
```
# Activity Hours

Activities and external submissions store `activity_hours` as `NUMERIC(10,2)`.
Existing records start at zero; the new creation/submission forms require positive
hours. Legacy API clients may omit the field, preserving their existing behavior.
Editing an internal activity accepts zero for legacy records.

Internal hours count once per membership when the activity is completed, or when
its end date/time has passed, matching the existing Dashboard completion rule.
The three-source breakdown counts the student's own-major activities, central
faculty activities, and approved external activities. Activities owned by another
major remain visible in history but do not enter this breakdown.
Cancelled activities never contribute. External hours count only after approval.
Totals are calculated from source activity records; editing hours updates totals.
Skill scores and their existing eligibility rules remain unchanged.

Development Compose startup automatically applies
`backend/migration_add_activity_hours.sql` without resetting data. For a deployment
without `DEV_SCHEMA_UPDATES`, apply that SQL before starting the updated backend.
Transcript PDF totals follow the selected scope and year filters; Student page
summaries show the student's overall accumulated hours.

Student Skills and Admin individual radars use the same Major / Faculty / External
profile calculation. External profiles contain only that student's approved
external evidence and have no population average or benchmark. Admin aggregate
statistics and evaluated-student counts use internal evidence only. The legacy
personal all-sources skill field remains explicitly identified as such; source
buttons and Skill PDF exports select one independent dataset. Transcript PDFs show
personal skills for the chosen records, with source labels and hour breakdowns.
