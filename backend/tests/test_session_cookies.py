from types import SimpleNamespace

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.core.config.settings import settings
from app.core.exceptions import AuthenticationException
from app.core.security.session_cookies import (
    require_refresh_cookie,
    set_refresh_cookies,
)
from app.domains.users.graphql.mutations import UserMutation
from app.domains.users.graphql.types import RefreshSessionInput
from app.domains.users.service.auth_service import AuthService, LoginResult


def make_request(
    cookie: str = "", csrf_header: str | None = None, scheme: str = "https"
) -> Request:
    headers = []
    if cookie:
        headers.append((b"cookie", cookie.encode("latin-1")))
    if csrf_header:
        headers.append(
            (
                settings.REFRESH_CSRF_HEADER_NAME.lower().encode("latin-1"),
                csrf_header.encode("latin-1"),
            )
        )
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": scheme,
            "server": ("test", 443 if scheme == "https" else 80),
            "path": "/graphql",
            "headers": headers,
        }
    )


def test_set_refresh_cookies_uses_secure_http_only_refresh_cookie():
    response = Response()

    set_refresh_cookies(response, "raw-refresh-token")

    set_cookie_headers = response.headers.getlist("set-cookie")
    refresh_cookie = next(
        header
        for header in set_cookie_headers
        if header.startswith(f"{settings.REFRESH_COOKIE_NAME}=")
    )
    assert "HttpOnly" in refresh_cookie
    assert "Secure" in refresh_cookie
    assert "SameSite=lax" in refresh_cookie
    assert f"Path={settings.REFRESH_COOKIE_PATH}" in refresh_cookie


def test_require_refresh_cookie_validates_double_submit_csrf_token():
    request = make_request(
        "refresh_token=raw-refresh-token; refresh_csrf=csrf-token",
        csrf_header="csrf-token",
    )

    assert require_refresh_cookie(request) == "raw-refresh-token"


def test_require_refresh_cookie_rejects_missing_csrf_header():
    request = make_request("refresh_token=raw-refresh-token; refresh_csrf=csrf-token")

    try:
        require_refresh_cookie(request)
    except AuthenticationException as exc:
        assert "Invalid CSRF token" in exc.message
    else:
        raise AssertionError("Expected CSRF validation to fail")


@pytest.mark.asyncio
async def test_https_refresh_flow_validates_csrf_and_rotates_secure_cookie(monkeypatch):
    old_refresh_token = "old-refresh-token"
    new_refresh_token = "new-refresh-token"
    request = make_request(
        f"{settings.REFRESH_COOKIE_NAME}={old_refresh_token}; "
        f"{settings.REFRESH_CSRF_COOKIE_NAME}=csrf-token",
        csrf_header="csrf-token",
        scheme="https",
    )
    response = Response()
    received_tokens = []

    async def refresh_session(refresh_token: str):
        received_tokens.append(refresh_token)
        return LoginResult(
            email="admin@app.com",
            token="new-access-token",
            access_token="new-access-token",
            refresh_token=new_refresh_token,
        )

    monkeypatch.setattr(AuthService, "refresh_session", refresh_session)
    monkeypatch.setattr(settings, "REFRESH_COOKIE_SECURE", True)

    result = await UserMutation().refresh_session(
        SimpleNamespace(context={"request": request, "response": response}),
        RefreshSessionInput(),
    )

    assert request.url.scheme == "https"
    assert received_tokens == [old_refresh_token]
    assert result.access_token == "new-access-token"
    assert result.refresh_token is None
    set_cookie_headers = response.headers.getlist("set-cookie")
    rotated_cookie = next(
        header
        for header in set_cookie_headers
        if header.startswith(f"{settings.REFRESH_COOKIE_NAME}=")
    )
    assert new_refresh_token in rotated_cookie
    assert "HttpOnly" in rotated_cookie
    assert "Secure" in rotated_cookie
