"""PostgreSQL indexes required by the structured-search compiler.

This module is the single source of truth shared by Alembic upgrades and the
zero-database setup. Expression text must remain identical to the expressions
compiled in ``compiler.py`` so PostgreSQL can select these indexes.
"""

from typing import NamedTuple


class SearchIndex(NamedTuple):
    name: str
    table: str
    expression: str
    operator_class: str | None = None


TRIGRAM_INDEXES = (
    SearchIndex(
        "ix_system_tasks_title_trgm_es",
        "system_tasks",
        "COALESCE(CAST(title ->> 'es_MX' AS VARCHAR), CAST(title ->> 'es' AS VARCHAR),"
        " CAST(title ->> 'en_US' AS VARCHAR), CAST(title ->> 'en' AS VARCHAR))",
        "gin_trgm_ops",
    ),
    SearchIndex(
        "ix_system_tasks_title_trgm_en",
        "system_tasks",
        "COALESCE(CAST(title ->> 'en_US' AS VARCHAR), CAST(title ->> 'en' AS VARCHAR),"
        " CAST(title ->> 'es_MX' AS VARCHAR), CAST(title ->> 'es' AS VARCHAR))",
        "gin_trgm_ops",
    ),
    SearchIndex(
        "ix_system_tasks_status_trgm",
        "system_tasks",
        "status",
        "gin_trgm_ops",
    ),
    SearchIndex(
        "ix_system_tasks_priority_trgm",
        "system_tasks",
        "priority",
        "gin_trgm_ops",
    ),
    SearchIndex(
        "ix_system_messages_subject_trgm_es",
        "system_messages",
        "COALESCE(CAST(subject ->> 'es_MX' AS VARCHAR), CAST(subject ->> 'es' AS VARCHAR),"
        " CAST(subject ->> 'en_US' AS VARCHAR), CAST(subject ->> 'en' AS VARCHAR))",
        "gin_trgm_ops",
    ),
    SearchIndex(
        "ix_system_messages_subject_trgm_en",
        "system_messages",
        "COALESCE(CAST(subject ->> 'en_US' AS VARCHAR), CAST(subject ->> 'en' AS VARCHAR),"
        " CAST(subject ->> 'es_MX' AS VARCHAR), CAST(subject ->> 'es' AS VARCHAR))",
        "gin_trgm_ops",
    ),
    SearchIndex(
        "ix_system_messages_status_trgm",
        "system_messages",
        "status",
        "gin_trgm_ops",
    ),
)

FTS_INDEXES = (
    SearchIndex(
        "ix_system_tasks_title_fts",
        "system_tasks",
        "setweight(to_tsvector('simple', COALESCE(CAST(title ->> 'es_MX' AS VARCHAR), '')"
        " || ' ' || COALESCE(CAST(title ->> 'en_US' AS VARCHAR), '')), 'A')",
    ),
    SearchIndex(
        "ix_system_tasks_status_fts",
        "system_tasks",
        "setweight(to_tsvector('simple', COALESCE(status, '')), 'B')",
    ),
    SearchIndex(
        "ix_system_tasks_priority_fts",
        "system_tasks",
        "setweight(to_tsvector('simple', COALESCE(priority, '')), 'B')",
    ),
    SearchIndex(
        "ix_system_messages_subject_fts",
        "system_messages",
        "setweight(to_tsvector('simple', COALESCE(CAST(subject ->> 'es_MX' AS VARCHAR), '')"
        " || ' ' || COALESCE(CAST(subject ->> 'en_US' AS VARCHAR), '')), 'A')",
    ),
    SearchIndex(
        "ix_system_messages_status_fts",
        "system_messages",
        "setweight(to_tsvector('simple', COALESCE(status, '')), 'B')",
    ),
)

HTML_FTS_INDEXES = (
    SearchIndex(
        "ix_system_tasks_description_fts",
        "system_tasks",
        "setweight(to_tsvector('simple', regexp_replace("
        "COALESCE(CAST(description ->> 'es_MX' AS VARCHAR), '') || ' ' ||"
        " COALESCE(CAST(description ->> 'en_US' AS VARCHAR), ''),"
        " '<[^>]*>', ' ', 'g')), 'C')",
    ),
    SearchIndex(
        "ix_system_messages_message_fts",
        "system_messages",
        "setweight(to_tsvector('simple', regexp_replace("
        "COALESCE(CAST(message ->> 'es_MX' AS VARCHAR), '') || ' ' ||"
        " COALESCE(CAST(message ->> 'en_US' AS VARCHAR), ''),"
        " '<[^>]*>', ' ', 'g')), 'C')",
    ),
)

SEARCH_INDEXES = TRIGRAM_INDEXES + FTS_INDEXES + HTML_FTS_INDEXES


def create_index_statement(index: SearchIndex, *, if_not_exists: bool = False) -> str:
    guard = " IF NOT EXISTS" if if_not_exists else ""
    operator_class = f" {index.operator_class}" if index.operator_class else ""
    return (
        f"CREATE INDEX{guard} {index.name} ON {index.table} "
        f"USING gin (({index.expression}){operator_class})"
    )
