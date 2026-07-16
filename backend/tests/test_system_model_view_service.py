import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.domains.system.models.system_model import (
    SystemModelSchema,
    SystemModelSchemaUse,
)
from app.domains.system.models.system_timezone import SystemTimezone
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.service.system_model_service import SystemModelService
from app.domains.system.service.system_model_service import _schema_with_user_options
from app.domains.system.service.system_model_service import _schema_with_relation_models
from app.domains.system.service.system_model_service import _schema_with_selection_options

FOLLOWERS_FIELD = {
    "name": "followers",
    "type": "one2many_followers",
    "label": {
        "es_MX": "Seguidores",
        "en_US": "Followers",
        "es": "Seguidores",
        "en": "Followers",
    },
    "form": {"footer": "left"},
    "options": [],
}


def test_message_recipient_field_receives_user_options():
    options = [{"uuid": "user-1", "name": "Ana"}]
    schema = [
        {"name": "to_users", "type": "many2many_pills", "form": {"leftColumn": 1}}
    ]

    enriched = _schema_with_user_options(schema, options)

    assert enriched[0]["model"] == "user.user"
    assert enriched[0]["options"] == options


def test_one2many_relationship_infers_its_child_model_for_nested_creation():
    schema = [{"name": "employees", "type": "one2many", "form": {"tab": 0}}]

    enriched = _schema_with_relation_models("parties.party", schema)

    assert enriched[0]["model"] == "parties.party"


@pytest.mark.asyncio
async def test_selection_options_can_come_from_registered_models(monkeypatch):
    schema = [{
        "name": "scope_model",
        "type": "selection",
        "selection_model": "system.model",
        "form": {"readonly": True},
    }]

    async def fake_get_records(model, field_names, relation_names=None):
        assert model == "system.model"
        assert field_names == ["name", "label"]
        return [
            SimpleNamespace(
                name="talent.system",
                label={"es_MX": "Sistemas de talento", "en_US": "Talent systems"},
            ),
            SimpleNamespace(name="access.role", label={}),
        ]

    monkeypatch.setattr(SystemModelRepository, "get_records", fake_get_records)

    enriched = await _schema_with_selection_options(schema)

    assert enriched[0]["selection_values"] == [
        {
            "value": "talent.system",
            "color": "zinc",
            "es_MX": "Sistemas de talento",
            "en_US": "Talent systems",
        },
        {
            "value": "access.role",
            "color": "zinc",
            "es_MX": "access.role",
            "en_US": "access.role",
        },
    ]


@pytest.fixture(autouse=True)
def no_followers(monkeypatch):
    async def fake_get_followable_users():
        return []

    async def fake_get_followers_by_record(model_id, record_uuids):
        return {}

    monkeypatch.setattr(
        SystemModelRepository,
        "get_followable_users",
        fake_get_followable_users,
    )
    monkeypatch.setattr(
        SystemModelRepository,
        "get_followers_by_record",
        fake_get_followers_by_record,
    )


@pytest.mark.asyncio
async def test_system_model_view_places_group_values_under_group_by(monkeypatch):
    system_model = SimpleNamespace(
        name="sale.order",
        label={"en": "Sale Order", "es": "Orden de Venta"},
        group_by="status",
        group_by_values=[
            {"value": "draft", "color": "zinc", "en": "Draft", "es": "Borrador"}
        ],
        tags=[],
    )
    schema = SimpleNamespace(
        view=[
            {"name": "uuid", "type": "string"},
            {"name": "name", "type": "string"},
        ]
    )
    record = SimpleNamespace(uuid="record-uuid", name="SO001", status="draft")

    async def fake_get_view_definition(model, use, name):
        return system_model, schema

    async def fake_get_records(model, field_names, relation_names=None):
        assert field_names == ["uuid", "name", "followers", "status"]
        assert relation_names == []
        return [record]

    monkeypatch.setattr(
        SystemModelRepository,
        "get_view_definition",
        fake_get_view_definition,
    )
    monkeypatch.setattr(SystemModelRepository, "get_records", fake_get_records)

    result = await SystemModelService.get_view(
        "sale.order",
        SystemModelSchemaUse.view,
        "default",
    )

    assert list(result["model"]) == [
        "name",
        "label",
        "readonly",
        "groupBy",
        "status",
        "tags",
        "schema",
    ]
    assert result["model"]["groupBy"] == "status"
    assert result["model"]["status"] == system_model.group_by_values
    assert result["records"] == [
        {"uuid": "record-uuid", "name": "SO001", "followers": [], "status": "draft"}
    ]


