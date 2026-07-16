from app.domains.system.search.indexes import (
    FTS_INDEXES,
    HTML_FTS_INDEXES,
    SEARCH_INDEXES,
    TRIGRAM_INDEXES,
    create_index_statement,
)


def test_zero_database_setup_declares_every_search_gin_index():
    assert len(TRIGRAM_INDEXES) == 7
    assert len(FTS_INDEXES) == 5
    assert len(HTML_FTS_INDEXES) == 2
    assert len(SEARCH_INDEXES) == 14
    assert len({index.name for index in SEARCH_INDEXES}) == len(SEARCH_INDEXES)

    statements = [
        create_index_statement(index, if_not_exists=True)
        for index in SEARCH_INDEXES
    ]
    assert all(statement.startswith("CREATE INDEX IF NOT EXISTS") for statement in statements)
    assert all("USING gin" in statement for statement in statements)
    assert all("gin_trgm_ops" in create_index_statement(index) for index in TRIGRAM_INDEXES)


def test_search_index_expressions_cover_locales_and_normalized_html():
    by_name = {index.name: index.expression for index in SEARCH_INDEXES}

    assert "'es_MX'" in by_name["ix_system_tasks_title_fts"]
    assert "'en_US'" in by_name["ix_system_tasks_title_fts"]
    assert "regexp_replace" in by_name["ix_system_tasks_description_fts"]
    assert "regexp_replace" in by_name["ix_system_messages_message_fts"]
