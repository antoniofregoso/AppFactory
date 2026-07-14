# Frontend Guide

The frontend is a Preact single-page application built with Vite. It renders
generic business views from the model payload returned by GraphQL.

## Technology stack

- Preact and JSX
- Signals for shared application state
- Tailwind CSS and project-level CSS variables
- Vite for development and production builds
- CJ Router for client-side navigation
- Vitest for component and utility tests
- ApexCharts and ApexSankey for insights

## Setup

From the `frontend` directory:

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`. The Vite configuration proxies `/graphql` and
`/api` requests to `http://localhost:8000`.

## Project structure

```text
frontend/
├── src/
│   ├── app/
│   │   ├── api/          # GraphQL and HTTP clients
│   │   ├── components/   # Shared UI and field components
│   │   ├── pages/        # Route-level orchestration
│   │   ├── store/        # Signals and state actions
│   │   ├── utils/        # Formatting, routing, and view helpers
│   │   └── views/        # Kanban, list, form, and calendar renderers
│   ├── i18n/             # Translation helpers
│   ├── App.js
│   ├── main.js
│   └── style.css
├── tests/
├── package.json
└── vite.config.js
```

## How declarative views work

The dashboard requests `systemModelView` with a model name, schema use, and
schema name. The response contains:

```json
{
  "model": {
    "name": "user.log",
    "readonly": true,
    "label": { "en": "User Logs", "es": "Registros de sesión" },
    "schema": []
  },
  "records": []
}
```

The selected renderer reads the same schema:

- `KanbanView.jsx` uses each field's `kanban` placement.
- `ListView.jsx` uses each field's `list` placement.
- `FormView.jsx` uses each field's `form` placement.
- `CalendarView.jsx` uses each field's `calendar` role.

Field visualization is delegated to reusable controls in
`src/app/components/fields`. For example, `many2one_avatar` renders a related
record's avatar and display name in both read-only lists and forms.

## Read-only models

When the model payload includes `"readonly": true`, the generic views hide
mutation controls:

- Create buttons
- Edit and save actions
- Delete and archive actions
- List and Kanban drag handles
- Editable communication controls

The backend must also enforce read-only access; hiding controls is not a
security boundary.

## Localization

Schema labels and values normally provide `en_US` and `es_MX`. The backend adds
the shorter `en` and `es` aliases to view payloads for frontend compatibility.

```json
{
  "label": {
    "en_US": "Assigned user",
    "es_MX": "Usuario asignado"
  }
}
```

Keep technical identifiers, field names, and API values language-independent.

## Testing

```bash
# Run tests once
npm test -- --run

# Watch changed tests
npm test

# Run selected test files
npm test -- --run tests/preact-views.test.jsx

# Open the Vitest UI
npm run test:ui

# Build for production
npm run build
```

Component tests use a browser-like DOM environment and should verify behavior,
not implementation details. For declarative views, test the schema and record
payload together so renderer regressions are caught.

## Adding a field visualization

1. Add or update the field type in `FieldControl.jsx`.
2. Implement the reusable field component.
3. Add field-level tests.
4. Document the type in [View Format](./VIEWS_FORMAT.md).
5. Use the type in `system_models.json` and place it in
   `system_model_schemas.json`.

## Production build

```bash
npm run build
```

Vite writes production assets to `frontend/dist`. Large chart dependencies are
split into separate chunks where possible; review build warnings when adding
new visualization libraries.
