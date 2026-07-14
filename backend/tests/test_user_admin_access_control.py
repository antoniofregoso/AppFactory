"""Tests for the admin-only field protection on the user.user model,
added so any authenticated user can't self-grant is_admin/mcp_access/active
via the generic update_system_model_record / create_system_model_record
mutations."""

import uuid
from types import SimpleNamespace

import pytest

from app.core.exceptions import AuthorizationException, ValidationException
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.service.system_model_service import SystemModelService
from app.domains.users.repository.user_repository import UserRepository


async def test_create_user_record_blocks_is_admin_for_non_admin_caller(monkeypatch):
    async def non_admin(user_id):
        assert user_id == 3
        return SimpleNamespace(is_admin=False)

    async def no_existing_user(email):
        return None

    monkeypatch.setattr(UserRepository, "get_by_id", non_admin)
    monkeypatch.setattr(UserRepository, "get_by_email", no_existing_user)

    with pytest.raises(AuthorizationException):
        await SystemModelService.create_record(
            "user.user",
            {
                "name": "Ana Admin",
                "email": "ana@example.com",
                "password": "password123",
                "user_type": "HUMAN",
                "is_admin": True,
            },
            current_user_id=3,
        )


async def test_create_user_record_allows_privileged_fields_for_admin_caller(monkeypatch):
    captured = {}

    async def admin_caller(user_id):
        assert user_id == 3
        return SimpleNamespace(
            id=3,
            is_admin=True,
            uuid=uuid.uuid4(),
            name="Admin",
            email="admin@example.com",
            avatar_url=None,
            user_type="HUMAN",
        )

    async def no_existing_user(email):
        return None

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
            is_admin=values.get("is_admin", False),
            mcp_access=values.get("mcp_access", False),
            company_id=None,
            created_at=None,
            create_by=3,
            updated_at=None,
            updated_by=None,
        )

    monkeypatch.setattr(UserRepository, "get_by_id", admin_caller)
    monkeypatch.setattr(UserRepository, "get_by_email", no_existing_user)
    monkeypatch.setattr(SystemModelRepository, "create_record", create_record)

    result = await SystemModelService.create_record(
        "user.user",
        {
            "name": "Ana Admin",
            "email": "ana@example.com",
            "password": "password123",
            "user_type": "HUMAN",
            "is_admin": True,
            "mcp_access": True,
        },
        current_user_id=3,
    )

    assert captured["is_admin"] is True
    assert captured["mcp_access"] is True
    assert result["is_admin"] is True
    assert result["mcp_access"] is True


async def test_update_user_record_rejects_password_change(monkeypatch):
    record_uuid = uuid.uuid4()

    async def existing(model, uuid_value):
        return SimpleNamespace(uuid=record_uuid)

    monkeypatch.setattr(SystemModelRepository, "get_record_by_uuid", existing)

    with pytest.raises(ValidationException):
        await SystemModelService.update_record(
            "user.user", record_uuid, {"password": "newpassword123"}, 3,
        )


async def test_update_user_record_blocks_mcp_access_for_non_admin_caller(monkeypatch):
    record_uuid = uuid.uuid4()

    async def non_admin(user_id):
        assert user_id == 3
        return SimpleNamespace(is_admin=False)

    async def existing(model, uuid_value):
        return SimpleNamespace(uuid=record_uuid)

    monkeypatch.setattr(UserRepository, "get_by_id", non_admin)
    monkeypatch.setattr(SystemModelRepository, "get_record_by_uuid", existing)

    with pytest.raises(AuthorizationException):
        await SystemModelService.update_record(
            "user.user", record_uuid, {"mcp_access": True}, 3,
        )


async def test_update_user_record_allows_mcp_access_for_admin_caller(monkeypatch):
    record_uuid = uuid.uuid4()

    async def admin_caller(user_id):
        assert user_id == 3
        return SimpleNamespace(is_admin=True)

    async def existing(model, uuid_value):
        return SimpleNamespace(uuid=record_uuid)

    async def update(model, uuid_value, values):
        assert values == {"mcp_access": True}
        return SimpleNamespace(mcp_access=True)

    monkeypatch.setattr(UserRepository, "get_by_id", admin_caller)
    monkeypatch.setattr(SystemModelRepository, "get_record_by_uuid", existing)
    monkeypatch.setattr(SystemModelRepository, "update_record", update)

    result = await SystemModelService.update_record(
        "user.user", record_uuid, {"mcp_access": True}, 3,
    )

    assert result["mcp_access"] is True


async def test_update_user_record_ignores_admin_fields_for_unrelated_model(monkeypatch):
    """Sanity check: the user.user-only guard must not leak into other models."""
    record_uuid = uuid.uuid4()

    async def existing(model, uuid_value):
        return SimpleNamespace(uuid=record_uuid, user_id=99)

    async def update(model, uuid_value, values):
        return SimpleNamespace(status="Pending")

    monkeypatch.setattr(SystemModelRepository, "get_record_by_uuid", existing)
    monkeypatch.setattr(SystemModelRepository, "update_record", update)

    result = await SystemModelService.update_record(
        "system.task", record_uuid, {"status": "Pending"}, 99,
    )

    assert result["status"] == "Pending"
