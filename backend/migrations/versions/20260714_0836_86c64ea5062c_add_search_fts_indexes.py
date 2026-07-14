"""add FTS GIN indexes for searchable text fields

Revision ID: 86c64ea5062c
Revises: 0b189788379d
"""

from alembic import op

revision = "86c64ea5062c"
down_revision = "0b189788379d"
branch_labels = None
depends_on = None

# `SearchQueryCompiler` now matches the free-text `query.text` predicate with
# PostgreSQL Full Text Search instead of ILIKE (see `_fts_field_vector` in
# `app.domains.system.search.compiler`): every `search.text: true` field gets
# its own `'simple'`-config tsvector — both locales (`es_MX`/`en_US`) folded
# into one vector so a single index covers a field regardless of language —
# weighted by that field's `search_config["weight"]` (A/B/C/D, default D),
# and matched with `@@ plainto_tsquery('simple', ...)`, OR'd across a model's
# text fields exactly like the ILIKE predicate it replaces. Structured filter
# operators (`contains`/`starts_with`) are untouched and still use ILIKE
# against the existing `pg_trgm` indexes.
#
# As with `20260713_2230_0b189788379d_add_search_trgm_indexes.py`, the index
# expression below must match the compiler's expression *exactly*—
# PostgreSQL only matches an expression index to a query by exact parse-tree
# equality, including the `CAST(... AS VARCHAR)` that SQLAlchemy's
# `.as_string()` compiles to for JSONB fields, and the same weight label.
_INDEXES = [
    (
        "ix_system_tasks_title_fts",
        "system_tasks",
        "setweight(to_tsvector('simple', COALESCE(CAST(title ->> 'es_MX' AS VARCHAR), '')"
        " || ' ' || COALESCE(CAST(title ->> 'en_US' AS VARCHAR), '')), 'A')",
    ),
    (
        "ix_system_tasks_status_fts",
        "system_tasks",
        "setweight(to_tsvector('simple', COALESCE(status, '')), 'B')",
    ),
    (
        "ix_system_tasks_priority_fts",
        "system_tasks",
        "setweight(to_tsvector('simple', COALESCE(priority, '')), 'B')",
    ),
    (
        "ix_system_messages_subject_fts",
        "system_messages",
        "setweight(to_tsvector('simple', COALESCE(CAST(subject ->> 'es_MX' AS VARCHAR), '')"
        " || ' ' || COALESCE(CAST(subject ->> 'en_US' AS VARCHAR), '')), 'A')",
    ),
    (
        "ix_system_messages_status_fts",
        "system_messages",
        "setweight(to_tsvector('simple', COALESCE(status, '')), 'B')",
    ),
]


def upgrade():
    for name, table, expression in _INDEXES:
        op.execute(f"CREATE INDEX {name} ON {table} USING gin (({expression}))")


def downgrade():
    for name, _table, _expression in reversed(_INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {name}")
