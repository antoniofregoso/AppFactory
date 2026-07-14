import asyncio

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.core.config.settings import settings
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.search.compiler import SearchQueryCompiler
from app.domains.system.search.contracts import SearchPlanV1
from app.domains.system.search.limits import DEFAULT_SEARCH_LIMITS
from app.domains.system.search.validator import SearchPlanValidator
from app.domains.system.service.system_search_service import SystemSearchService
from tests.test_search_plan_validator import models


def plan_with_limits(*limits):
    return SearchPlanV1.model_validate(
        {
            "version": 1,
            "intent": "search_records",
            "queries": [{"model": "system.task", "limit": limit} for limit in limits],
            "needs_clarification": False,
            "clarification_question": None,
        }
    )


def test_limits_are_centralized_and_allocate_global_budget_in_query_order():
    assert DEFAULT_SEARCH_LIMITS.max_models_per_plan == 5
    assert DEFAULT_SEARCH_LIMITS.max_filters_per_query == 10
    assert DEFAULT_SEARCH_LIMITS.max_relation_depth == 1
    assert DEFAULT_SEARCH_LIMITS.max_results_per_query == 20
    assert DEFAULT_SEARCH_LIMITS.max_results_total == 50
    assert DEFAULT_SEARCH_LIMITS.allocate_results([20, 20, 20, 20]) == (
        20,
        20,
        10,
        0,
    )

    with pytest.raises(ValidationError):
        plan_with_limits(20, 20, 20, 20, 20, 20)


def test_validator_and_compiler_apply_the_global_result_budget():
    validated = SearchPlanValidator.validate_with_models(
        plan_with_limits(20, 20, 20, 20),
        models(),
    )

    assert [query.result_limit for query in validated.queries] == [20, 20, 10, 0]
    compiled = SearchQueryCompiler.compile(validated.queries[-2], 7).compile(
        dialect=postgresql.dialect()
    )
    assert 10 in compiled.params.values()


@pytest.mark.asyncio
async def test_text_search_is_cancelled_when_execution_timeout_expires(monkeypatch):
    async def get_all():
        await asyncio.sleep(0.05)
        return []

    monkeypatch.setattr(SystemModelRepository, "get_all_with_fields", get_all)
    monkeypatch.setattr(settings, "SEARCH_TIMEOUT_SECONDS", 0.001)

    with pytest.raises(TimeoutError):
        await SystemSearchService.search("report", 7)
