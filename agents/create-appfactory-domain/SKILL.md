---
name: create-appfactory-domain
description: Create or extend complete AppFactory business domains using the repository's SQLModel, declarative model metadata, generic GraphQL CRUD, modular access control, search, sidebar, migrations, setup, and test infrastructure. Use when an AI agent must add a domain, model, menu section, role, permission, or any kanban/list/form/calendar view in this AppFactory repository; especially use for requests where forms or other declarative views must render correctly.
---

# Create AppFactory Domain

Build domains as first-class modules of this repository. Prefer the generic model/view infrastructure; add custom GraphQL or frontend components only when the requested behavior cannot be expressed declaratively.

## Required context

Read these references before editing:

1. Read [references/domain-architecture.md](references/domain-architecture.md) for module structure and registration points.
2. Read [references/views.md](references/views.md) completely for every task that creates or changes a model or view. Treat view design as required implementation work, not decoration.
3. Read [references/access-search-setup.md](references/access-search-setup.md) when the domain needs menus, roles, permissions, search, migrations, or fresh-database support. New domains normally need all of them.

Inspect the current repository after reading the references. Conventions may evolve; use the nearest working domain, normally `talent`, as evidence.

**Model naming**: a model has a capitalized conceptual name (`Domain.Model.Submodel`, e.g. `User.User`) used only in prose, and a logical name that is always **lowercase and dotted** (`domain.model.submodel`, e.g. `user.user`) used everywhere in code — `MODEL_CLASS_BY_NAME` keys, JSON `"model"` fields, permission codes, and every frontend call. Never write the capitalized form into code or JSON. See [references/domain-architecture.md](references/domain-architecture.md#model-naming) for the full table.

## Workflow

### 1. Establish the domain contract

Create a compact matrix before coding:

| Model | Purpose | Company scoped | Relations | Default views | Search | Roles/actions |
|---|---|---|---|---|---|---|

Resolve ambiguous names, ownership, lifecycle, deletion behavior, and role boundaries from repository context. Ask only when a choice materially changes business behavior.

### 2. Design views before finalizing fields

For every visible model, decide what users must see in kanban, list, form, and calendar where applicable. Then design ORM fields and metadata to support those views.

Require all of the following:

- A renderable default form, even if the initial request mentions only another view.
- A meaningful kanban title; add subtitle/image/body only when useful.
- Unique, ordered list columns.
- Bilingual labels, placeholders, and helpers using `es_MX` and `en_US`.
- `html` for rich multilingual descriptions. Put the description in `form.tab: 0`, the first form tab.
- Correct relation widgets and related model names.
- Calendar title/start/end markers when a calendar is requested.

Follow [references/views.md](references/views.md) exactly.

### 3. Implement the persistence model

Create `backend/app/domains/<domain>/models/` using `SQLModel` and `SystemAudit` for audited records. Include UUID defaults, foreign keys, bidirectional relationships where useful, indexes, unique constraints, checks, enums, company ownership, and safe defaults.

Keep ORM names, metadata names, relation attributes, and schema field names aligned. A `many2one` field normally uses the database FK name such as `area_id`, while the ORM relationship is `area`.

### 4. Register generic CRUD

Register every visible ORM class in `MODEL_CLASS_BY_NAME`. Add company scoping and access enforcement at the generic service layer. Update relation mappings and writable many-to-many declarations when required.

Use custom repository/service/GraphQL modules only for behavior beyond the generic `systemModelView`, create, update, and delete flow. If custom GraphQL exists, enforce the same action permissions there so it cannot bypass generic CRUD security.

### 5. Declare model and view data

Create:

```text
backend/app/domains/<domain>/data/
├── system_models.json
├── system_model_schemas.json
└── access_control.json
```

Keep field helpers in `system_models.json` identical to `form.help` in the view schema. Declare one `default`/`view` schema for every visible model. Do not rely on implicit frontend fallbacks to make an incomplete schema appear usable.

### 6. Add access and navigation

Define exact CRUD permissions for restricted roles and `<domain>.*` for a full manager role. Leave `assignments` empty unless the user explicitly requests bootstrap assignments.

Add sidebar items with `.read` permissions. Update backend and frontend controlled-model registries so menus, buttons, direct URLs, generic mutations, and custom GraphQL enforce the same policy.

### 7. Integrate fresh setup and migrations

Import models before `SQLModel.metadata.create_all`, register the domain's data source in `setup_database.py`, and seed its metadata/schemas. Add an Alembic migration for existing databases. Make the migration idempotent where practical and preserve historical migrations.

If search is enabled, add secure search registration, authorization policy, URL builder, and matching PostgreSQL indexes when the compiler requires them.

### 8. Add tests with the domain

At minimum test:

- Every ORM model is registered for generic CRUD.
- Metadata uses valid field types and describes every model.
- Every model has a `default` view.
- Schema fields exist in model metadata or are approved virtual fields.
- List columns do not collide.
- Every form has a title and visible content.
- Rich descriptions use `html` and `tab: 0`.
- Helpers match between metadata and form schemas.
- Calendar markers are complete.
- Access roles contain the intended actions and no unintended delete permission.
- Roles are unassigned by default.
- Sidebar visibility and action buttons follow permissions.
- Company scoping and direct API authorization are enforced.

Run the bundled audit before tests:

```bash
python3 agents/create-appfactory-domain/scripts/audit_domain.py \
  backend/app/domains/<domain>
```

Then run focused backend and frontend tests. Run broader suites in proportion to the integration risk.

## Guardrails

- Do not reset or drop the database unless the user explicitly authorizes it.
- Do not edit generated database state instead of source JSON/migrations.
- Do not expose a menu without backend authorization.
- Do not protect only the menu; secure direct API access too.
- Do not invent unsupported field or layout types.
- Do not create a custom view component when the declarative schema supports the requirement.
- Do not omit forms. A model is incomplete until its form renders useful fields.
- Do not make company-scoped records writable across companies.
- Preserve unrelated changes in a dirty worktree.

## Completion standard

Finish only when a fresh database setup can discover the domain, an existing database can migrate, authorized users see the correct menu and actions, unauthorized direct calls fail, every declared view renders meaningful data, and focused tests plus `audit_domain.py` pass.
