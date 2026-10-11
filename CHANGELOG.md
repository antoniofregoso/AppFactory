# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - 2026-10-11

### Added

- Schema-driven Kanban, list, form, calendar, and insights views.
- Secure access and refresh-token sessions with rotation and reuse detection.
- Declarative global search with validated AI interpretation and text fallback.
- Reusable system, parties, and talent domain foundations.
- Authenticated attachment storage, notifications, MCP reports, and activity logs.
- Task due-date shortcuts and recurring task schedules.
- PostgreSQL backup and restore commands, documented in
  [Database setup](./Doc/DATABASE_SETUP.md), with timestamped custom-format
  archives and confirmation before replacing existing database objects.

### Fixed

- Made the task recurrence migration safe when upgrading databases that already contain the recurrence column.
- Preserved authorization isolation in generic system-model record creation tests.
- Made fresh setup build the current schema, seed data, and search indexes
  directly before stamping Alembic at `head`.
- Passed the target database explicitly to `pg_restore`, preventing restores
  from exiting before connecting.

### Security

- Updated audited production dependencies to remove known high-severity advisories.
