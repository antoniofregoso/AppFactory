import strawberry

from app.core.security.session_cookies import (
    clear_refresh_cookies,
    require_refresh_cookie,
    set_refresh_cookies,
)
from app.core.exceptions import AuthorizationException
from app.core.security.jwt_bearer import IsAuthenticated
from app.core.security.jwt_manager import JWTManager
from app.domains.users.graphql.mappers import user_log_to_type
from app.domains.users.graphql.queries import get_current_user
from app.domains.users.graphql.types import (
    UserLogType,
    LoginType,
    LoginInput,
    RefreshSessionInput,
    LogoutInput,
    RegisterInput,
)
from app.domains.users.service.auth_service import AuthService
from app.domains.users.service.user_log_service import UserLogService


@strawberry.type
class UserMutation:

    @strawberry.mutation
    async def login(self, info: strawberry.types.Info, login: LoginInput) -> LoginType:
        """Autentica un usuario y retorna access/refresh tokens JWT."""
        result = await AuthService.login(login.email, login.password)
        set_refresh_cookies(info.context["response"], result.refresh_token)
        return LoginType(
            email=result.email,
            token=result.token,
            access_token=result.access_token,
            refresh_token=None,
        )

    @strawberry.mutation
    async def refresh_session(
        self,
        info: strawberry.types.Info,
        refresh: RefreshSessionInput,
    ) -> LoginType:
        """Renueva la sesión usando la cookie HttpOnly de refresh token."""
        refresh_token = refresh.refresh_token or require_refresh_cookie(
            info.context["request"]
        )
        result = await AuthService.refresh_session(refresh_token)
        set_refresh_cookies(info.context["response"], result.refresh_token)
        return LoginType(
            email=result.email,
            token=result.token,
            access_token=result.access_token,
            refresh_token=None,
        )

    @strawberry.mutation
    async def logout(self, info: strawberry.types.Info, logout: LogoutInput) -> bool:
        """Revoca la sesión asociada al refresh token enviado."""
        refresh_token = logout.refresh_token
        if refresh_token is None:
            refresh_token = require_refresh_cookie(info.context["request"])
        result = await AuthService.logout(refresh_token)
        clear_refresh_cookies(info.context["response"])
        return result

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def heartbeat(self, info: strawberry.types.Info) -> UserLogType:
        """Registra actividad reciente del usuario autenticado."""
        user = await get_current_user(info)
        log = await UserLogService.heartbeat(user.id)
        return user_log_to_type(log)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def generate_mcp_token(self, info: strawberry.types.Info) -> str:
        """Genera un token de larga duración para conectar clientes MCP de solo lectura."""
        user = await get_current_user(info)
        if not user.mcp_access:
            raise AuthorizationException("MCP access is not enabled for this user")
        return JWTManager.generate_mcp_token({"sub": user.email})

    @strawberry.mutation
    async def register(self, register: RegisterInput) -> str:
        """Registra un nuevo usuario en el sistema."""
        return await AuthService.register(
            register.name, register.email, register.password
        )
