import typing

from strawberry.permission import BasePermission
from strawberry.types import Info

from app.core.security.jwt_manager import JWTManager


class IsAuthenticated(BasePermission):
    """Permiso de Strawberry que valida el token JWT en el header Authorization."""

    message = "User is not authenticated"

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        request = info.context["request"]
        authentication = request.headers.get("Authorization")

        if authentication and authentication.startswith("Bearer "):
            token = authentication.split("Bearer ")[1]
            try:
                JWTManager.verify_token(token, expected_token_type="access")
                return True
            except Exception:
                return False

        return False
