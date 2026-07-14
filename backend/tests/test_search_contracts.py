import pytest
from pydantic import ValidationError

from app.domains.system.search.contracts import (
    FilterGroup,
    ModelSearchQuery,
    SearchFilter,
    SearchPlanV1,
)


def valid_plan(**overrides):
    data = {
        "version": 1,
        "intent": "search_records",
        "queries": [{"model": "system.task"}],
        "needs_clarification": False,
        "clarification_question": None,
    }
    data.update(overrides)
    return data


def test_search_plan_accepts_contract_example_and_assigns_defaults():
    plan = SearchPlanV1.model_validate(
        valid_plan(
            queries=[
                {
                    "model": "system.task",
                    "filters": {
                        "and": [
                            {"field": "priority", "operator": "eq", "value": "Urgent"},
                            {
                                "field": "user_id.name",
                                "operator": "contains",
                                "value": "Antonio",
                            },
                            {
                                "field": "date_due",
                                "operator": "this_week",
                                "value": None,
                            },
                        ]
                    },
                    "order": [{"field": "date_due", "direction": "asc"}],
                    "limit": 20,
                }
            ]
        )
    )

    assert plan.queries[0].limit == 20
    assert plan.queries[0].filters.and_filters is not None
    assert plan.model_dump(by_alias=True)["queries"][0]["filters"]["and"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"field": "name", "operator": "eq", "value": None}, "non-null scalar"),
        ({"field": "name", "operator": "in", "value": []}, "between 1 and 20"),
        (
            {"field": "name", "operator": "in", "value": ["a", "a"]},
            "unique values",
        ),
        (
            {"field": "amount", "operator": "between", "value": [2, 1]},
            "must not be greater",
        ),
        (
            {"field": "date_due", "operator": "today", "value": "today"},
            "requires a null",
        ),
        (
            {"field": "name", "operator": "contains", "value": "x" * 501},
            "must not exceed 500",
        ),
    ],
)
def test_search_filter_rejects_invalid_value_shapes(payload, message):
    with pytest.raises(ValidationError, match=message):
        SearchFilter.model_validate(payload)


def test_filter_group_allows_only_one_flat_logical_operator():
    search_filter = {"field": "name", "operator": "contains", "value": "report"}

    assert len(FilterGroup.model_validate({"or": [search_filter]}).or_filters) == 1
    with pytest.raises(ValidationError, match="exactly one"):
        FilterGroup.model_validate({"and": [], "or": []})
    with pytest.raises(ValidationError):
        FilterGroup.model_validate({"and": [{"and": [search_filter]}]})


def test_query_enforces_filter_order_and_result_limits():
    search_filter = {"field": "name", "operator": "eq", "value": "report"}
    order = {"field": "name", "direction": "asc"}

    with pytest.raises(ValidationError):
        ModelSearchQuery.model_validate(
            {"model": "system.task", "filters": {"and": [search_filter] * 11}}
        )
    with pytest.raises(ValidationError):
        ModelSearchQuery.model_validate({"model": "system.task", "order": [order] * 4})
    with pytest.raises(ValidationError):
        ModelSearchQuery.model_validate({"model": "system.task", "limit": 21})


def test_plan_requires_consistent_clarification_state():
    clarification = SearchPlanV1.model_validate(
        valid_plan(
            queries=[],
            needs_clarification=True,
            clarification_question="Which task model do you mean?",
        )
    )
    assert clarification.queries == []

    with pytest.raises(ValidationError, match="must not contain queries"):
        SearchPlanV1.model_validate(
            valid_plan(
                needs_clarification=True,
                clarification_question="Which task?",
            )
        )
    with pytest.raises(ValidationError, match="between 1 and 5"):
        SearchPlanV1.model_validate(valid_plan(queries=[]))


def test_contract_models_forbid_extra_fields_at_every_level():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SearchPlanV1.model_validate(valid_plan(debug=True))
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SearchPlanV1.model_validate(
            valid_plan(queries=[{"model": "system.task", "sql": "SELECT 1"}])
        )


def test_top_level_contract_fields_are_required():
    for field in (
        "version",
        "intent",
        "queries",
        "needs_clarification",
        "clarification_question",
    ):
        payload = valid_plan()
        del payload[field]
        with pytest.raises(ValidationError):
            SearchPlanV1.model_validate(payload)
