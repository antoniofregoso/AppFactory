"""add FTS GIN indexes for normalized HTML search fields

Revision ID: 5fb991178534
Revises: 24d8babba860
"""

from alembic import op

revision = "5fb991178534"
down_revision = "24d8babba860"
branch_labels = None
depends_on = None

# `type: html` fields (`system.task.description`, `system.message.message`)
# are now eligible for the free-text FTS predicate (see the `field_type ==
# "html"` branch in `_fts_source_text`, `app.domains.system.search.compiler`).
# Raw HTML markup would pollute matching/ranking with tag names and
# attributes, so the vector is built over `regexp_replace(html, '<[^>]*>',
# ' ', 'g')` instead of the raw column — a deliberately simple tag-stripper
# (no entity decoding, no <script>/<style> content removal), acceptable
# because this content comes from the app's allowlisted Quill editor, not
# arbitrary raw HTML. `regexp_replace` with a constant pattern/flags is
# PostgreSQL-IMMUTABLE, so it's safe inside a GIN expression index.
#
# As with the two prior search migrations, the index expression below must
# match the compiler's expression *exactly* — PostgreSQL only matches an
# expression index to a query by exact parse-tree equality.
_INDEXES = [
    (
        "ix_system_tasks_description_fts",
        "system_tasks",
        "setweight(to_tsvector('simple', regexp_replace("
        "COALESCE(CAST(description ->> 'es_MX' AS VARCHAR), '') || ' ' ||"
        " COALESCE(CAST(description ->> 'en_US' AS VARCHAR), ''),"
        " '<[^>]*>', ' ', 'g')), 'C')",
    ),
    (
        "ix_system_messages_message_fts",
        "system_messages",
        "setweight(to_tsvector('simple', regexp_replace("
        "COALESCE(CAST(message ->> 'es_MX' AS VARCHAR), '') || ' ' ||"
        " COALESCE(CAST(message ->> 'en_US' AS VARCHAR), ''),"
        " '<[^>]*>', ' ', 'g')), 'C')",
    ),
]


def upgrade():
    for name, table, expression in _INDEXES:
        op.execute(f"CREATE INDEX {name} ON {table} USING gin (({expression}))")


def downgrade():
    for name, _table, _expression in reversed(_INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {name}")
