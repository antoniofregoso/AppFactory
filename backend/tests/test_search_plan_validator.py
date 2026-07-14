from types import SimpleNamespace

import pytest

from app.domains.system.search.authorization import USER_AUTHORIZATION_POLICY
from app.domains.system.search.contracts import SearchPlanV1
from app.domains.system.search.validator import (
    SearchPlanValidationError,
    SearchPlanValidator,
)


def field(name, field_type, **search_config):
    return SimpleNamespace(
        name=name,
        type=field_type,
        search_config=search_config,
    )


def models():
    return [
        SimpleNamespace(
            name="system.task",
            search=True,
            fields=[
                field(
                    "title",
                    "string",
                    enabled=True,
                    text=True,
                    filter=True,
                    operators=["eq", "contains", "starts_with"],
                ),
                field(
                    "priority",
                    "selection",
                    enabled=True,
                    filter=True,
                    operators=["eq", "in"],
                    selection_values=[
                        {"value": "Low", "es_MX": "Baja", "en_US": "Low"},
                        {"value": "High", "es_MX": "Alta", "en_US": "High"},
                        {
                            "value": "Urgent",
                            "es_MX": "Urgente",
                            "en_US": "Urgent",
                        },
                    ],
                ),
                field(
                    "date_due",
                    "datetime",
                    enabled=True,
                    filter=True,
                    operators=["before", "between", "this_week"],
                ),
                field(
                    "user_id",
                    "many2one_avatar",
                    enabled=True,
                    filter=True,
                    operators=["eq", "in"],
                    relation_fields=["name", "email"],
                ),
                field("description", "html", enabled=True),
                field("password", "password", enabled=True, filter=True),
            ],
        ),
        SimpleNamespace(
            name="user.user",
            search=False,
            fields=[
                field(
                    "name",
                    "string",
                    enabled=True,
                    filter=True,
                    operators=["eq", "contains"],
                ),
                field("email", "string", enabled=False, filter=True),
                field("password", "password", enabled=True, filter=True),
            ],
        ),
    ]


def plan(filters=None, order=None, **query_overrides):
    query = {
        "model": "system.task",
        "filters": {"and": filters or []},
        "order": order or [],
    }
    query.update(query_overrides)
    return SearchPlanV1.model_validate(
        {
            "version": 1,
            "intent": "search_records",
            "queries": [query],
            "needs_clarification": False,
            "clarification_question": None,
        }
    )


def test_validator_resolves_authorized_related_fields_without_executing_queries():
    validated = SearchPlanValidator.validate_with_models(
        plan(
            filters=[
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
            ],
            order=[{"field": "date_due", "direction": "asc"}],
            text="urgent report",
        ),
        models(),
    )

    related = validated.queries[0].filters[0].resolved_field
    assert related.related_model_name == "user.user"
    assert (
        related.related_registration.authorization_policy is USER_AUTHORIZATION_POLICY
    )
    assert validated.queries[0].orders[0].resolved_field.field_type == "datetime"


@pytest.mark.parametrize(
    ("filters", "message"),
    [
        ([{"field": "missing", "operator": "eq", "value": "x"}], "does not exist"),
        (
            [{"field": "description", "operator": "contains", "value": "x"}],
            "not filterable",
        ),
        (
            [{"field": "priority", "operator": "contains", "value": "High"}],
            "not allowed",
        ),
        (
            [{"field": "user_id.email", "operator": "contains", "value": "a@b.com"}],
            "not filterable",
        ),
        (
            [{"field": "user_id.password", "operator": "eq", "value": "secret"}],
            "not explicitly allowed",
        ),
        (
            [{"field": "user_id.name.first", "operator": "eq", "value": "A"}],
            "maximum relation depth",
        ),
        (
            [{"field": "password", "operator": "eq", "value": "secret"}],
            "not filterable",
        ),
        (
            [{"field": "date_due", "operator": "before", "value": "2026-07-13"}],
            "incompatible",
        ),
    ],
)
def test_validator_rejects_invalid_fields_relations_operators_and_values(
    filters, message
):
    with pytest.raises(SearchPlanValidationError, match=message):
        SearchPlanValidator.validate_with_models(plan(filters=filters), models())


