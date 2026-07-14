from app.domains.system.search.schema import SearchableSchemaError, SearchSchemaService
from tests.test_search_plan_validator import models


def test_searchable_schema_contains_only_authorized_models_and_fields():
    schema = SearchSchemaService.build_with_models(
        models(),
        language="es",
        timezone_name="America/Mexico_City",
    )

    assert [model.name for model in schema.models] == ["system.task"]
    fields = {field.name: field for field in schema.models[0].fields}
    assert set(fields) == {"title", "priority", "date_due", "user_id", "description"}
    assert fields["priority"].selection_values[2].label == "Urgente"
    assert fields["user_id"].relation_fields == ["name"]
    assert fields["description"].operators == []
    assert "password" not in schema.model_dump_json()
    assert schema.timezone == "America/Mexico_City"


def test_searchable_schema_rejects_a_model_outside_search_scope():
    try:
        SearchSchemaService.build_with_models(
            models(),
            language="en",
            timezone_name="UTC",
            requested_model="user.user",
        )
    except SearchableSchemaError as exc:
        assert "not available" in str(exc)
    else:
        raise AssertionError("disabled model should not be exposed")
