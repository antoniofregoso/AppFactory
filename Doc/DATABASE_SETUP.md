# Database Setup

The backend includes a setup script that recreates the PostgreSQL database,
creates all tables from the SQLModel metadata, and loads the initial data from
`backend/app/domains/system/data`.

## Run

From the `backend` directory:

```bash
./.venv/bin/python scripts/setup_database.py
```

You can also use `python scripts/setup_database.py` if your active environment
already points to the project Python.

From the repository root:

```bash
backend/.venv/bin/python backend/scripts/setup_database.py
```

The script reads `DATABASE_URL` from `.env`, for example:

```env
DATABASE_URL=postgresql+asyncpg://odoo:dexter@localhost:5432/backend
```

## Existing Database

If the target database already exists, the script asks for confirmation:

```text
The database 'backend' already exists. Delete it and continue? [y/N]:
```

Accepted affirmative answers are `y`, `yes`, `s`, `si`, and `sí`.

If the answer is not affirmative, the setup stops and the existing database is
not changed.

## What The Script Does

1. Connects to PostgreSQL using the server and credentials from `DATABASE_URL`.
2. Checks whether the target database exists.
3. Drops the target database only after confirmation.
4. Creates the target database.
5. Enables `pgcrypto` for `gen_random_uuid()`.
6. Creates all backend tables from the SQLModel metadata.
7. Loads the initial data from `backend/app/domains/system/data`.
8. Applies the search index migrations: stamps Alembic at the revision right
   before the pg_trgm/full-text search migrations
   (`f2a6c8d9b4e0`, `add the virtual insight model`), then runs
   `alembic upgrade head`. Those migrations only run raw SQL (`CREATE
   EXTENSION`, `CREATE INDEX ... USING gin`) that `SQLModel.metadata.create_all`
   cannot produce, since it isn't backed by any model or table column. Every
   earlier migration is treated as already applied because `create_all` and
   the data seed already reproduce their effect — the schema from current
   models and the data from the JSON files in
   `backend/app/domains/system/data`.

## Load Order

The setup starts with `user.user` by creating the internal `App Bot` record from
`user_users.json`.

`App Bot` is only used for system audit fields. It is created as inactive, uses
an internal placeholder email, and receives a random Argon2-hashed password that
is never printed or stored in plain text, so it cannot be used to sign in.

After `App Bot` exists, the script loads:

1. `system_lang.json`
2. the remaining records from `user_users.json`
3. `system_currency.json`
4. `system_country.json`
5. `system_models.json`
6. `system_model_schemas.json`

`system_model_fields.json` is currently empty because fields are embedded in
`system_models.json`.

Each record in `system_model_schemas.json` must define its declarative layout in
the `view` field. The setup stores that value in `SystemModelSchema.view`; the
`systemModelView` GraphQL query exposes it as `model.schema` in the response.

Human/system users loaded after `App Bot` use passwords from `user_users.json`.
Those passwords are hashed with the same Argon2 helper used by the backend
authentication flow (`AuthService.hash_password`) before they are inserted.

## Default Admin User

The initial seed creates a default development administrator:

```json
{
  "email": "admin@app.com",
  "password": "changeMe123"
}
```

Use this account only for local setup and change the password before using a
shared or production database.

## Audit Fields

For records that inherit from `SystemAudit`, the setup writes:

- `created_at`: current UTC date and time at setup execution
- `updated_at`: current UTC date and time at setup execution
- `create_by`: the `id` of `App Bot`
- `updated_by`: the `id` of `App Bot`

`App Bot` is created first and then updated to reference itself in its audit
fields.
