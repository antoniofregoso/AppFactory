# Access, navigation, search, setup, and migrations

## Contents

- Modular access data
- Enforcement layers
- Sidebar and action visibility
- Fresh database setup
- Existing database migrations
- Declarative search
- Verification commands

## Modular access data

Place `access_control.json` in the domain's `data` directory:

```json
{
  "permissions": [
    {
      "code": "example.record.read",
      "name": {"es_MX": "Consultar registros", "en_US": "Read records"},
      "description": {"es_MX": "Permite consultar registros", "en_US": "Allows reading records"}
    },
    {
      "code": "example.*",
      "name": {"es_MX": "Administrar ejemplo", "en_US": "Manage example"},
      "description": {"es_MX": "Acceso total al dominio", "en_US": "Full domain access"}
    }
  ],
  "roles": [
    {
      "code": "example_user",
      "name": {"es_MX": "Usuario de ejemplo", "en_US": "Example user"},
      "description": {"es_MX": "Acceso operativo", "en_US": "Operational access"},
      "sequence": 20,
      "permissions": ["example.record.read"]
    },
    {
      "code": "example_manager",
      "name": {"es_MX": "Manager de ejemplo", "en_US": "Example manager"},
      "description": {"es_MX": "Acceso total", "en_US": "Full access"},
      "sequence": 21,
      "permissions": ["example.*"]
    }
  ],
  "assignments": []
}
```

Use `<model>.read|create|update|delete` for exact permissions. Wildcards ending in `.*` grant all nested actions. Do not give delete implicitly when the user says “crear y editar pero no borrar.”

The setup auto-discovers `domains/*/data/access_control.json`, validates duplicate codes and references, creates role templates, and creates only explicit assignments.

## Enforcement layers

Apply permission checks consistently:

1. Sidebar `.read` permission controls discovery.
2. Frontend action permissions control Create/Edit/Delete/reorder affordances.
3. Generic service checks protect direct GraphQL calls.
4. Custom GraphQL resolvers require the exact action.
5. Company scoping restricts records and related IDs.

Backend locations currently include `ACCESS_CONTROLLED_MODELS` and `_require_model_permission` in `system_model_service.py`. Frontend locations include `utils/accessControl.js` and sidebar permission matching. These registries are currently explicit; update them for a new domain.

Never treat a hidden menu or button as authorization.

## Sidebar and action visibility

Add a domain group to `frontend/src/app/data/sidebar.json`. Each leaf uses:

```json
{
  "key": "records",
  "labelEn": "Records",
  "labelEs": "Registros",
  "url": "/dashboard/example/example.record",
  "permission": "example.record.read"
}
```

Register a supported icon in `frontend/src/app/components/sidebar.jsx` if the group needs a new icon. Test exact grants and wildcard manager grants.

## Fresh database setup

`backend/scripts/setup_database.py` creates the latest schema from imported SQLModel metadata and then loads current JSON data. A new domain must be visible to both phases:

- Import its model package before `SQLModel.metadata.create_all`.
- Add its model/schema filenames to `MODEL_DATA_SOURCES`.
- Load its models and schemas in `seed_data()`.
- Keep access control in `access_control.json`; that portion is auto-discovered.
- Validate all source JSON before the destructive reset begins.

Run setup only with explicit user authorization because it drops the configured database.

## Existing database migrations

Create an Alembic migration for schema and seeded metadata changes. Follow the current head revision. Do not rewrite an applied historical migration.

### Required two-phase migration

For a new visible domain, use both phases:

1. A schema revision creates tables, columns, constraints, indexes, and foreign keys.
2. A following idempotent data revision reads the domain's committed JSON sources and upserts:
   - `system_models`;
   - `system_model_fields`;
   - `system_model_schemas`, including one `default`/`view` per visible model;
   - `access_permissions`;
   - company-neutral `access_roles` templates;
   - `access_role_permissions` links.

Do not stop after phase 1. Generic `systemModelView` resolves views from database metadata, not directly from JSON, so ORM tables can exist while every domain view returns missing/empty definitions.

Keep the fresh-setup migration checkpoint on the newest schema revision. The data revision must follow that checkpoint and be safe after JSON seeding. This prevents `create_all` from colliding with schema migrations while still exercising the same metadata upsert on fresh and existing databases.

For seeded data:

- Use stable logical keys such as model names, role codes, and permission codes.
- Upsert where reruns must be safe.
- Avoid assigning template roles to users.
- Make downgrade behavior conservative around shared permissions and historical data.

After `alembic upgrade head`, verify the database itself. For each expected logical model, require a row in `system_models`, at least one field, and exactly one usable default view schema. Verify permission and role codes separately. An Alembic head check only proves revisions ran; it does not prove view metadata was installed.

The fresh setup and migration must produce equivalent functional state.

## Declarative search

Set model `search: true` only when search is fully secured and registered. Configure each searchable field with explicit capabilities such as `enabled`, `text`, `filter`, `operators`, relation fields, and weight.

Then update:

- `backend/app/domains/system/search/registry.py` with ORM class, authorization policy, and dashboard URL.
- `authorization.py` with a policy equivalent to normal view visibility.
- PostgreSQL search index definitions when new compiler expressions require GIN/trigram/FTS indexes.
- Search tests for schema exposure, authorization equivalence, compiler SQL, and result URLs.

Startup intentionally fails when a searchable model lacks secure registration. Do not bypass this guard.

## Verification commands

Run from the repository root unless noted:

```bash
python3 agents/create-appfactory-domain/scripts/audit_domain.py backend/app/domains/<domain>
backend/.venv/bin/python -m compileall -q backend/app/domains/<domain>
backend/.venv/bin/pytest -q backend/tests/test_<domain>_data_metadata.py backend/tests/test_access_control_data.py
cd frontend && npm test -- --run tests/sidebar-permissions.test.jsx tests/access-control-permissions.test.js
```

Add domain-specific service, company-scope, GraphQL, and rendering tests. Use `git diff --check` before handoff.

When a disposable or explicitly authorized database is available, also run a metadata smoke check after migration. At minimum inspect:

```sql
SELECT m.name, count(DISTINCT f.id), count(DISTINCT s.id)
FROM system_models m
LEFT JOIN system_model_fields f ON f.model_id = m.id
LEFT JOIN system_model_schemas s ON s.model_id = m.id
WHERE m.name LIKE '<domain>.%'
GROUP BY m.name ORDER BY m.name;
```

Compare the returned model names with `system_models.json`; do not accept an empty or partial result.
