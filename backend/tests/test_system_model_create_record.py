from types import SimpleNamespace
import uuid

import pytest

from app.core.exceptions import AuthorizationException
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.service.system_model_service import SystemModelService
from app.domains.users.repository.user_repository import UserRepository
from app.domains.users.service.auth_service import AuthService
from app.domains.system.service.system_message_service import SystemMessageService


async def test_user_log_records_are_read_only():
    record_uuid = uuid.uuid4()

    with pytest.raises(AuthorizationException, match="read-only"):
        await SystemModelService.create_record("user.log", {})
    with pytest.raises(AuthorizationException, match="read-only"):
        await SystemModelService.update_record("user.log", record_uuid, {})
    with pytest.raises(AuthorizationException, match="read-only"):
        await SystemModelService.delete_record("user.log", record_uuid)


async def test_create_user_record_hashes_password_and_returns_safe_record(monkeypatch):
    captured = {}

    async def no_existing_user(email):
        assert email == "ana@example.com"
        return None

    async def get_creator(user_id):
        assert user_id == 3
        return SimpleNamespace(
            uuid=uuid.uuid4(), name="Admin", email="admin@example.com",
            avatar_url=None, user_type="HUMAN",
        )

    async def create_record(model, values):
        captured.update(values)
        return SimpleNamespace(
            id=9,
            uuid=uuid.uuid4(),
            name=values["name"],
            email=values["email"],
            password=values["password"],
            avatar_url=None,
            theme="system",
            lang_id=None,
            user_type="HUMAN",
            active=True,
            is_admin=False,
            mcp_access=False,
            company_id=None,
            created_at=None,
            create_by=3,
            updated_at=None,
            updated_by=None,
        )

    monkeypatch.setattr(UserRepository, "get_by_email", no_existing_user)
    monkeypatch.setattr(UserRepository, "get_by_id", get_creator)
    monkeypatch.setattr(SystemModelRepository, "create_record", create_record)

    result = await SystemModelService.create_record(
        "user.user",
        {
            "name": "Ana Admin",
            "email": "ana@example.com",
            "password": "password123",
            "user_type": "HUMAN",
        },
        current_user_id=3,
    )

    assert AuthService.verify_password("password123", captured["password"])
    assert result["email"] == "ana@example.com"
    assert captured["user_type"] == "HUMAN"
    assert "password" not in result
    assert result["followers"][0]["name"] == "Admin"


async def test_update_record_persists_virtual_followers(monkeypatch):
    record_uuid = uuid.uuid4()
    follower_uuid = uuid.uuid4()
    record = SimpleNamespace(uuid=record_uuid, name="SO001")
    follower = SimpleNamespace(
        uuid=follower_uuid, name="Ana", email="ana@example.com",
        avatar_url=None, user_type="HUMAN",
    )

    async def existing(model, uuid_value):
        return record

    async def update(model, uuid_value, values):
        assert values == {}
        return record

    async def get_model(model):
        return SimpleNamespace(id=7)

    async def set_followers(model_id, uuid_value, user_uuids, current_user_id):
        assert (model_id, uuid_value, user_uuids, current_user_id) == (7, record_uuid, [follower_uuid], 3)
        return [follower]

    monkeypatch.setattr(SystemModelRepository, "get_record_by_uuid", existing)
    monkeypatch.setattr(SystemModelRepository, "update_record", update)
    monkeypatch.setattr(SystemModelRepository, "get_by_name", get_model)
    monkeypatch.setattr(SystemModelRepository, "set_followers_for_record", set_followers)

    result = await SystemModelService.update_record(
        "user.user", record_uuid, {"followers": [{"uuid": str(follower_uuid)}]}, 3,
    )
    assert result["followers"][0]["name"] == "Ana"


async def test_create_message_record_forces_authenticated_sender(monkeypatch):
    sender_uuid = uuid.uuid4()
    recipient_uuid = uuid.uuid4()
    sender = SimpleNamespace(
        id=3, uuid=sender_uuid, name="Admin", email="admin@example.com",
        avatar_url=None, user_type="HUMAN",
    )
    recipient = SimpleNamespace(
        id=4, uuid=recipient_uuid, name="Laslo", email="laslo@example.com",
        avatar_url=None, user_type="HUMAN",
    )

    async def get_sender(user_id):
        assert user_id == 3
        return sender

    async def create_message(values):
        assert values["from_user_uuid"] == sender_uuid
        assert values["to_user_uuids"] == [str(recipient_uuid)]
        return SimpleNamespace(
            uuid=uuid.uuid4(), status="Sent", date=None,
            subject=values["subject"], message=values["message"],
            from_user=sender, to_users=[recipient], created_at=None,
        )

    monkeypatch.setattr(UserRepository, "get_by_id", get_sender)
    monkeypatch.setattr(SystemMessageService, "create", create_message)

    result = await SystemModelService.create_record(
        "system.message",
        {
            "subject": {"es": "Prueba"},
            "message": {"es": "<p>Hola</p>"},
            "from_user_id": {"uuid": str(recipient_uuid)},
            "to_users": [str(recipient_uuid)],
        },
        current_user_id=3,
    )
    assert result["from_user_id"]["uuid"] == str(sender_uuid)
    assert result["to_users"][0]["uuid"] == str(recipient_uuid)
