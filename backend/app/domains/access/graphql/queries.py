import strawberry

from app.core.security.jwt_bearer import IsAuthenticated
from app.domains.access.graphql.mappers import permission_type, role_type, user_role_type
from app.domains.access.graphql.types import AccessPermissionType, AccessRoleType, AccessUserRoleType
from app.domains.access.repository import AccessRepository
from app.domains.access.service import AccessService
from app.domains.users.graphql.queries import get_current_user


async def require_access_manager(info):
    user = await get_current_user(info)
    await AccessService.require(user, "access.manage", company_id=user.company_id)
    return user


@strawberry.type
class AccessQuery:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def access_permissions(self, info: strawberry.types.Info) -> list[AccessPermissionType]:
        await require_access_manager(info)
        return [permission_type(item) for item in await AccessRepository.permissions()]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def access_roles(self, info: strawberry.types.Info) -> list[AccessRoleType]:
        user = await require_access_manager(info)
        return [role_type(role, permissions) for role, permissions in await AccessRepository.roles(user.company_id)]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def access_user_roles(self, info: strawberry.types.Info) -> list[AccessUserRoleType]:
        user = await require_access_manager(info)
        return [user_role_type(*row) for row in await AccessRepository.user_roles(user.company_id)]
