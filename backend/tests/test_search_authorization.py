from types import MappingProxyType, SimpleNamespace

import pytest
from sqlalchemy import select

from app.domains.system.models.system_message import SystemMessage
from app.domains.system.models.system_model import SystemModelSchemaUse
from app.domains.system.models.system_task import SystemTask
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.search.authorization import (
    MESSAGE_AUTHORIZATION_POLICY,
    TASK_AUTHORIZATION_POLICY,
)
from app.domains.system.search.registry import (
    SEARCH_MODEL_REGISTRY,
    validate_configured_search_models,
    validate_search_model_registry,
)
from app.domains.system.service.system_model_service import SystemModelService


def test_secure_registry_is_an_immutable_explicit_allowlist():
    assert isinstance(SEARCH_MODEL_REGISTRY, MappingProxyType)
    assert set(SEARCH_MODEL_REGISTRY) == {
        "system.task",
        "system.message",
        "user.user",
    }
    assert SEARCH_MODEL_REGISTRY["system.task"].orm_class is SystemTask
    assert SEARCH_MODEL_REGISTRY["system.message"].orm_class is SystemMessage
    assert (
        SEARCH_MODEL_REGISTRY["system.task"].build_url("task-1")
        == "/dashboard/user/system.task/task-1"
    )

    with pytest.raises(TypeError):
        SEARCH_MODEL_REGISTRY["system.company"] = SEARCH_MODEL_REGISTRY["system.task"]


def test_registry_validation_rejects_enabled_but_unregistered_models():
    validate_search_model_registry({"system.task", "system.message"})

    with pytest.raises(RuntimeError, match="system.company"):
        validate_search_model_registry({"system.task", "system.company"})


@pytest.mark.asyncio
async def test_configured_search_models_are_validated_for_startup(monkeypatch):
    async def get_all():
        return [
            SimpleNamespace(name="system.task", search=True),
            SimpleNamespace(name="system.company", search=False),
        ]

    monkeypatch.setattr(SystemModelRepository, "get_all", get_all)

    await validate_configured_search_models()

    async def get_invalid_models():
        return [SimpleNamespace(name="system.company", search=True)]

    monkeypatch.setattr(SystemModelRepository, "get_all", get_invalid_models)
    with pytest.raises(RuntimeError, match="system.company"):
        await validate_configured_search_models()


def test_authorization_policies_build_parameterized_sql_predicates():
    task_query = TASK_AUTHORIZATION_POLICY.apply(select(SystemTask), 42).compile()
    message_query = MESSAGE_AUTHORIZATION_POLICY.apply(
        select(SystemMessage), 42
    ).compile()

    assert 42 in task_query.params.values()
    assert 42 in message_query.params.values()
    assert "42" not in str(task_query)
    assert "42" not in str(message_query)
    assert "EXISTS" in str(message_query)


@pytest.mark.parametrize(
    ("model_name", "policy", "records"),
    [
        (
            "system.task",
            TASK_AUTHORIZATION_POLICY,
            [
                SimpleNamespace(uuid="assigned", user_id=7),
                SimpleNamespace(uuid="other", user_id=8),
                SimpleNamespace(uuid="unassigned", user_id=None),
            ],
        ),
        (
            "system.message",
            MESSAGE_AUTHORIZATION_POLICY,
            [
                SimpleNamespace(uuid="sent", from_user_id=7, to_users=[]),
                SimpleNamespace(
                    uuid="received",
                    from_user_id=8,
                    to_users=[SimpleNamespace(id=7)],
                ),
                SimpleNamespace(
                    uuid="other",
                    from_user_id=8,
                    to_users=[SimpleNamespace(id=9)],
                ),
            ],
        ),
    ],
)
@pytest.mark.asyncio
async def test_view_visibility_matches_search_authorization_policy(
    monkeypatch, model_name, policy, records
):
    system_model = SimpleNamespace(
        id=None,
        uuid=None,
        name=model_name,
        label={"en_US": model_name},
        readonly=False,
        group_by=None,
        group_by_values=[],
        tags=[],
    )
    schema = SimpleNamespace(view=[{"name": "uuid", "type": "string"}])

    async def get_view_definition(model, use, name):
        return system_model, schema

    async def get_records(model, field_names, relation_names=None):
        return records

    async def get_followable_users():
        return []

    monkeypatch.setattr(
        SystemModelRepository, "get_view_definition", get_view_definition
    )
    monkeypatch.setattr(SystemModelRepository, "get_records", get_records)
    monkeypatch.setattr(
        SystemModelRepository, "get_followable_users", get_followable_users
    )

    view = await SystemModelService.get_view(
        model_name,
        SystemModelSchemaUse.view,
        "default",
        current_user_id=7,
    )

    expected = [record.uuid for record in records if policy.allows_record(record, 7)]
    assert [record["uuid"] for record in view["records"]] == expected
