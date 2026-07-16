"""add FTS GIN indexes for searchable text fields

Revision ID: 86c64ea5062c
Revises: 0b189788379d
"""

from alembic import op

from app.domains.system.search.indexes import FTS_INDEXES, create_index_statement

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
def upgrade():
    for index in FTS_INDEXES:
        op.execute(create_index_statement(index))


def downgrade():
    for index in reversed(FTS_INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {index.name}")
