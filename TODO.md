# Tareas pendientes

## 🔴 Urgente — Migración gradual del frontend a Preact

- [x] Instalar y configurar Preact con Vite y JSX.
- [x] Conservar los schemas GraphQL/JSON como fuente para generar las vistas dinámicas.
- [x] Migrar primero Home y Login sin interrumpir las rutas actuales.
- [x] Migrar Topbar y Sidebar con manejo automático del ciclo de vida.
- [x] Migrar el panel de notas, mensajes y documentos, eliminando inserciones inseguras con `innerHTML`.
- [x] Convertir cada tipo de campo del schema en un componente reutilizable.
- [x] Migrar gradualmente Kanban, Lista, Formulario y Calendario.
- [x] Cargar Quill y las librerías de gráficas mediante `import()` solo cuando se necesiten.
- [x] Mantener pruebas y build funcionales después de cada etapa; evitar una reescritura completa.

## Renovación de sesión

- [x] Reducir la duración del access token a 15 minutos.
- [x] Agregar configuración para la duración del refresh token.
- [x] Generar access token y refresh token durante el login.
- [x] Crear una mutación GraphQL para renovar la sesión.
- [x] Guardar únicamente el hash del refresh token en PostgreSQL.
- [x] Implementar rotación: invalidar el refresh token usado y emitir uno nuevo.
- [x] Permitir revocar sesiones al cerrar sesión, cambiar contraseña o deshabilitar un usuario.
- [x] Detectar la reutilización de refresh tokens y revocar la sesión afectada.
- [x] Definir una expiración absoluta para la sesión, además del tiempo de inactividad.

## Seguridad web

- [x] Entregar el refresh token mediante una cookie `HttpOnly`, `Secure` y `SameSite`.
- [x] Mantener el access token en memoria en el frontend.
- [x] Configurar correctamente CORS y protección CSRF para el flujo con cookies.
- [x] Agregar `issuer`, `audience`, `jti` y tipo de token a los JWT.
- [x] Solicitar contraseña o MFA nuevamente para operaciones críticas.

## Frontend

- [x] Solicitar automáticamente la renovación antes de expirar el access token o al recibir un `401`.
- [x] Evitar múltiples solicitudes de refresh simultáneas.
- [x] Repetir la petición original después de renovar el token.
- [x] Cerrar la sesión y redirigir al login si la renovación falla.

## Global declarative search

Approved design: [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md).

### First phase implemented

- [x] Add `SystemModel.search` and `SystemModelField.search_config` as persistent metadata.
- [x] Load declarative configuration from `system_models.json`.
- [x] Create and apply the Alembic search migration.
- [x] Implement global text search over enabled models and fields only.
- [x] Reuse the per-user record scope from existing views.
- [x] Expose the GraphQL `systemSearch` query.
- [x] Connect topbar search with loading, error, empty, and result states.
- [x] Add direct links from results to each record.
- [x] Initially enable tasks and messages.
- [x] Document the declarative format in `Doc/DATA_FORMAT.md`.

### Contract and security implemented

- [x] Create Pydantic `SearchPlanV1`, `ModelSearchQuery`, `FilterGroup`, `SearchFilter`, and `SearchOrder` models with extra fields forbidden.
- [x] Implement the secure `SEARCH_MODEL_REGISTRY` with ORM class, authorization policy, and URL builder.
- [x] Create `SearchAuthorizationPolicy` and equivalence tests between records visible in views and search.
- [x] Apply authorization to related models used in filters.
- [x] Validate models, fields, operators, relations, limits, and ordering before executing any plan.
- [x] Implement type-specific parameterized filters, including localized selections, relative dates, and relations.
- [x] Resolve dates with an IANA timezone and convert boundaries to UTC.
- [x] Add typed GraphQL responses and errors: `OK`, `PARTIAL`, `NEEDS_CLARIFICATION`, and `FAILED`.
- [x] Add limits for models, filters, relation depth, time, and result count.
- [x] Audit searches without retaining sensitive text by default.

### AI interpretation implemented

- [x] Define the provider-independent `SearchInterpreter` interface.
- [x] Generate `SearchableSchemaV1` using authorized models and fields only.
- [x] Implement a reference adapter configured through backend secrets.
- [x] Convert natural-language questions into `SearchPlanV1`; AI must never generate or execute SQL.
- [x] Validate every provider output locally before querying PostgreSQL.
- [x] Implement `AUTO`, `TEXT`, and `AI` modes with explicit AI-to-text fallback.
- [x] Implement stateless clarifications using the original question and the user's answer.
- [x] Add timeout, cancellation, and handling for unconfigured or unavailable providers.
- [x] Create Spanish and English evaluations for queries, dates, relations, ambiguity, and permissions.

### Performance and future work pending

