from types import SimpleNamespace

import pytest

from app.domains.system.graphql import queries as queries_module
from app.domains.system.graphql.queries import SystemQuery
from app.domains.system.graphql.types import (
    SystemSearchErrorCode,
    SystemSearchInput,
    SystemSearchStatus,
)
from app.domains.system.service.system_search_audit_service import (
    SystemSearchAuditService,
)
from app.domains.system.service.system_search_service import (
    SearchExecution,
    SearchResult,
    SearchResults,
    SystemSearchService,
)


async def current_user(info):
    return SimpleNamespace(id=7)


@pytest.fixture(autouse=True)
def disable_search_audit_persistence(monkeypatch):
    async def record(**kwargs):
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(SystemSearchAuditService, "record", record)


@pytest.mark.asyncio
async def test_system_search_returns_typed_success_response(monkeypatch):
    async def run(query, current_user_id, **kwargs):
        results = SearchResults(
            [
                SearchResult(
                    model="system.task",
                    model_label="Tareas",
                    uuid="task-1",
                    title="Preparar reporte",
                    subtitle="Urgent",
                    snippet=None,
                    url="/dashboard/user/system.task/task-1",
                    score=100,
                )
            ],
            queried_models=["system.task"],
        )
        return SearchExecution("OK", query, False, None, results)

    monkeypatch.setattr(queries_module, "get_current_user", current_user)
    monkeypatch.setattr(SystemSearchService, "run", run)

    response = await SystemQuery().system_search(
        SystemSearchInput(query="reporte", lang="es", limit=20),
        SimpleNamespace(context={}),
    )

    assert response.status is SystemSearchStatus.OK
    assert response.request_id is not None
    assert response.needs_clarification is False
    assert response.clarification_question is None
    assert response.errors == []
    assert response.results[0].uuid == "task-1"


@pytest.mark.asyncio
async def test_system_search_returns_typed_timeout_without_graphql_error(monkeypatch):
    async def run(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr(queries_module, "get_current_user", current_user)
    monkeypatch.setattr(SystemSearchService, "run", run)

    response = await SystemQuery().system_search(
        SystemSearchInput(query="reporte", lang="es"),
        SimpleNamespace(context={}),
    )

    assert response.status is SystemSearchStatus.FAILED
    assert response.results == []
    assert response.errors[0].code is SystemSearchErrorCode.TIMEOUT


@pytest.mark.asyncio
async def test_system_search_does_not_expose_internal_exception_details(monkeypatch):
    async def run(*args, **kwargs):
        raise RuntimeError("database password was secret-value")

    monkeypatch.setattr(queries_module, "get_current_user", current_user)
    monkeypatch.setattr(SystemSearchService, "run", run)

    response = await SystemQuery().system_search(
        SystemSearchInput(query="reporte", lang="en"),
        SimpleNamespace(context={}),
    )

    assert response.status is SystemSearchStatus.FAILED
    assert response.errors[0].code is SystemSearchErrorCode.INTERNAL_ERROR
    assert "secret-value" not in response.errors[0].message


@pytest.mark.asyncio
async def test_system_search_audits_typed_outcome_without_changing_response(
    monkeypatch,
):
    captured = {}

    async def run(*args, **kwargs):
        raise TimeoutError

    async def record(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(queries_module, "get_current_user", current_user)
    monkeypatch.setattr(SystemSearchService, "run", run)
    monkeypatch.setattr(SystemSearchAuditService, "record", record)

    response = await SystemQuery().system_search(
        SystemSearchInput(query="reporte confidencial", lang="es"),
        SimpleNamespace(context={}),
    )

    assert response.status is SystemSearchStatus.FAILED
    assert captured["request_id"] == response.request_id
    assert captured["user_id"] == 7
    assert captured["status"] == "FAILED"
    assert captured["result_count"] == 0
    assert captured["error_codes"] == ["TIMEOUT"]


@pytest.mark.asyncio
async def test_system_search_still_returns_results_when_audit_fails(monkeypatch):
    async def run(query, *args, **kwargs):
        return SearchExecution(
            "OK", query, False, None, SearchResults([], queried_models=[])
        )

    async def record(**kwargs):
        raise RuntimeError("audit database unavailable")

    monkeypatch.setattr(queries_module, "get_current_user", current_user)
    monkeypatch.setattr(SystemSearchService, "run", run)
    monkeypatch.setattr(SystemSearchAuditService, "record", record)

    response = await SystemQuery().system_search(
        SystemSearchInput(query="reporte", lang="es"),
        SimpleNamespace(context={}),
    )

    assert response.status is SystemSearchStatus.OK
    assert response.results == []
