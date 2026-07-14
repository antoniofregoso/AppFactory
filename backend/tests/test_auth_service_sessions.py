"""Tests for auth session persistence."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.core.exceptions import AuthenticationException
from app.domains.users.service.auth_service import AuthService


@pytest.mark.asyncio
async def test_login_stores_only_refresh_token_hash(monkeypatch):
    raw_refresh_token = "raw-refresh-token"
    stored_sessions = []
    user = SimpleNamespace(
        id=42,
        email="admin@app.com",
        password=AuthService.hash_password("changeMe123"),
        active=True,
    )

    async def get_by_email(email: str):
        assert email == "admin@app.com"
        return user

    async def create(session):
        stored_sessions.append(session)
        return session

    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserRepository.get_by_email",
        get_by_email,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.generate_refresh_token",
        lambda data: raw_refresh_token,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.generate_access_token",
        lambda data: "access-token",
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.create",
        create,
    )

    result = await AuthService.login("admin@app.com", "changeMe123")

    assert result.refresh_token == raw_refresh_token
    assert stored_sessions
    assert stored_sessions[0].user_id == user.id
    assert stored_sessions[0].absolute_expires_at > stored_sessions[0].expires_at
    assert stored_sessions[0].refresh_token_hash != raw_refresh_token
    assert stored_sessions[0].refresh_token_hash == AuthService.hash_refresh_token(
        raw_refresh_token
    )


def test_hash_refresh_token_is_stable_and_not_plain_text():
    raw_refresh_token = "raw-refresh-token"

    first_hash = AuthService.hash_refresh_token(raw_refresh_token)
    second_hash = AuthService.hash_refresh_token(raw_refresh_token)

    assert first_hash == second_hash
    assert first_hash != raw_refresh_token
    assert len(first_hash) == 64


def test_session_absolute_expiration_is_later_than_refresh_expiration():
    refresh_expires_at = AuthService._refresh_token_expires_at()
    absolute_expires_at = AuthService._session_absolute_expires_at()

    assert absolute_expires_at > refresh_expires_at


@pytest.mark.asyncio
async def test_refresh_session_revokes_used_refresh_token_and_stores_new_hash(
    monkeypatch,
):
    old_refresh_token = "old-refresh-token"
    new_refresh_token = "new-refresh-token"
    user = SimpleNamespace(id=42, email="admin@app.com", active=True)
    used_session = SimpleNamespace(
        id=7,
        user_id=user.id,
        refresh_token_hash=AuthService.hash_refresh_token(old_refresh_token),
        absolute_expires_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        revoked_at=None,
    )
    stored_sessions = []
    revoked_sessions = []

    async def get_by_email(email: str):
        assert email == user.email
        return user

    async def get_active_by_refresh_token_hash(refresh_token_hash: str):
        assert refresh_token_hash == used_session.refresh_token_hash
        return used_session

    async def revoke(session):
        session.revoked_at = datetime.now(timezone.utc)
        revoked_sessions.append(session)
        return session

    async def create(session):
        stored_sessions.append(session)
        return session

    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.verify_token",
        lambda token, expected_token_type=None: {"sub": user.email},
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.generate_refresh_token",
        lambda data: new_refresh_token,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.generate_access_token",
        lambda data: "new-access-token",
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserRepository.get_by_email",
        get_by_email,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.get_active_by_refresh_token_hash",
        get_active_by_refresh_token_hash,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.revoke",
        revoke,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.create",
        create,
    )

    result = await AuthService.refresh_session(old_refresh_token)

    assert result.access_token == "new-access-token"
    assert result.refresh_token == new_refresh_token
    assert revoked_sessions == [used_session]
    assert used_session.revoked_at is not None
    assert stored_sessions
    assert stored_sessions[0].user_id == user.id
    assert stored_sessions[0].absolute_expires_at == used_session.absolute_expires_at
    assert stored_sessions[0].refresh_token_hash == AuthService.hash_refresh_token(
        new_refresh_token
    )


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token_hash(monkeypatch):
    raw_refresh_token = "raw-refresh-token"
    session = SimpleNamespace(user_id=42)
    revoked_hashes = []
    closed_user_ids = []

    async def get_by_refresh_token_hash(refresh_token_hash: str):
        assert refresh_token_hash == AuthService.hash_refresh_token(raw_refresh_token)
        return session

    async def revoke_by_refresh_token_hash(refresh_token_hash: str):
        revoked_hashes.append(refresh_token_hash)
        return True

    async def close_open_for_user(user_id: int):
        closed_user_ids.append(user_id)
        return None

    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.get_by_refresh_token_hash",
        get_by_refresh_token_hash,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.revoke_by_refresh_token_hash",
        revoke_by_refresh_token_hash,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserLogService.close_open_for_user",
        close_open_for_user,
    )

    result = await AuthService.logout(raw_refresh_token)

    assert result is True
    assert closed_user_ids == [session.user_id]
    assert revoked_hashes == [AuthService.hash_refresh_token(raw_refresh_token)]


@pytest.mark.asyncio
async def test_refresh_session_detects_reused_refresh_token_and_revokes_user_sessions(
    monkeypatch,
):
    reused_refresh_token = "reused-refresh-token"
    reused_session = SimpleNamespace(
        id=7,
        user_id=42,
        refresh_token_hash=AuthService.hash_refresh_token(reused_refresh_token),
        revoked_at=datetime.now(timezone.utc),
    )
    revoked_user_ids = []

    async def get_active_by_refresh_token_hash(refresh_token_hash: str):
        assert refresh_token_hash == reused_session.refresh_token_hash
        return None

    async def get_by_refresh_token_hash(refresh_token_hash: str):
        assert refresh_token_hash == reused_session.refresh_token_hash
        return reused_session

    async def revoke_all_by_user_id(user_id: int):
        revoked_user_ids.append(user_id)
        return 2

    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.verify_token",
        lambda token, expected_token_type=None: {"sub": "admin@app.com"},
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.get_active_by_refresh_token_hash",
        get_active_by_refresh_token_hash,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.get_by_refresh_token_hash",
        get_by_refresh_token_hash,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.revoke_all_by_user_id",
        revoke_all_by_user_id,
    )

    with pytest.raises(AuthenticationException, match="reuse detected"):
        await AuthService.refresh_session(reused_refresh_token)

    assert revoked_user_ids == [reused_session.user_id]


@pytest.mark.asyncio
async def test_refresh_session_rejects_expired_jwt_before_database_lookup(monkeypatch):
    database_lookups = []

    def verify_token(*args, **kwargs):
        raise ValueError("Token expired")

    async def get_active_by_refresh_token_hash(refresh_token_hash: str):
        database_lookups.append(refresh_token_hash)

    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.verify_token",
        verify_token,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.get_active_by_refresh_token_hash",
        get_active_by_refresh_token_hash,
    )

    with pytest.raises(AuthenticationException, match="Invalid or expired"):
        await AuthService.refresh_session("expired-refresh-token")

    assert database_lookups == []


@pytest.mark.asyncio
async def test_refresh_session_rejects_session_past_absolute_expiration(monkeypatch):
    refresh_token = "absolute-expired-refresh-token"
    expired_session = SimpleNamespace(
        user_id=42,
        refresh_token_hash=AuthService.hash_refresh_token(refresh_token),
        revoked_at=None,
        absolute_expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    async def get_active_by_refresh_token_hash(refresh_token_hash: str):
        assert refresh_token_hash == expired_session.refresh_token_hash
        return None

    async def get_by_refresh_token_hash(refresh_token_hash: str):
        assert refresh_token_hash == expired_session.refresh_token_hash
        return expired_session

    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.verify_token",
        lambda token, expected_token_type=None: {"sub": "admin@app.com"},
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.get_active_by_refresh_token_hash",
        get_active_by_refresh_token_hash,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.get_by_refresh_token_hash",
        get_by_refresh_token_hash,
    )

    with pytest.raises(AuthenticationException, match="Invalid refresh token"):
        await AuthService.refresh_session(refresh_token)


@pytest.mark.asyncio
async def test_logins_from_multiple_devices_create_independent_sessions(monkeypatch):
    refresh_tokens = iter(["laptop-refresh-token", "phone-refresh-token"])
    stored_sessions = []
    revoked_hashes = []
    user = SimpleNamespace(
        id=42,
        email="admin@app.com",
        password=AuthService.hash_password("changeMe123"),
        active=True,
    )

    async def get_by_email(email: str):
        return user

    async def create(session):
        session.id = len(stored_sessions) + 1
        stored_sessions.append(session)
        return session

    async def get_by_refresh_token_hash(refresh_token_hash: str):
        return next(
            session
            for session in stored_sessions
            if session.refresh_token_hash == refresh_token_hash
        )

    async def revoke_by_refresh_token_hash(refresh_token_hash: str):
        revoked_hashes.append(refresh_token_hash)
        return True

    async def close_open_for_user(user_id: int):
        return None

    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserRepository.get_by_email",
        get_by_email,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.generate_refresh_token",
        lambda data: next(refresh_tokens),
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.JWTManager.generate_access_token",
        lambda data: "access-token",
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.create",
        create,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.get_by_refresh_token_hash",
        get_by_refresh_token_hash,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserSessionRepository.revoke_by_refresh_token_hash",
        revoke_by_refresh_token_hash,
    )
    monkeypatch.setattr(
        "app.domains.users.service.auth_service.UserLogService.close_open_for_user",
        close_open_for_user,
    )

    laptop = await AuthService.login("admin@app.com", "changeMe123")
    phone = await AuthService.login("admin@app.com", "changeMe123")
    await AuthService.logout(laptop.refresh_token)

    assert len(stored_sessions) == 2
    assert (
        stored_sessions[0].refresh_token_hash != stored_sessions[1].refresh_token_hash
    )
    assert revoked_hashes == [stored_sessions[0].refresh_token_hash]
    assert stored_sessions[1].refresh_token_hash == AuthService.hash_refresh_token(
        phone.refresh_token
    )
