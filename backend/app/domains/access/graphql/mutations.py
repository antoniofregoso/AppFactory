from dataclasses import asdict
import uuid as uuid_lib

import strawberry

from app.core.exceptions import AuthorizationException, ValidationException
from app.core.security.jwt_bearer import IsAuthenticated
from app.domains.access.graphql.mappers import permission_type, role_type, user_role_type
from app.domains.access.graphql.queries import require_access_manager
from app.domains.access.graphql.types import AccessPermissionInput, AccessPermissionType, AccessRoleInput, AccessRoleType, AccessUserRoleInput, AccessUserRoleType
from app.domains.access.repository import AccessRepository
from app.domains.access.service import AccessService


@strawberry.type
class AccessMutation:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_access_permission(self, info: strawberry.types.Info, input: AccessPermissionInput) -> AccessPermissionType:
        user = await require_access_manager(info)
        if not await AccessService.has_global_permission(user, "access.manage"):
            raise AuthorizationException("Global access.manage permission is required")
        values = asdict(input)
        expected = f"{values['domain']}.{values['resource']}.{values['action']}"
        if values["code"] not in {"*", expected} and not values["code"].endswith(".*"):
            raise ValidationException(f"Permission code must be '{expected}' or a wildcard")
        return permission_type(await AccessRepository.create_permission(values, user.id))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_access_role(self, info: strawberry.types.Info, input: AccessRoleInput) -> AccessRoleType:
        user = await require_access_manager(info)
        values = asdict(input); permission_uuids = values.pop("permission_uuids")
        global_manager = await AccessService.has_global_permission(user, "access.manage")
        if values["company_id"] is not None and values["company_id"] != user.company_id and not global_manager:
            raise AuthorizationException("Cannot manage roles from another company")
        if values["company_id"] is None:
            values["company_id"] = user.company_id
        result = await AccessRepository.create_role(values, permission_uuids, user.id)
        if result is None:
            raise ValidationException("One or more permission UUIDs are invalid")
        return role_type(*result)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def assign_access_role(self, info: strawberry.types.Info, input: AccessUserRoleInput) -> AccessUserRoleType:
        user = await require_access_manager(info)
        values = asdict(input); user_uuid = values.pop("user_uuid"); role_uuid = values.pop("role_uuid")
        global_manager = await AccessService.has_global_permission(user, "access.manage")
        if values["scope_type"].value == "GLOBAL" and not global_manager:
            raise AuthorizationException("Only a global manager can assign global roles")
        if values["company_id"] is not None and values["company_id"] != user.company_id and not global_manager:
            raise AuthorizationException("Cannot assign roles in another company")
        if values["company_id"] is None and values["scope_type"].value != "GLOBAL":
            values["company_id"] = user.company_id
        result = await AccessRepository.assign(values, user_uuid, role_uuid, user.id, None if global_manager else user.company_id)
        if result is None:
            raise ValidationException("Invalid user_uuid or role_uuid")
        return user_role_type(*result)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def revoke_access_role(self, info: strawberry.types.Info, record_uuid: uuid_lib.UUID) -> bool:
        user = await require_access_manager(info)
        global_manager = await AccessService.has_global_permission(user, "access.manage")
        return await AccessRepository.revoke(record_uuid, None if global_manager else user.company_id)