@pytest.mark.asyncio
async def test_parties_view_is_scoped_to_current_company(monkeypatch):
    system_model = SimpleNamespace(
        id=10,
        uuid=uuid.uuid4(),
        name="parties.party",
        label={"en": "Parties", "es": "Contactos"},
        readonly=False,
        group_by=None,
        group_by_values=[],
        tags=[],
    )
    schema = SimpleNamespace(
        view=[
            {"name": "uuid", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "position", "type": "string_i18n"},
        ]
    )
    own_party = SimpleNamespace(
        uuid=uuid.uuid4(),
        name="Ana",
        position={"es_MX": "Directora"},
        company_id=7,
        create_by=None,
        sequence=10,
    )
    other_party = SimpleNamespace(
        uuid=uuid.uuid4(),
        name="Bob",
        position={"en_US": "Director"},
        company_id=8,
        create_by=None,
        sequence=10,
    )

    async def fake_get_view_definition(model, use, name):
        return system_model, schema

    async def fake_get_records(model, field_names, relation_names=None):
        return [own_party, other_party]

    monkeypatch.setattr(
        SystemModelRepository, "get_view_definition", fake_get_view_definition
    )
    monkeypatch.setattr(SystemModelRepository, "get_records", fake_get_records)

    result = await SystemModelService.get_view(
        "parties.party",
        SystemModelSchemaUse.view,
        "default",
        current_user_id=1,
        current_user=SimpleNamespace(company_id=7),
    )

    assert result["records"] == [
        {
            "uuid": str(own_party.uuid),
            "name": "Ana",
            "position": {"es_MX": "Directora"},
            "followers": [],
            "sequence": 10,
        }
    ]


@pytest.mark.asyncio
async def test_system_model_view_preserves_schema_payload(monkeypatch):
    schema_payload = [
        {"name": "uuid", "type": "string"},
        {"name": "name", "type": "string", "form": {"required": True}},
    ]
    system_model = SimpleNamespace(
        name="user.user",
        label={"en": "Users", "es": "Usuarios"},
        group_by=None,
        group_by_values=[],
        tags=[],
    )
    schema = SimpleNamespace(view={"schema": schema_payload})
    record = SimpleNamespace(uuid="user-uuid", name="App Admin")

    async def fake_get_view_definition(model, use, name):
        return system_model, schema

    async def fake_get_records(model, field_names, relation_names=None):
        assert field_names == ["uuid", "name", "followers"]
        assert relation_names == []
        return [record]

    monkeypatch.setattr(
        SystemModelRepository,
        "get_view_definition",
        fake_get_view_definition,
    )
    monkeypatch.setattr(SystemModelRepository, "get_records", fake_get_records)

    result = await SystemModelService.get_view(
        "user.user",
        SystemModelSchemaUse.view,
        "default",
    )

    assert result["model"]["schema"] == [*schema_payload, FOLLOWERS_FIELD]
    assert result["records"] == [
        {"uuid": "user-uuid", "name": "App Admin", "followers": []}
    ]


@pytest.mark.asyncio
async def test_system_model_view_includes_model_uuid_for_attachments(monkeypatch):
    model_uuid = uuid.uuid4()
    system_model = SimpleNamespace(
        id=7,
        uuid=model_uuid,
        name="user.user",
        label={"en": "Users", "es": "Usuarios"},
        group_by=None,
        group_by_values=[],
        tags=[],
    )
    schema = SimpleNamespace(view=[{"name": "uuid", "type": "string"}])
    record = SimpleNamespace(uuid="user-uuid")

    async def fake_get_view_definition(model, use, name):
        return system_model, schema

    async def fake_get_records(model, field_names, relation_names=None):
        assert field_names == ["uuid", "followers"]
        return [record]

    monkeypatch.setattr(
        SystemModelRepository,
        "get_view_definition",
        fake_get_view_definition,
    )
    monkeypatch.setattr(SystemModelRepository, "get_records", fake_get_records)

    result = await SystemModelService.get_view(
        "user.user",
        SystemModelSchemaUse.view,
        "default",
    )

    assert result["model"]["uuid"] == str(model_uuid)


