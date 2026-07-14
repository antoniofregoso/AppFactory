# Backend Guide

The backend is a FastAPI application with a Strawberry GraphQL API, SQLModel
entities, PostgreSQL persistence, and Alembic migrations. Business logic is
organized by domain and separated into models, repositories, services, and API
or GraphQL adapters.

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/setup_database.py
uvicorn main:app --reload
```

Useful endpoints:

| Endpoint                      | Purpose                              |
| ----------------------------- | ------------------------------------ |
| `/graphql`                    | GraphQL API and development explorer |
| `/mcp`                        | Streamable HTTP MCP server           |
| `/api/system/attachments/...` | Authenticated attachment content     |

## Project structure

```text
backend/
├── app/
│   ├── core/                  # Configuration, database, auth, and errors
│   ├── domains/
│   │   ├── system/            # Generic models, schemas, views, and platform services
│   │   └── users/             # Users, sessions, authentication, and activity logs
│   └── mcp/                   # Read-only MCP authentication and reports
├── migrations/versions/       # Alembic revisions
├── scripts/setup_database.py  # Destructive clean setup and seed loader
├── tests/                     # Pytest suite
├── main.py                    # FastAPI application and lifespan tasks
└── requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and review every value. The most important
settings are:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_db
SECRET_KEY=replace-this-value
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
SESSION_ABSOLUTE_EXPIRE_DAYS=30
LOG_LEVEL=INFO
DB_ECHO=false
```

Attachment, notification, heartbeat, MCP, and search settings are documented
in `.env.example` and their feature-specific guides.

## Database workflows

### Create a clean development database

```bash
python scripts/setup_database.py
```

This command drops the configured database after confirmation, recreates the
schema from SQLModel metadata, and loads the canonical JSON data files. See
[Database Setup](./DATABASE_SETUP.md) for ordering and troubleshooting.

### Apply migrations

```bash
alembic upgrade head
```

Create a migration after changing persisted models:

```bash
alembic revision -m "describe the change"
```

Review generated migrations before applying them. Declarative model or view
changes may also require a data migration for existing installations.

## Domain architecture

Use the following dependency direction:

```text
GraphQL / API adapter
  └─ service
       └─ repository
            └─ SQLModel entity
```

- Models define persistence and relationships.
- Repositories own database queries.
- Services enforce validation, authorization, and business rules.
- GraphQL and HTTP adapters translate transport input and output.

Avoid importing GraphQL types into services or placing business rules in
resolvers.

## Declarative models and views

The generic system-model service combines persisted metadata with records and
returns a frontend-ready payload.

Canonical seed definitions:

- `app/domains/system/data/system_models.json`
- `app/domains/system/data/system_model_schemas.json`

`system_models.json` defines the model and its field types. The schema file
defines where those fields appear in Kanban, list, form, and calendar views.
Relationship fields such as `many2one_avatar` are serialized as objects:

```json
{
  "uuid": "user-uuid",
  "name": "Ana Admin",
  "display_name": "Ana Admin",
  "avatar": "/api/system/attachments/avatar/content",
  "model": "user.user"
}
```

## Authentication and authorization

- Access tokens are short-lived JWTs.
- Refresh tokens rotate and are stored only as hashes.
- Protected GraphQL operations use authentication permission classes.
- Services enforce record ownership and privileged-field rules.
- Read-only models must be enforced by the backend; hiding frontend controls is
  only a usability measure.

See [Session Renewal](./SESSION_RENEWAL.md) for the full token lifecycle.

## Background tasks

The FastAPI lifespan starts periodic jobs such as:

- Closing stale activity logs
- Generating task reminder notifications
- Dispatching notification delivery work

Jobs should log failures without terminating the application lifespan.

## Attachments

Files are stored outside PostgreSQL. Database rows contain metadata while the
configured filestore contains bytes.

```env
FILESTORE_ROOT=/var/lib/webapp/filestore
FILESTORE_NAMESPACE=app_db
ATTACHMENT_MAX_SIZE_BYTES=26214400
```

Attachment downloads require authentication. Image components obtain local
attachment content through authenticated fetches and object URLs.

## Testing and quality

```bash
# Entire backend suite
pytest -q

# One file
pytest tests/test_system_model_view_service.py -q

# One test
pytest tests/test_system_model_view_service.py::test_name -q

# Style checks
flake8 --jobs 1 app tests
```

Tests should cover service rules, authorization boundaries, serialization, and
the declarative metadata that drives the frontend.

## Docker

From `backend`:

```bash
docker compose up --build
```

The backend container applies migrations before starting Uvicorn. Source code
is mounted for hot reload, while PostgreSQL and attachment data use named
volumes.

## Related documentation

- [Database Setup](./DATABASE_SETUP.md)
- [GraphQL Queries](./GRAPHQL_QUERIES.md)
- [View Format](./VIEWS_FORMAT.md)
- [Notifications](./NOTIFICATIONS.md)
- [MCP Reports](./MCP.md)
- [Quality and Testing](./QUALITY_AND_TESTING_GUIDE.md)
