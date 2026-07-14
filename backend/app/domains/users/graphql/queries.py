import uuid as uuid_lib

import strawberry
from strawberry.scalars import JSON

from app.domains.users.graphql.mappers import user_log_to_type
from app.domains.users.graphql.types import UserActivityPeriod, UserLogType, UserType
from app.core.security.jwt_bearer import IsAuthenticated
from app.core.security.jwt_manager import JWTManager
from app.core.exceptions import AuthorizationException
from app.domains.users.service.user_log_service import UserLogService
from app.domains.users.service.user_activity_graphics_service import (
    UserActivityGraphicsService,
)
from app.domains.users.service.user_service import UserService


async def get_current_user(info: strawberry.types.Info):
    request = info.context["request"]
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = JWTManager.verify_token(token, expected_token_type="access")
    user = await UserService.get_by_email(payload["sub"])
    if not user.active:
        raise AuthorizationException("User account is disabled")
    return user


@strawberry.type
class UserQuery:

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def user_activity_graphics(
        self,
        info: strawberry.types.Info,
        period: UserActivityPeriod = UserActivityPeriod.today,
    ) -> JSON:
        """Builds real user-activity KPI and chart data without mounting a view."""
        user = await get_current_user(info)
        if not user.is_admin:
            raise AuthorizationException("Administrator access is required")
        return await UserActivityGraphicsService.get(period.value, user.company_id)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def me(self, info: strawberry.types.Info) -> UserType:
        """Retorna el usuario autenticado actual a partir del token JWT."""
        user = await get_current_user(info)
        return UserType(
            id=user.id,
            uuid=user.uuid,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            theme=user.theme.value,
            lang=user.lang.name if user.lang else None,
            active=user.active,
            is_admin=user.is_admin,
        )

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def user_logs(
        self,
        info: strawberry.types.Info,
        limit: int = 50,
    ) -> list[UserLogType]:
        """Retorna los logs del usuario autenticado."""
        user = await get_current_user(info)
        logs = await UserLogService.get_by_user_id(user.id, limit)
        return [user_log_to_type(log) for log in logs]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def user_log(
        self,
        info: strawberry.types.Info,
        log_uuid: uuid_lib.UUID,
    ) -> UserLogType:
        """Retorna un log del usuario autenticado."""
        user = await get_current_user(info)
        log = await UserLogService.get_by_uuid_and_user_id(log_uuid, user.id)
        return user_log_to_type(log)