@pytest.mark.asyncio
async def test_system_model_view_ignores_pydantic_schema_method(monkeypatch):
    schema_payload = [
        {"name": "uuid", "type": "string"},
        {"name": "name", "type": "string"},
    ]
    system_model = SimpleNamespace(
        name="system.model",
        label={"en": "Models", "es": "Modelos"},
        group_by=None,
        group_by_values=[],
        tags=[],
    )
    schema = SystemModelSchema(
        name="default",
        use=SystemModelSchemaUse.view,
        view=schema_payload,
        model_id=1,
    )
    record = SimpleNamespace(uuid="model-uuid", name="system.model")

    async def fake_get_view_definition(model, use, name):
        return system_model, schema

    async def fake_get_records(model, field_names, relation_names=None):
        assert field_names == ["uuid", "name", "followers"]
        assert relation_names == []
        return [record]

    monkeypatch.setattr(
        SystemModelRepository,
        "get_view_definition",
        fake_get_view_definition,
    )
    monkeypatch.setattr(SystemModelRepository, "get_records", fake_get_records)

    result = await SystemModelService.get_view(
        "system.model",
        SystemModelSchemaUse.view,
        "default",
    )

    assert result["model"]["schema"] == [*schema_payload, FOLLOWERS_FIELD]
    assert result["records"] == [
        {"uuid": "model-uuid", "name": "system.model", "followers": []}
    ]


@pytest.mark.asyncio
async def test_system_model_view_serializes_related_schemas_as_schema(monkeypatch):
    related_schema = SystemModelSchema(
        id=1,
        name="default",
        use=SystemModelSchemaUse.view,
        view=[{"name": "uuid", "type": "string"}],
        model_id=1,
    )
    system_model = SimpleNamespace(
        name="system.model",
        label={"en": "Models", "es": "Modelos"},
        group_by=None,
        group_by_values=[],
        tags=[],
    )
    schema = SimpleNamespace(
        view=[
            {"name": "uuid", "type": "string"},
            {"name": "schemas", "type": "one2many_list"},
        ]
    )
    record = SimpleNamespace(uuid="model-uuid", schemas=[related_schema])

    async def fake_get_view_definition(model, use, name):
        return system_model, schema

    async def fake_get_records(model, field_names, relation_names=None):
        assert field_names == ["uuid", "schemas", "followers"]
        assert relation_names == []
        return [record]

    monkeypatch.setattr(
        SystemModelRepository,
        "get_view_definition",
        fake_get_view_definition,
    )
    monkeypatch.setattr(SystemModelRepository, "get_records", fake_get_records)

    result = await SystemModelService.get_view(
        "system.model",
        SystemModelSchemaUse.view,
        "default",
    )

    related_payload = result["records"][0]["schemas"][0]
    assert "schema" in related_payload
    assert "view" not in related_payload
    assert related_payload["schema"] == [{"name": "uuid", "type": "string"}]


