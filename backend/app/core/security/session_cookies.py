from secrets import token_urlsafe

from fastapi import Request, Response

from app.core.config.settings import settings
from app.core.exceptions import AuthenticationException


def _cookie_max_age() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def set_refresh_cookies(response: Response, refresh_token: str) -> None:
    csrf_token = token_urlsafe(32)
    cookie_options = {
        "max_age": _cookie_max_age(),
        "secure": settings.REFRESH_COOKIE_SECURE,
        "samesite": settings.REFRESH_COOKIE_SAMESITE,
        "path": settings.REFRESH_COOKIE_PATH,
    }
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        **cookie_options,
    )
    response.set_cookie(
        settings.REFRESH_CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        **cookie_options,
    )


def clear_refresh_cookies(response: Response) -> None:
    cookie_options = {
        "secure": settings.REFRESH_COOKIE_SECURE,
        "samesite": settings.REFRESH_COOKIE_SAMESITE,
        "path": settings.REFRESH_COOKIE_PATH,
    }
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, **cookie_options)
    response.delete_cookie(settings.REFRESH_CSRF_COOKIE_NAME, **cookie_options)


def require_refresh_cookie(request: Request) -> str:
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    csrf_cookie = request.cookies.get(settings.REFRESH_CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(settings.REFRESH_CSRF_HEADER_NAME)

    if not refresh_token:
        raise AuthenticationException("Refresh token cookie is missing")
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise AuthenticationException("Invalid CSRF token")
    return refresh_token
