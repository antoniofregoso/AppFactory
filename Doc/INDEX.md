# WebApp Documentation

Welcome to the WebApp documentation. This project uses declarative model and
view definitions to generate reusable business applications, operational
screens, dashboards, and reports.

## Start here

| Guide                                                 | Purpose                                    |
| ----------------------------------------------------- | ------------------------------------------ |
| [Project README](../README.md)                        | Overview, architecture, and quick start    |
| [Database setup](./DATABASE_SETUP.md)                 | Create a clean database and load seed data |
| [Backend](./BACKEND.md)                               | Run and extend the FastAPI application     |
| [Frontend](./FRONTEND.md)                             | Run and extend the Preact dashboard        |
| [Quality and testing](./QUALITY_AND_TESTING_GUIDE.md) | Test and code-quality workflows            |

## Declarative application model

The backend returns a single view payload containing model metadata, schema
configuration, and records. The frontend uses that payload to render the
selected view without model-specific page code.

| Reference                               | Covers                                   |
| --------------------------------------- | ---------------------------------------- |
| [Data format](./DATA_FORMAT.md)         | Model and record payloads                |
| [View format](./VIEWS_FORMAT.md)        | Kanban, list, form, and calendar layouts |
| [Insights format](./INSIGHTS_FORMAT.md) | KPIs, gauges, and chart definitions      |
| [GraphQL queries](./GRAPHQL_QUERIES.md) | Queries and mutations                    |

### Canonical data files

| File                        | Responsibility                                                     |
| --------------------------- | ------------------------------------------------------------------ |
| `system_models.json`        | Model definitions, field types, validation, and read-only metadata |
| `system_model_schemas.json` | Placement and behavior of fields in each view                      |
| `user_users.json`           | Seed users for local development                                   |

These files are located in `backend/app/domains/system/data`.

## Platform features

- [Session renewal](./SESSION_RENEWAL.md)
- [Notifications and browser push](./NOTIFICATIONS.md)
- [Declarative global search](./AI_SEARCH_DESIGN.md)
- [MCP read-only reports](./MCP.md)
- [Structured error handling](./ERROR_HANDLING_GUIDE.md)

## Insight visualizations

- [Bar](./BAR.md)
- [Donut](./DONUT.md)
- [Heat map](./HEATMAP.md)
- [Line](./LINE.md)
- [Radar](./RADAR.md)
- [Sankey](./SANKEY.md)
- [Tree map](./TREEMAP.md)

## Conventions

- Documentation prose is written in English.
- User-facing values may include both `en_US` and `es_MX` translations.
- File paths are relative to the repository root unless stated otherwise.
- Commands assume Bash on Linux or macOS.
- Never use seed passwords or development secrets in production.

## Keeping documentation current

When changing a declarative field, update both sources when applicable:

1. `system_models.json` for the field definition and visualization type.
2. `system_model_schemas.json` for list, Kanban, form, and calendar placement.
3. The related migration when existing databases must receive the change.
4. The relevant reference guide and tests.