@pytest.mark.asyncio
async def test_system_model_view_serializes_many2one_with_translated_name(monkeypatch):
    company = SimpleNamespace(
        uuid="company-uuid",
        name={"en": "My Company", "es": "Mi Empresa"},
        avatar_url=None,
    )
    system_model = SimpleNamespace(
        name="user.user",
        label={"en": "Users", "es": "Usuarios"},
        group_by=None,
        group_by_values=[],
        tags=[],
    )
    schema = SimpleNamespace(
        view=[
            {"name": "uuid", "type": "string"},
            {"name": "company_id", "type": "many2one"},
        ]
    )
    record = SimpleNamespace(uuid="user-uuid", company=company)

    async def fake_get_view_definition(model, use, name):
        return system_model, schema

    async def fake_get_records(model, field_names, relation_names=None):
        assert field_names == ["uuid", "company_id", "followers"]
        assert relation_names == ["company"]
        return [record]

    monkeypatch.setattr(
        SystemModelRepository,
        "get_view_definition",
        fake_get_view_definition,
    )
    monkeypatch.setattr(SystemModelRepository, "get_records", fake_get_records)

    result = await SystemModelService.get_view(
        "user.user",
        SystemModelSchemaUse.view,
        "default",
    )

    assert result["records"] == [
        {
            "uuid": "user-uuid",
            "company_id": {
                "uuid": "company-uuid",
                "name": "Mi Empresa",
                "display_name": "Mi Empresa",
                "model": None,
            },
            "followers": [],
        }
    ]


@pytest.mark.asyncio
async def test_user_log_view_includes_user_name_in_list_and_kanban(monkeypatch):
    data_path = (
        Path(__file__).resolve().parents[1]
        / "app/domains/system/data/system_model_schemas.json"
    )
    schemas = json.loads(data_path.read_text(encoding="utf-8"))
    view = next(item["view"] for item in schemas if item["model"] == "user.log")
    user_field = next(field for field in view if field["name"] == "user_id")

    models_path = data_path.with_name("system_models.json")
    models = json.loads(models_path.read_text(encoding="utf-8"))
    user_log_model = next(item for item in models if item["name"] == "user.log")
    model_user_field = next(
        field for field in user_log_model["fields"] if field["name"] == "user_id"
    )

    assert model_user_field["type"] == "many2one_avatar"
    assert model_user_field["model"] == "user.user"
    assert model_user_field["sequence"] == 10
    assert user_field["type"] == "many2one_avatar"
    assert user_field["model"] == "user.user"
    assert user_field["list"] == {"column": 1}
    assert user_field["kanban"] == {"header": "title"}
    assert user_field["form"]["header"] == "title"
    assert user_field["form"]["readonly"] is True

    system_model = SimpleNamespace(
        name="user.log",
        label={"en_US": "User Logs", "es_MX": "Registros de sesión"},
        group_by="status",
        group_by_values=[],
        tags=[],
        readonly=True,
    )
    schema = SimpleNamespace(view=view)
    user = SimpleNamespace(uuid="user-uuid", name="Ana López", avatar_url=None)
    record = SimpleNamespace(
        uuid="log-uuid",
        user=user,
        status="Offline",
        start_date=None,
        last_seen_at=None,
        end_date=None,
        duration=1000,
    )

    async def fake_get_view_definition(model, use, name):
        return system_model, schema

    async def fake_get_records(model, field_names, relation_names=None):
        assert "user_id" in field_names
        assert relation_names == ["user"]
        return [record]

    monkeypatch.setattr(
        SystemModelRepository,
        "get_view_definition",
        fake_get_view_definition,
    )
    monkeypatch.setattr(SystemModelRepository, "get_records", fake_get_records)

    result = await SystemModelService.get_view(
        "user.log",
        SystemModelSchemaUse.view,
        "default",
    )

    assert result["records"][0]["user_id"]["name"] == "Ana López"
    assert result["model"]["readonly"] is True


