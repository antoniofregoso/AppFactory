# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - 2026-10-04

### Added

- Schema-driven Kanban, list, form, calendar, and insights views.
- Secure access and refresh-token sessions with rotation and reuse detection.
- Declarative global search with validated AI interpretation and text fallback.
- Reusable system, parties, and talent domain foundations.
- Authenticated attachment storage, notifications, MCP reports, and activity logs.
- Task due-date shortcuts and recurring task schedules.

### Fixed

- Made the task recurrence migration safe when upgrading databases that already contain the recurrence column.
- Preserved authorization isolation in generic system-model record creation tests.

### Security

- Updated audited production dependencies to remove known high-severity advisories.
