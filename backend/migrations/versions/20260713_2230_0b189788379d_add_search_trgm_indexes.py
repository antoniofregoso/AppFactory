"""add pg_trgm GIN indexes for searchable text fields

Revision ID: 0b189788379d
Revises: f2a6c8d9b4e0
"""

from alembic import op

from app.domains.system.search.indexes import TRIGRAM_INDEXES, create_index_statement

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
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    for index in TRIGRAM_INDEXES:
        op.execute(create_index_statement(index))


def downgrade():
    for index in reversed(TRIGRAM_INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {index.name}")