@pytest.mark.asyncio
async def test_user_logs_insight_hydrates_declared_outputs(monkeypatch):
    system_model = SimpleNamespace(
        name="system.insight",
        label={"en_US": "Insights", "es_MX": "Paneles de información"},
    )
    schema = SimpleNamespace(
        name="userLogs",
        view={
            "period": "today",
            "layout": {"graphics": 2},
            "kpis": [
                "kpiUsersOnline",
                "kpiUsersAverageSessionTime",
                "kpiUsersActiveUsers",
                "kpiRecurringUsers",
            ],
            "gauges": [],
            "graphics": ["graphicUsersPerHour", "graphicUsersMAU"],
        },
    )
    generated = {
        "period": "weekly",
        "kpis": [
            {"id": "kpiUsersOnline", "value": 2},
            {"id": "kpiUsersAverageSessionTime", "value": 30},
            {"id": "kpiUsersActiveUsers", "value": 4},
            {"id": "kpiRecurringUsers", "value": 1},
        ],
        "graphics": [
            {"id": "graphicUsersPerHour", "type": "heatmap", "data": []},
            {"id": "graphicUsersMAU", "type": "bar", "data": [4]},
        ],
    }
    user = SimpleNamespace(id=7, company_id=9)

    async def allow(*args, **kwargs):
        return None

    monkeypatch.setattr("app.domains.access.service.AccessService.require", allow)

    async def get_view_definition(model, use, name):
        assert (model, use, name) == (
            "system.insight",
            SystemModelSchemaUse.insight,
            "userLogs",
        )
        return system_model, schema

    async def generate(period, company_id, *, timezone_name=None):
        assert period == "weekly"
        assert company_id == 9
        assert timezone_name == "America/Mexico_City"
        return generated

    monkeypatch.setattr(
        SystemModelRepository, "get_view_definition", get_view_definition
    )
    monkeypatch.setitem(
        __import__(
            "app.domains.system.service.system_model_service",
            fromlist=["INSIGHT_GENERATORS"],
        ).INSIGHT_GENERATORS,
        ("system.insight", "userLogs"),
        generate,
    )

    result = await SystemModelService.get_view(
        "system.insight",
        SystemModelSchemaUse.insight,
        "userLogs",
        current_user_id=user.id,
        current_user=user,
        period="weekly",
        timezone_name="America/Mexico_City",
    )

    insight = result["model"]["schema"]
    assert insight["period"] == "weekly"
    assert insight["layout"] == {"graphics": 2}
    assert [item["id"] for item in insight["kpis"]] == schema.view["kpis"]
    assert [item["id"] for item in insight["graphics"]] == schema.view["graphics"]
    assert insight["gauges"] == []
    assert result["records"] == []


def test_user_logs_insight_schema_is_assigned_to_virtual_insight_model():
    data_path = (
        Path(__file__).resolve().parents[1]
        / "app/domains/system/data/system_model_schemas.json"
    )
    schemas = json.loads(data_path.read_text(encoding="utf-8"))
    insight = next(
        item
        for item in schemas
        if item["name"] == "userLogs" and item["use"] == "insight"
    )

    assert insight["model"] == "system.insight"
    assert insight["view"]["period"] == "today"
    assert insight["view"]["kpis"] == [
        "kpiUsersOnline",
        "kpiUsersAverageSessionTime",
        "kpiUsersActiveUsers",
        "kpiRecurringUsers",
    ]
    assert insight["view"]["graphics"] == [
        "graphicUsersPerHour",
        "graphicUsersMAU",
    ]

    models_path = data_path.with_name("system_models.json")
    models = json.loads(models_path.read_text(encoding="utf-8"))
    virtual_model = next(item for item in models if item["name"] == "system.insight")
    assert virtual_model["readonly"] is True
    assert virtual_model["search"] is False
    assert virtual_model["fields"] == []


def test_app_settings_views_declare_both_sides_of_the_nested_relation():
    data_path = (
        Path(__file__).resolve().parents[1]
        / "app/domains/system/data/system_model_schemas.json"
    )
    schemas = json.loads(data_path.read_text(encoding="utf-8"))
    views = {schema["model"]: schema["view"] for schema in schemas}

    settings = next(
        field for field in views["system.app"] if field["name"] == "settings_ids"
    )
    app = next(
        field
        for field in views["system.app.settings"]
        if field["name"] == "app_id"
    )

    assert settings["model"] == "system.app.settings"
    assert app["type"] == "many2one"
    assert app["model"] == "system.app"
    assert "form" not in app


