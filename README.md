# AppFactory

![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Version: 1.0.0](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI%20%7C%20GraphQL%20%7C%20PostgreSQL-009688)
![Frontend](https://img.shields.io/badge/frontend-Preact%20%7C%20Vite%20%7C%20Tailwind-673ab8)

**App Factory** is an AI-native software factory that empowers ambitious small teams to build enterprise-grade applications. Combining Domain-Driven Design (DDD), GraphQL, reusable architecture, intelligent agents, and code generation, it transforms lean teams into high-performance software organizations capable of delivering production-ready business applications at scale.

AppFactory is based on the [WebApp project](https://github.com/antoniofregoso/WebApp), which is a basic template for generating web applications with integrated AI.

## Contents

- [Highlights](#highlights)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Database backup and restore](#database-backup-and-restore)
- [Development commands](#development-commands)
- [Documentation](#documentation)
- [Security note](#security-note)
- [License](#license)

## Highlights

**Declarative core**
- Declarative Kanban, list, form, and calendar views
- Reusable field components, relationships, avatars, and localized labels
- Insights dashboards: KPIs, gauges, and charts from declarative definitions

**Search**
- Natural-language global search: an AI interpreter turns questions into
  validated, typed search plans, with automatic fallback to plain text when
  no provider is configured
- PostgreSQL full-text search (`tsvector`/`ts_rank`) and trigram (`pg_trgm`)
  indexes, tuned to stay fast at 100,000+ records per model
- Contextual, in-app help for the search bar

**Security and accounts**
- Access/refresh token session renewal with rotation and reuse detection
- CSRF-protected refresh cookies with absolute session expiration
- Session activity tracking and read-only user log reporting

**Platform**
- Modular parties, talent, and role-based access-control domains
- In-app and browser push notifications
- Read-only MCP reports for authorized users
- Attachment storage with authenticated previews
- FastAPI, GraphQL, SQLModel, PostgreSQL, and Alembic
- Preact, Signals, Tailwind CSS, Vite, and CJ Router

## Architecture

```text
Browser
  └─ Preact dashboard
       ├─ GraphQL API ── FastAPI services ── PostgreSQL
       ├─ Attachment API ── local filestore
       └─ MCP endpoint ── read-only reports
```

Declarative model definitions are distributed by domain under
`backend/app/domains/*/data/`. Depending on the domain, the source files are:

- `system_models.json` or `system_model.json` — models and fields
- `system_model_schemas.json` or `system_model_schema.json` — view layouts

## Prerequisites

- Python 3.11 or newer
- PostgreSQL 15 or newer, including the `pg_dump` and `pg_restore` client tools
- Node.js 20.19+ or 22.12+ and npm
- Docker with Docker Compose, if you prefer containerized PostgreSQL

## Quick start

### Backend

```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Start the bundled PostgreSQL service; skip this if you use another server.
docker compose up -d db
python scripts/setup_database.py
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`, with GraphQL at
`http://localhost:8000/graphql`.

> `scripts/setup_database.py` recreates the configured database. Review
> `DATABASE_URL` before confirming the operation. A successful run also
> installs `pg_trgm`, creates all required trigram/FTS GIN search indexes, and
> verifies them against PostgreSQL before reporting completion.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

The development server is available at `http://localhost:3000` and proxies API
requests to the backend.

### Docker

```bash
cd backend
docker compose up -d db
docker compose build web
docker compose run --rm web python scripts/setup_database.py
docker compose up
```

The setup command asks before replacing the database created by PostgreSQL.
Run the frontend separately with Vite for the best development experience.

## Database backup and restore

Both commands read `DATABASE_URL` from `backend/.env`. From `backend`:

```bash
# Creates backups/<database>_<timestamp>.dump
python scripts/backup_database.py

# Optional custom destination
python scripts/backup_database.py --output /path/to/backup.dump

# Replaces the existing database objects after confirmation
python scripts/restore_database.py backups/<backup-file>.dump

# Non-interactive restore
python scripts/restore_database.py backups/<backup-file>.dump --yes
```

Backup files can contain sensitive application data. The default `backups/`
directory is ignored by Git; store exported files securely.

## Development commands

| Task               | Command                                        |
| ------------------ | ---------------------------------------------- |
| Backend tests      | `cd backend && .venv/bin/pytest -q`            |
| Backend migrations | `cd backend && .venv/bin/alembic upgrade head` |
| Frontend tests     | `cd frontend && npm test -- --run`             |
| Frontend lint      | `cd frontend && npm run lint`                  |
| Production build   | `cd frontend && npm run build`                 |

## Documentation

Start with the [documentation index](./Doc/INDEX.md), or jump directly to:

- [Database setup](./Doc/DATABASE_SETUP.md)
- [Declarative views](./Doc/VIEWS_FORMAT.md)
- [Data format](./Doc/DATA_FORMAT.md)
- [Frontend guide](./Doc/FRONTEND.md)
- [Backend guide](./Doc/BACKEND.md)
- [GraphQL reference](./Doc/GRAPHQL_QUERIES.md)
- [Insights format](./Doc/INSIGHTS_FORMAT.md)
- [Global search design](./Doc/AI_SEARCH_DESIGN.md)
- [MCP reports](./Doc/MCP.md)
- [Error handling guide](./Doc/ERROR_HANDLING_GUIDE.md)
- [Quality and testing guide](./Doc/QUALITY_AND_TESTING_GUIDE.md)

## Security note

The seed credentials are intended for local development only. Replace default
passwords and secrets before exposing any environment outside your workstation.

## License

See the backend [license file](./backend/LICENSE).