- [x] Create a reproducible benchmark with 100,000 records per model and 10 concurrent clients. See `backend/scripts/benchmark_search.py` and [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md#benchmark-results-2026-07-13).
- [x] Fix `TEXT`/`AUTO` search (`SystemSearchService._search`) to filter in SQL via `SearchQueryCompiler` instead of loading the entire table through `get_view`. p95 at 100,000 records/model dropped from 11,073 ms (100% timeouts) to 3,635 ms. Still ~12x over the 300 ms SLO — now a real unindexed-`ILIKE` problem. See [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md#fix-route-text-search-through-searchquerycompiler-2026-07-13).
- [x] Add `pg_trgm` indexes on every `ILIKE`-searched text field (`system_tasks.title/status/priority`, `system_messages.subject/status`), not just title/subject — the compiler `OR`s across all of them. See migration `20260713_2230_0b189788379d_add_search_trgm_indexes.py` and [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md#pg_trgm-indexes-2026-07-13). p95 dropped from 3,635 ms to 841 ms; raw query cost for rare/no-match terms is now sub-millisecond.
- [x] Lighten the per-request catalog fetch (`SystemModelRepository.get_all_with_fields()` skips the unused `schemas` relation) and raise the DB connection pool (`DB_POOL_SIZE`/`DB_MAX_OVERFLOW`, default 20+20). p95 dropped from 841 ms to 719 ms. Running per-model queries concurrently via `asyncio.gather` was tried and reverted — it made p95 worse (1,458 ms) in this single-process benchmark, likely event-loop/GIL contention from doubling in-flight CPU-bound ORM work, not I/O wait. See [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md#reducing-per-request-overhead-2026-07-14).
- [x] Re-measured against a multi-worker deployment: added `run-http` to `backend/scripts/benchmark_search.py` (real `systemSearch` GraphQL requests over HTTP, not in-process) and ran it against `uvicorn main:app --workers 4`. p95 dropped from 719 ms (single-process) to ~217–330 ms across trials — confirms the remaining gap was single-process concurrency overhead, not query cost. Still borderline against the 300 ms SLO (one of three trials failed) on this 4-core dev machine; needs re-measuring on the actual deployment host's core count. See [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md#multi-worker-re-measurement-2026-07-14).
- [x] Implement PostgreSQL Full Text Search with `tsvector`, ranking, and GIN indexes. `SearchQueryCompiler`'s free-text predicate now matches via `tsvector`/`@@ plainto_tsquery`/`ts_rank` per field (one GIN index per field, migration `20260714_0836_86c64ea5062c_add_search_fts_indexes.py`) instead of `ILIKE` + `ORDER BY uuid LIMIT n`, fixing a real correctness bug (best matches beyond an arbitrary uuid-ordered slice were previously invisible). Rare/exact queries got faster (~150–230 ms p50); common-word queries (matching a large fraction of the table) got slower (p95 ~700–1,400 ms vs. ~220–550 ms before) because true top-K ranking must evaluate every match, not just the first 20 found — an accepted, documented trade-off, not a bug. See [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md#full-text-search-2026-07-14).
- [x] Create normalized, indexable text for HTML fields before allowing them in search. `system.task.description` and `system.message.message` (the only `html` fields on search-registered models) now participate in the free-text FTS predicate: markup is stripped via `regexp_replace('<[^>]*>', ' ', 'g')` both in the GIN index (migration `20260714_0909_5fb991178534_add_search_fts_html_indexes.py`) and when building displayed snippets, with no new stored column or write-path sync needed. Verified against 100,000 seeded rows: a word only present inside an HTML `description` is found via `Bitmap Index Scan`, with a clean tag-free snippet. See [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md#normalized-html-search-text-2026-07-14).
- [x] Decide whether the first version includes notes and attachment filenames. Decided: not in v1 — `system_notes`/`system_attachments` are polymorphic (attached to any record via `model_id`/`record_uuid`, not a fixed model), so they don't fit `SEARCH_MODEL_REGISTRY`'s one-policy-one-URL-per-model shape; would need new dynamic authorization dispatch for a benefit that isn't yet proven. See [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md#notes-and-attachment-search-deferred-2026-07-14).
- [x] Evaluate embeddings only if filters and full-text search cannot solve real conceptual queries. Decided: not justified yet — structured queries (e.g. "urgent tasks from Antonio") already go through `SearchPlanV1` filters, not free text; FTS/`pg_trgm` cover exact and prefix/substring text. The remaining gap (pure synonym/paraphrase matching with no lexical overlap) has no evidence of occurring in real use. See [Doc/AI_SEARCH_DESIGN.md](./Doc/AI_SEARCH_DESIGN.md#embeddings-evaluation-2026-07-14).

## Logs de actividad de usuario

- [x] Crear endpoint o mutación GraphQL de heartbeat/ping para el usuario autenticado.
- [x] En cada ping, buscar el `UserLog` abierto del usuario (`status = ONLINE`, sin `end_date`) y actualizar `last_seen_at` con la hora del servidor.
- [x] Hacer que el frontend envíe el ping cada 30-60 segundos mientras la sesión esté activa y la pestaña esté visible.
- [x] Crear una tarea programada que marque como `OFFLINE` los logs sin ping reciente, usando un timeout definido, por ejemplo 2-5 minutos.
- [x] Al cerrar automáticamente, usar `last_seen_at` como `end_date` para que `duration` no cuente tiempo inactivo.
- [x] Probar login, logout explícito, cierre de pestaña/navegador, suspensión de laptop y múltiples pestañas.

## Base de datos y pruebas

- [x] Crear el modelo y la migración para sesiones o refresh tokens.
- [x] Probar expiración, rotación, revocación y reutilización de tokens.
- [x] Probar múltiples dispositivos y sesiones concurrentes.
- [x] Probar cookies y flujo de renovación con configuración de producción bajo HTTPS.

## Archivos adjuntos

- [x] Implementar inicialmente un filestore local persistente para documentos e imágenes asociados a los registros.
- [x] Guardar en PostgreSQL únicamente los metadatos y la ruta relativa del archivo, nunca el contenido binario.
- [x] Mantener el acceso al almacenamiento detrás de una interfaz intercambiable para evitar acoplar el dominio al disco local.
- [ ] Antes de producción, migrar el filestore a un bucket privado de Cloudflare R2.
- [ ] En producción, subir y descargar mediante URLs firmadas de corta duración, conservando la validación de permisos en el backend.
- [ ] Preparar y verificar la migración de archivos locales a R2, incluyendo checksums, conteo de objetos y estrategia de respaldo/rollback.
