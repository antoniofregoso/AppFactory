import asyncio

import pytest

from app.domains.system.search.contracts import SearchPlanV1
from app.domains.system.service import system_search_service as service_module
from app.domains.system.service.system_search_service import (
    SearchMode,
    SearchResults,
    SystemSearchService,
)
from tests.test_search_plan_validator import models


def make_plan(*, text=None, filters=None, clarification=None):
    return SearchPlanV1.model_validate(
        {
            "version": 1,
            "intent": "search_records",
            "queries": (
                []
                if clarification
                else [
                    {
                        "model": "system.task",
                        "text": text,
                        "filters": {"and": filters or []},
                        "order": [],
                        "limit": 20,
                    }
                ]
            ),
            "needs_clarification": bool(clarification),
            "clarification_question": clarification,
        }
    )


class FakeInterpreter:
    def __init__(self, plan):
        self.plan = plan
        self.calls = []

    async def interpret(self, query, schema, context):
        self.calls.append((query, schema, context))
        return self.plan


class SlowInterpreter:
    async def interpret(self, query, schema, context):
        await asyncio.sleep(1)
        return make_plan(text=query)


@pytest.mark.asyncio
async def test_auto_falls_back_to_text_when_ai_is_not_configured(monkeypatch):
    fallback = SearchResults([], queried_models=["system.task"])

    async def text_search(*args, **kwargs):
        return fallback

    monkeypatch.setattr(service_module, "get_search_interpreter", lambda: None)
    monkeypatch.setattr(SystemSearchService, "_search", text_search)

    result = await SystemSearchService._run(
        "reporte",
        7,
        lang="es",
        limit=20,
        mode=SearchMode.AUTO,
        model=None,
        original_query=None,
        clarification_answer=None,
        timezone_name="America/Mexico_City",
    )

    assert result.status == "PARTIAL"
    assert result.results is fallback
    assert result.errors[0].code == "AI_UNAVAILABLE"


@pytest.mark.asyncio
async def test_ai_mode_does_not_hide_provider_failure_with_text(monkeypatch):
    monkeypatch.setattr(service_module, "get_search_interpreter", lambda: None)

    result = await SystemSearchService._run(
        "report",
        7,
        lang="en",
        limit=20,
        mode=SearchMode.AI,
        model=None,
        original_query=None,
        clarification_answer=None,
        timezone_name="UTC",
    )

    assert result.status == "FAILED"
    assert result.results == []
    assert result.errors[0].code == "AI_UNAVAILABLE"


@pytest.mark.asyncio
async def test_ai_interpretation_timeout_is_typed_and_cancels_provider(monkeypatch):
    monkeypatch.setattr(
        service_module, "get_search_interpreter", lambda: SlowInterpreter()
    )
    monkeypatch.setattr(service_module.settings, "SEARCH_AI_TIMEOUT_SECONDS", 0.001)

    async def get_all():
        return models()

    monkeypatch.setattr(service_module.SystemModelRepository, "get_all_with_fields", get_all)

    result = await SystemSearchService._run(
        "report",
        7,
        lang="en",
        limit=20,
        mode=SearchMode.AI,
        model=None,
        original_query=None,
        clarification_answer=None,
        timezone_name="UTC",
    )

    assert result.status == "FAILED"
    assert result.errors[0].code == "TIMEOUT"


@pytest.mark.asyncio
async def test_clarification_is_stateless_and_does_not_query_database(monkeypatch):
    interpreter = FakeInterpreter(make_plan(clarification="¿Qué prioridad?"))
    monkeypatch.setattr(service_module, "get_search_interpreter", lambda: interpreter)

    async def get_all():
        return models()

    async def unexpected_execute(statement):
        raise AssertionError("clarification must not execute a query")

    monkeypatch.setattr(service_module.SystemModelRepository, "get_all_with_fields", get_all)
    monkeypatch.setattr(
        service_module.SearchQueryRepository, "execute", unexpected_execute
    )

    result = await SystemSearchService._run(
        "alta",
        7,
        lang="es",
        limit=20,
        mode=SearchMode.AI,
        model=None,
        original_query="buscar tareas",
        clarification_answer="alta",
        timezone_name="America/Mexico_City",
    )

    assert result.status == "NEEDS_CLARIFICATION"
    assert result.clarification_question == "¿Qué prioridad?"
    context = interpreter.calls[0][2]
    assert context.original_query == "buscar tareas"
    assert context.clarification_answer == "alta"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("language", "query", "plan"),
    [
        (
            "es",
            "tareas urgentes de esta semana",
            make_plan(
                filters=[
                    {"field": "priority", "operator": "eq", "value": "Urgente"},
                    {"field": "date_due", "operator": "this_week", "value": None},
                ]
            ),
        ),
        (
            "en",
            "tasks assigned to Antonio",
            make_plan(
                filters=[
                    {
                        "field": "user_id.name",
                        "operator": "contains",
                        "value": "Antonio",
                    },
                ]
            ),
        ),
    ],
)
async def test_bilingual_plans_are_validated_before_execution(
    monkeypatch, language, query, plan
):
    interpreter = FakeInterpreter(plan)
    monkeypatch.setattr(service_module, "get_search_interpreter", lambda: interpreter)

    async def get_all():
        return models()

    async def execute(statement):
        return []

    monkeypatch.setattr(service_module.SystemModelRepository, "get_all_with_fields", get_all)
    monkeypatch.setattr(service_module.SearchQueryRepository, "execute", execute)

    result = await SystemSearchService._run(
        query,
        7,
        lang=language,
        limit=20,
        mode=SearchMode.AI,
        model=None,
        original_query=None,
        clarification_answer=None,
        timezone_name="America/Mexico_City",
    )

    assert result.status == "OK"
    assert result.results.queried_models == ("system.task",)


@pytest.mark.asyncio
async def test_provider_cannot_query_a_model_outside_exposed_permissions(monkeypatch):
    unauthorized = SearchPlanV1.model_validate(
        {
            "version": 1,
            "intent": "search_records",
            "queries": [{"model": "user.user", "filters": {"and": []}}],
            "needs_clarification": False,
            "clarification_question": None,
        }
    )
    monkeypatch.setattr(
        service_module, "get_search_interpreter", lambda: FakeInterpreter(unauthorized)
    )

    async def get_all():
        return models()

    monkeypatch.setattr(service_module.SystemModelRepository, "get_all_with_fields", get_all)

    result = await SystemSearchService._run(
        "all users",
        7,
        lang="en",
        limit=20,
        mode=SearchMode.AI,
        model=None,
        original_query=None,
        clarification_answer=None,
        timezone_name="UTC",
    )

    assert result.status == "FAILED"
    assert result.errors[0].code == "INVALID_PLAN"
