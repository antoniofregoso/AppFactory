import json
from pathlib import Path


DATA_DIR = Path(__file__).parents[1] / "app/domains/access/data"


def _load(file_name: str):
    return json.loads((DATA_DIR / file_name).read_text(encoding="utf-8"))


def test_access_role_has_a_renderable_form_schema():
    schemas = {item["model"]: item for item in _load("system_model_schema.json")}
    fields = schemas["access.role"]["view"]

    assert any(field.get("form", {}).get("header") == "title" for field in fields)
    assert any("leftColumn" in field.get("form", {}) for field in fields)
    assert any("rightColumn" in field.get("form", {}) for field in fields)
    assert next(field for field in fields if field["name"] == "description")["form"]["tab"] == 0


def test_access_user_role_calendar_uses_user_and_validity_dates():
    schemas = {item["model"]: item for item in _load("system_model_schema.json")}
    fields = {field["name"]: field for field in schemas["access.user.role"]["view"]}

    assert fields["user_id"]["calendar"] == {"title": True}
    assert fields["date_start"]["calendar"] == {"startDate": True}
    assert fields["date_end"]["calendar"] == {"endDate": True}


def test_access_permission_action_is_a_selection():
    models = {item["name"]: item for item in _load("system_model.json")}
    schemas = {item["model"]: item for item in _load("system_model_schema.json")}
    model_action = next(
        field for field in models["access.permission"]["fields"]
        if field["name"] == "action"
    )
    view_action = next(
        field for field in schemas["access.permission"]["view"]
        if field["name"] == "action"
    )

    assert model_action["type"] == view_action["type"] == "selection"
    assert {item["value"] for item in view_action["selection_values"]} == {
        "read", "create", "update", "delete", "approve", "manage", "*",
    }


def test_scope_model_is_an_editable_selection_from_system_models():
    models = {item["name"]: item for item in _load("system_model.json")}
    schemas = {item["model"]: item for item in _load("system_model_schema.json")}
    model_field = next(
        field for field in models["access.user.role"]["fields"]
        if field["name"] == "scope_model"
    )
    view_field = next(
        field for field in schemas["access.user.role"]["view"]
        if field["name"] == "scope_model"
    )

    assert model_field["type"] == view_field["type"] == "selection"
    assert model_field["readonly"] is False
    assert view_field["form"]["readonly"] is False
    assert view_field["selection_model"] == "system.model"


def test_permission_kanban_uses_only_the_permission_name():
    models = {item["name"]: item for item in _load("system_model.json")}
    schemas = {item["model"]: item for item in _load("system_model_schema.json")}
    fields = schemas["access.permission"]["view"]
    kanban_fields = [field for field in fields if "kanban" in field]

    assert models["access.permission"]["group_by"] is False
    assert models["access.permission"]["group_by_values"] == []
    assert [(field["name"], field["kanban"]) for field in kanban_fields] == [
        ("name", {"header": "title"}),
    ]
