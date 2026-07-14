"""Tests for JWT token generation."""

from datetime import datetime, timezone

import jwt

from app.core.config.settings import settings
from app.core.security.jwt_manager import JWTManager


def decode_without_exp_validation(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"verify_exp": False},
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE,
    )


def seconds_until_expiration(payload: dict) -> float:
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    return (expires_at - datetime.now(timezone.utc)).total_seconds()


def test_generate_access_token_uses_configured_minutes():
    token = JWTManager.generate_access_token({"sub": "admin@app.com"})
    payload = decode_without_exp_validation(token)

    assert payload["sub"] == "admin@app.com"
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE
    assert payload["token_type"] == "access"
    assert payload["jti"]
    expected_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert expected_seconds - 5 <= seconds_until_expiration(payload) <= expected_seconds


def test_generate_refresh_token_uses_configured_days():
    token = JWTManager.generate_refresh_token({"sub": "admin@app.com"})
    payload = decode_without_exp_validation(token)

    assert payload["sub"] == "admin@app.com"
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE
    assert payload["token_type"] == "refresh"
    assert payload["jti"]
    expected_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    assert expected_seconds - 5 <= seconds_until_expiration(payload) <= expected_seconds


def test_generate_mcp_token_uses_configured_days():
    token = JWTManager.generate_mcp_token({"sub": "admin@app.com"})
    payload = decode_without_exp_validation(token)

    assert payload["sub"] == "admin@app.com"
    assert payload["token_type"] == "mcp"
    expected_seconds = settings.MCP_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    assert expected_seconds - 5 <= seconds_until_expiration(payload) <= expected_seconds


def test_verify_token_rejects_unexpected_token_type():
    token = JWTManager.generate_refresh_token({"sub": "admin@app.com"})

    try:
        JWTManager.verify_token(token, expected_token_type="access")
    except ValueError as exc:
        assert "Invalid token type" in str(exc)
    else:
        raise AssertionError("Expected token type validation to fail")
