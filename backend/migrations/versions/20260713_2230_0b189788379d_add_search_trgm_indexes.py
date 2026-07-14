"""add pg_trgm GIN indexes for searchable text fields

Revision ID: 0b189788379d
Revises: f2a6c8d9b4e0
"""

from alembic import op

revision = "0b189788379d"
down_revision = "f2a6c8d9b4e0"
branch_labels = None
depends_on = None

# The compiler ORs an ILIKE predicate across every `search.text: true` field of a
# model (see `SearchQueryCompiler.compile`), so every one of those fields needs a
# matching index or PostgreSQL falls back to a sequential scan for the whole OR.
# JSONB (localized) expressions must match — including the explicit VARCHAR casts —
# argument-for-argument what SQLAlchemy's `.as_string()` compiles to (see
# `app.domains.system.search.compiler._localized_column`), because PostgreSQL only
# matches an expression index to a query by exact parse-tree equality: a query cast
# not mirrored in the index definition is enough to make the planner ignore it.
_INDEXES = [
    (
        "ix_system_tasks_title_trgm_es",
        "system_tasks",
        "COALESCE(CAST(title ->> 'es_MX' AS VARCHAR), CAST(title ->> 'es' AS VARCHAR),"
        " CAST(title ->> 'en_US' AS VARCHAR), CAST(title ->> 'en' AS VARCHAR))",
    ),
    (
        "ix_system_tasks_title_trgm_en",
        "system_tasks",
        "COALESCE(CAST(title ->> 'en_US' AS VARCHAR), CAST(title ->> 'en' AS VARCHAR),"
        " CAST(title ->> 'es_MX' AS VARCHAR), CAST(title ->> 'es' AS VARCHAR))",
    ),
    ("ix_system_tasks_status_trgm", "system_tasks", "status"),
    ("ix_system_tasks_priority_trgm", "system_tasks", "priority"),
    (
        "ix_system_messages_subject_trgm_es",
        "system_messages",
        "COALESCE(CAST(subject ->> 'es_MX' AS VARCHAR), CAST(subject ->> 'es' AS VARCHAR),"
        " CAST(subject ->> 'en_US' AS VARCHAR), CAST(subject ->> 'en' AS VARCHAR))",
    ),
    (
        "ix_system_messages_subject_trgm_en",
        "system_messages",
        "COALESCE(CAST(subject ->> 'en_US' AS VARCHAR), CAST(subject ->> 'en' AS VARCHAR),"
        " CAST(subject ->> 'es_MX' AS VARCHAR), CAST(subject ->> 'es' AS VARCHAR))",
    ),
    ("ix_system_messages_status_trgm", "system_messages", "status"),
]


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    for name, table, expression in _INDEXES:
        op.execute(
            f"CREATE INDEX {name} ON {table} USING gin (({expression}) gin_trgm_ops)"
        )


def downgrade():
    for name, _table, _expression in reversed(_INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {name}")
