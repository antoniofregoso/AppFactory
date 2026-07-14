from types import SimpleNamespace

import jwt
import pytest

from app.core.config.settings import settings
from app.core.exceptions import AuthorizationException
from app.domains.users.graphql import mutations


def _decode(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE,
    )


async def test_generate_mcp_token_rejects_user_without_access(monkeypatch):
    user = SimpleNamespace(email="user@test.com", mcp_access=False)

    async def fake_get_current_user(info):
        return user

    monkeypatch.setattr(mutations, "get_current_user", fake_get_current_user)

    with pytest.raises(AuthorizationException):
        await mutations.UserMutation().generate_mcp_token(info=None)


async def test_generate_mcp_token_succeeds_for_granted_user(monkeypatch):
    user = SimpleNamespace(email="director@test.com", mcp_access=True)

    async def fake_get_current_user(info):
        return user

    monkeypatch.setattr(mutations, "get_current_user", fake_get_current_user)

    token = await mutations.UserMutation().generate_mcp_token(info=None)
    payload = _decode(token)

    assert payload["sub"] == "director@test.com"
    assert payload["token_type"] == "mcp"
