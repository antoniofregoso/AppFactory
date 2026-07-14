"""Tests for user updates that revoke sessions."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.domains.users.service.auth_service import AuthService
from app.domains.users.service.user_service import UserService


CURRENT_PASSWORD = "currentPassword123"


def _mock_existing_user(monkeypatch, user_id: int):
    """`UserService.update` re-fetches the user to verify `current_password`
    for any critical operation (password change / deactivation)."""
    existing_user = SimpleNamespace(id=user_id, password=AuthService.hash_password(CURRENT_PASSWORD))

    async def get_user_by_uuid(_user_uuid):
        return existing_user

    monkeypatch.setattr(
        "app.domains.users.service.user_service.UserRepository.get_user_by_uuid",
        get_user_by_uuid,
    )
    return existing_user


@pytest.mark.asyncio
async def test_update_password_hashes_password_and_revokes_sessions(monkeypatch):
    user_uuid = uuid4()
    updated_payload = {}
    revoked_user_ids = []
    user = SimpleNamespace(id=42)
    _mock_existing_user(monkeypatch, user.id)

    async def update(received_uuid, user_data):
        assert received_uuid == user_uuid
        updated_payload.update(user_data)
        return user

    async def revoke_user_sessions(user_id: int):
        revoked_user_ids.append(user_id)
        return 1

    monkeypatch.setattr(
        "app.domains.users.service.user_service.UserRepository.update",
        update,
    )
    monkeypatch.setattr(
        "app.domains.users.service.user_service.AuthService.revoke_user_sessions",
        revoke_user_sessions,
    )

    result = await UserService.update(
        user_uuid, {"password": "newPassword123"}, current_password=CURRENT_PASSWORD
    )

    assert result is user
    assert updated_payload["password"] != "newPassword123"
    assert AuthService.verify_password("newPassword123", updated_payload["password"])
    assert revoked_user_ids == [user.id]


@pytest.mark.asyncio
async def test_update_inactive_user_revokes_sessions(monkeypatch):
    user_uuid = uuid4()
    revoked_user_ids = []
    user = SimpleNamespace(id=42)
    _mock_existing_user(monkeypatch, user.id)

    async def update(received_uuid, user_data):
        assert received_uuid == user_uuid
        assert user_data == {"active": False}
        return user

    async def revoke_user_sessions(user_id: int):
        revoked_user_ids.append(user_id)
        return 2

    monkeypatch.setattr(
        "app.domains.users.service.user_service.UserRepository.update",
        update,
    )
    monkeypatch.setattr(
        "app.domains.users.service.user_service.AuthService.revoke_user_sessions",
        revoke_user_sessions,
    )

    result = await UserService.update(
        user_uuid, {"active": False}, current_password=CURRENT_PASSWORD
    )

    assert result is user
    assert revoked_user_ids == [user.id]
