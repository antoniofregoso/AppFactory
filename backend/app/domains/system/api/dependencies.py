from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security.jwt_manager import JWTManager
from app.domains.users.models.user_user import UserUser
from app.domains.users.service.user_service import UserService

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> UserUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationException("Authentication required")
    try:
        payload = JWTManager.verify_token(
            credentials.credentials,
            expected_token_type="access",
        )
    except ValueError as exc:
        raise AuthenticationException("Invalid or expired token") from exc

    email = payload.get("sub")
    if not email:
        raise AuthenticationException("Invalid token subject")
    user = await UserService.get_by_email(email)
    if not user.active:
        raise AuthorizationException("User account is disabled")
    return user