def test_country_form_uses_kanban_states_and_timezone_pills():
    data_path = (
        Path(__file__).resolve().parents[1]
        / "app/domains/system/data/system_model_schemas.json"
    )
    schemas = json.loads(data_path.read_text(encoding="utf-8"))
    country = next(schema for schema in schemas if schema["model"] == "system.country")
    fields = {field["name"]: field for field in country["view"]}

    assert fields["states"]["type"] == "one2many_kanban"
    assert fields["states"]["model"] == "system.country.state"
    assert fields["states"]["form"]["view"] == "one2many_kanban"
    assert fields["states"]["form"]["kanban_view"]["header"] == {
        "title": "name",
        "subtitle": "code",
    }
    assert fields["timezones"]["type"] == "many2many_pills"
    assert fields["timezones"]["model"] == "system.timezone"
    assert fields["name"]["list"]["order"] == "asc"


def test_timezone_seed_links_iana_zones_to_existing_country_codes():
    data_dir = Path(__file__).resolve().parents[1] / "app/domains/system/data"
    countries = json.loads(
        (data_dir / "system_country.json").read_text(encoding="utf-8")
    )
    timezones = json.loads(
        (data_dir / "system_timezone.json").read_text(encoding="utf-8")
    )
    country_codes = {record["code"] for record in countries}
    timezone_codes = [record["code"] for record in timezones]
    referenced_countries = {
        country_code
        for record in timezones
        for country_code in record["country_codes"]
    }
    mexico_timezones = {
        record["code"]
        for record in timezones
        if "MX" in record["country_codes"]
    }

    assert len(timezone_codes) == len(set(timezone_codes))
    assert referenced_countries <= country_codes
    assert "America/Mexico_City" in mexico_timezones
    assert "America/Cancun" in mexico_timezones


@pytest.mark.asyncio
async def test_country_view_loads_timezone_options_for_search(monkeypatch):
    system_model = SimpleNamespace(
        name="system.country",
        label={"es_MX": "Países", "en_US": "Countries"},
        group_by=None,
        group_by_values=[],
        tags=[],
        readonly=False,
        search=False,
        uuid=uuid.uuid4(),
        id=5,
    )
    schema = SimpleNamespace(
        view=[{
            "name": "timezones",
            "type": "many2many_pills",
            "model": "system.timezone",
            "form": {"tab": 0},
        }],
    )
    timezone = SystemTimezone(
        name="America/Mexico_City",
        code="CST",
        offset=-6,
    )

    async def get_view_definition(model, use, name):
        return system_model, schema

    async def get_records(model, field_names, relation_names=None):
        if model == "system.timezone":
            return [timezone]
        return []

    monkeypatch.setattr(SystemModelRepository, "get_view_definition", get_view_definition)
    monkeypatch.setattr(SystemModelRepository, "get_records", get_records)

    result = await SystemModelService.get_view(
        "system.country",
        SystemModelSchemaUse.view,
        "default",
    )

    options = result["model"]["schema"][0]["options"]
    assert options[0]["display_name"] == "America/Mexico_City"
    assert options[0]["model"] == "system.timezone"


@pytest.mark.asyncio
async def test_country_update_accepts_timezone_relationship(monkeypatch):
    country_uuid = uuid.uuid4()
    timezone = SystemTimezone(
        uuid=uuid.uuid4(),
        name="America/Mexico_City",
        code="CST",
        offset=-6,
    )
    captured = {}

    async def get_record_by_uuid(model, record_uuid):
        assert model == "system.country"
        assert record_uuid == country_uuid
        return SimpleNamespace(uuid=country_uuid)

    async def update_record(model, record_uuid, values):
        captured.update(values)
        return SimpleNamespace(uuid=country_uuid, timezones=[timezone])

    monkeypatch.setattr(
        SystemModelRepository, "get_record_by_uuid", get_record_by_uuid
    )
    monkeypatch.setattr(SystemModelRepository, "update_record", update_record)

    result = await SystemModelService.update_record(
        "system.country",
        country_uuid,
        {"timezones": [{"uuid": str(timezone.uuid)}]},
    )

    assert captured == {"timezones": [{"uuid": str(timezone.uuid)}]}
    assert result["timezones"][0]["uuid"] == str(timezone.uuid)
    assert result["timezones"][0]["model"] == "system.timezone"
