"""Tests for app/mcp/auth.py: MCP tool calls must re-check mcp_access on
every call, not just when the token was minted, so revoking access takes
effect immediately."""

from types import SimpleNamespace

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from app.core.security.jwt_manager import JWTManager
from app.domains.users.service.user_service import UserService
from app.mcp import auth as mcp_auth


def make_ctx(token: str | None):
    headers = {"authorization": f"Bearer {token}"} if token else {}
    request = SimpleNamespace(headers=headers)
    return SimpleNamespace(request_context=SimpleNamespace(request=request))


async def test_rejects_missing_authorization_header():
    with pytest.raises(ToolError):
        await mcp_auth.get_authenticated_user(make_ctx(None))


async def test_rejects_access_token_instead_of_mcp_token():
    token = JWTManager.generate_access_token({"sub": "user@test.com"})
    with pytest.raises(ToolError):
        await mcp_auth.get_authenticated_user(make_ctx(token))


async def test_rejects_user_with_mcp_access_revoked(monkeypatch):
    token = JWTManager.generate_mcp_token({"sub": "user@test.com"})
    user = SimpleNamespace(active=True, mcp_access=False)

    async def fake_get_by_email(email):
        assert email == "user@test.com"
        return user

    monkeypatch.setattr(UserService, "get_by_email", fake_get_by_email)

    with pytest.raises(ToolError):
        await mcp_auth.get_authenticated_user(make_ctx(token))


async def test_accepts_user_with_mcp_access_granted(monkeypatch):
    token = JWTManager.generate_mcp_token({"sub": "director@test.com"})
    user = SimpleNamespace(active=True, mcp_access=True)

    async def fake_get_by_email(email):
        assert email == "director@test.com"
        return user

    monkeypatch.setattr(UserService, "get_by_email", fake_get_by_email)

    result = await mcp_auth.get_authenticated_user(make_ctx(token))

    assert result is user
