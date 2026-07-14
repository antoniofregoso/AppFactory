# WebApp

![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI%20%7C%20GraphQL%20%7C%20PostgreSQL-009688)
![Frontend](https://img.shields.io/badge/frontend-Preact%20%7C%20Vite%20%7C%20Tailwind-673ab8)

WebApp is a schema-driven application template for building internal tools,
operational dashboards, and reporting systems. Models, fields, views, and
insights are declared as data, allowing the same frontend and backend to adapt
to different business domains with minimal custom code.

## Contents

- [Highlights](#highlights)
- [Architecture](#architecture)
- [Quick start](#quick-start)
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
- Step-up re-authentication (password/MFA) for critical operations
- Session activity tracking and read-only user log reporting

**Platform**
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

The canonical model definitions live in:

- `backend/app/domains/system/data/system_models.json` — models and fields
- `backend/app/domains/system/data/system_model_schemas.json` — view layouts

## Quick start

### Backend

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/setup_database.py
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`, with GraphQL at
`http://localhost:8000/graphql`.

> `scripts/setup_database.py` recreates the configured database. Review
> `DATABASE_URL` before confirming the operation.

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
docker compose up --build
```

This starts PostgreSQL and the backend. Run the frontend separately with Vite
for the best development experience.

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
