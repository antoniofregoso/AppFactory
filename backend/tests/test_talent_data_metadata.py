import json
from pathlib import Path

from app.domains.system.models.system_model import FieldType

DATA_DIR = Path(__file__).parents[1] / "app/domains/talent/data"


def _load(file_name):
    return json.loads((DATA_DIR / file_name).read_text(encoding="utf-8"))


def test_talent_metadata_describes_every_model_and_uses_valid_field_types():
    models = _load("system_models.json")
    allowed_types = {field_type.value for field_type in FieldType}
    models_by_name = {model["name"]: model for model in models}

    assert set(models_by_name) == {
        "talent.system",
        "talent.area",
        "talent.position",
        "talent.agent",
    }
    for model in models:
        assert all(field["type"] in allowed_types for field in model["fields"])

    for model_name in ("talent.system", "talent.area", "talent.position"):
        fields = {field["name"]: field for field in models_by_name[model_name]["fields"]}
        assert fields["name"]["type"] == "string_i18n"
    assert {
        field["type"]
        for model in models
        for field in model["fields"]
        if field["name"] in {"description", "mission"}
    } == {"html"}


def test_every_talent_model_has_a_valid_default_view():
    models = _load("system_models.json")
    schemas = _load("system_model_schemas.json")
    fields_by_model = {
        model["name"]: {field["name"] for field in model["fields"]} | {"uuid"}
        for model in models
    }

    assert {schema["model"] for schema in schemas} == set(fields_by_model)
    assert all(schema["name"] == "default" for schema in schemas)
    assert all(schema["use"] == "view" for schema in schemas)
    for schema in schemas:
        assert {
            field["name"] for field in schema["view"]
        } <= fields_by_model[schema["model"]]
        columns = [
            field["list"]["column"]
            for field in schema["view"]
            if "list" in field
        ]
        assert len(columns) == len(set(columns))