def test_validator_rejects_disabled_models_and_non_orderable_fields():
    disabled_models = models()
    disabled_models[0].search = False
    with pytest.raises(SearchPlanValidationError, match="not enabled"):
        SearchPlanValidator.validate_with_models(plan(), disabled_models)

    with pytest.raises(SearchPlanValidationError, match="cannot be used for ordering"):
        SearchPlanValidator.validate_with_models(
            plan(order=[{"field": "user_id", "direction": "asc"}]),
            models(),
        )

    with pytest.raises(SearchPlanValidationError, match="Related field"):
        SearchPlanValidator.validate_with_models(
            plan(order=[{"field": "user_id.name", "direction": "asc"}]),
            models(),
        )


def test_validator_compares_typed_between_boundaries():
    with pytest.raises(SearchPlanValidationError, match="start exceeds end"):
        SearchPlanValidator.validate_with_models(
            plan(
                filters=[
                    {
                        "field": "date_due",
                        "operator": "between",
                        "value": [
                            "2026-07-14T00:00:00-06:00",
                            "2026-07-13T00:00:00-06:00",
                        ],
                    }
                ]
            ),
            models(),
        )


def test_validator_resolves_localized_selection_labels_to_technical_values():
    validated = SearchPlanValidator.validate_with_models(
        plan(filters=[{"field": "priority", "operator": "eq", "value": "Urgente"}]),
        models(),
        language="es",
    )

    assert validated.queries[0].filters[0].value == "Urgent"


def test_validator_rejects_unknown_and_ambiguous_localized_selections():
    with pytest.raises(SearchPlanValidationError, match="is not valid"):
        SearchPlanValidator.validate_with_models(
            plan(
                filters=[{"field": "priority", "operator": "eq", "value": "Critical"}]
            ),
            models(),
        )

    metadata = models()
    priority = next(field for field in metadata[0].fields if field.name == "priority")
    priority.search_config["selection_values"].append(
        {"value": "Critical", "es_MX": "Urgente", "en_US": "Critical"}
    )
    with pytest.raises(SearchPlanValidationError, match="ambiguous"):
        SearchPlanValidator.validate_with_models(
            plan(filters=[{"field": "priority", "operator": "eq", "value": "Urgente"}]),
            metadata,
        )


def test_status_selection_uses_model_group_by_values():
    metadata = models()
    metadata[0].group_by = "status"
    metadata[0].group_by_values = [
        {"value": "Pending", "es_MX": "Pendiente", "en_US": "Pending"},
        {"value": "Completed", "es_MX": "Completada", "en_US": "Completed"},
    ]
    metadata[0].fields.append(
        field(
            "status",
            "status_badge",
            enabled=True,
            filter=True,
            operators=["eq", "in"],
        )
    )

    validated = SearchPlanValidator.validate_with_models(
        plan(filters=[{"field": "status", "operator": "eq", "value": "Pendiente"}]),
        metadata,
        language="es",
    )

    assert validated.queries[0].filters[0].value == "Pending"


def test_enabled_text_html_field_is_resolved_as_a_text_field():
    metadata = models()
    description = next(f for f in metadata[0].fields if f.name == "description")
    assert description.type == "html"
    # The shared fixture only sets `enabled=True`; text search on html fields
    # is opt-in and previously impossible regardless of this flag.
    description.search_config = {"enabled": True, "text": True}

    validated = SearchPlanValidator.validate_with_models(
        plan(text="hola"),
        metadata,
    )

    text_field_names = [f.field.name for f in validated.queries[0].text_fields]
    assert "description" in text_field_names
