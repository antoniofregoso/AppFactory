# AppFactory domain architecture

## Contents

- Domain layout
- Generic CRUD path
- Persistence conventions
- Registration checklist
- When custom GraphQL is justified
- Existing reference implementations

## Domain layout

Use this structure when the domain has only generic CRUD:

```text
backend/app/domains/<domain>/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── <model>.py
└── data/
    ├── system_models.json
    ├── system_model_schemas.json
    └── access_control.json
```

Add `repository/`, `service/`, and `graphql/` only for domain-specific behavior that generic CRUD cannot provide.

## Generic CRUD path

The dashboard loads `systemModelView` data and uses the generic record mutations in:

- `backend/app/domains/system/repository/system_model_repository.py`
- `backend/app/domains/system/service/system_model_service.py`
- `backend/app/domains/system/graphql/queries.py`
- `backend/app/domains/system/graphql/mutations.py`
- `frontend/src/app/api/systemModel.js`

Every generic model must be present in `MODEL_CLASS_BY_NAME`. The service infers relations from SQLAlchemy mappings, serializes many-to-one records, hydrates relation options, enforces company ownership, and applies conventional `<model>.<action>` permissions to controlled models.

## Persistence conventions

- Inherit `SystemAudit, SQLModel, table=True` for audited business records.
- Use plural snake-case table names and dotted logical model names: `sales_orders` and `sales.order`.
- Include integer `id` primary key and generated/indexed/unique UUID.
- Use timezone-aware datetimes.
- Use PostgreSQL `JSONB` for `string_i18n`, `html`, and structured JSON.
- Back selection values with `str, Enum` or constrained strings.
- Add database constraints for invariants such as date ranges and company-level uniqueness.
- Index foreign keys used for joins or company scoping.
- Add `company_id` to tenant-owned roots and propagate/validate it in services.
- Define relationships with matching `back_populates` when navigation is bidirectional.
- Keep secrets out of generic serialization and forms.

## Registration checklist

Inspect and update all applicable locations:

1. Export ORM classes from `backend/app/domains/<domain>/models/__init__.py` and the domain package.
2. Import models during setup so `SQLModel.metadata.create_all` sees them.
3. Register logical names in `SystemModelRepository.MODEL_CLASS_BY_NAME`.
4. Extend `COMPANY_SCOPED_MODELS` for tenant-owned models.
5. Extend `ACCESS_CONTROLLED_MODELS` for RBAC-protected generic endpoints.
6. Extend writable many-to-many mappings only for explicitly editable relationships.
7. Add the data directory to `MODEL_DATA_SOURCES` and load both metadata and schemas in `seed_data()`.
8. Add sidebar entries and frontend controlled-model recognition.
9. Register searchable models and policies only when `search: true`.
10. Import custom query/mutation mixins into `main.py` only when custom GraphQL is necessary.
11. Add a migration for existing databases.
12. Add domain metadata, authorization, and rendering tests.

Search for the constants instead of relying on line numbers; this repository evolves.

## When custom GraphQL is justified

Use generic CRUD for standard create/read/update/delete, relation selection, company scoping, and declarative views.

Add custom GraphQL for operations such as transactions spanning models, external service calls, computed aggregates, workflow transitions, or strongly typed public APIs. When adding it:

- Reuse the same service/repository rules.
- Require `<domain>.<resource>.<action>` on every query and mutation.
- Re-check company ownership for records and related IDs.
- Validate relations before writes.
- Test that custom mutations cannot bypass delete/update restrictions.

## Existing reference implementations

- `talent`: complete multi-model domain, relations, custom GraphQL, company scoping, views, roles, and sidebar.
- `parties`: generic CRUD with tenant ownership and reference catalogs.
- `access`: singular legacy metadata filenames plus advanced form, calendar, selection, and many-to-many views. New domains should use plural filenames.
- `system.task` and `system.message`: declarative search and specialized behavior.
