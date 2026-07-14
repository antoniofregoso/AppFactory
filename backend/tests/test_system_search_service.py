from types import SimpleNamespace

import pytest
from sqlalchemy.dialects import postgresql

from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.search.repository import SearchQueryRepository
from app.domains.system.service.system_search_service import SystemSearchService


def field(name, result, weight="B", field_type=None):
    return SimpleNamespace(
        name=name,
        type=field_type,
        search_config={
            "enabled": True,
            "text": True,
            "result": result,
            "weight": weight,
        },
    )


@pytest.mark.asyncio
async def test_search_only_uses_enabled_models_and_user_scoped_views(monkeypatch):
    models = [
        SimpleNamespace(
            name="system.task",
            search=True,
            label={"es_MX": "Tareas"},
            fields=[field("title", "title", "A"), field("priority", "subtitle")],
        ),
        SimpleNamespace(
            name="system.company",
            search=False,
            label={"es_MX": "Empresas"},
            fields=[field("name", "title")],
        ),
    ]

    async def get_all():
        return models

    captured_statements = []

    async def execute(statement):
        captured_statements.append(statement)
        return [
            SimpleNamespace(
                uuid="task-1",
                title={"es_MX": "Preparar reporte urgente"},
                priority="Urgent",
            )
        ]

    monkeypatch.setattr(SystemModelRepository, "get_all_with_fields", get_all)
    monkeypatch.setattr(SearchQueryRepository, "execute", execute)

    results = await SystemSearchService.search("reporte urgente", 7, lang="es")

    assert [result.uuid for result in results] == ["task-1"]
    assert results[0].title == "Preparar reporte urgente"
    assert results[0].subtitle == "Urgent"
    assert results[0].url == "/dashboard/user/system.task/task-1"

    # Only the enabled model (system.task) is queried, and its authorization
    # policy (scoping to the requesting user) is baked into the compiled SQL.
    # (Not compiled with `literal_binds=True`: the FTS predicate's `'simple'`
    # regconfig argument has no literal renderer in this SQLAlchemy version —
    # bound params are asserted directly instead.)
    assert len(captured_statements) == 1
    compiled = captured_statements[0].compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert "system_tasks" in sql
    assert "user_id" in sql
    assert 7 in compiled.params.values()


@pytest.mark.asyncio
async def test_search_rejects_empty_queries(monkeypatch):
    async def fail_if_called():
        raise AssertionError("models must not be loaded")

    monkeypatch.setattr(SystemModelRepository, "get_all_with_fields", fail_if_called)
    assert await SystemSearchService.search("   ", 7) == []


@pytest.mark.asyncio
async def test_search_fails_closed_for_enabled_unregistered_models(monkeypatch):
    async def get_all():
        return [
            SimpleNamespace(
                name="system.company",
                search=True,
                label={"en_US": "Companies"},
                fields=[field("name", "title")],
            )
        ]

    monkeypatch.setattr(SystemModelRepository, "get_all_with_fields", get_all)

    with pytest.raises(ValueError, match="is not registered"):
        await SystemSearchService.search("Acme", 7)


def test_map_plan_records_strips_html_tags_from_snippet():
    model = SimpleNamespace(
        name="system.task",
        label={"es_MX": "Tareas"},
        fields=[
            field("title", "title", "A"),
            field("description", "snippet", "C", field_type="html"),
        ],
    )
    record = SimpleNamespace(
        uuid="task-1",
        title={"es_MX": "Renovar contrato"},
        description={
            "es_MX": "<p>Revisar <strong>cláusulas</strong> con el cliente</p>"
        },
    )

    mapped = SystemSearchService._map_plan_records([record], model, "es")

    assert mapped[0].snippet == "Revisar cláusulas con el cliente"
    assert "<" not in mapped[0].snippet
    assert mapped[0].title == "Renovar contrato"
