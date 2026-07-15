from datetime import date
from uuid import UUID

from sqlalchemy import select

from app.core.database.session import db
from app.core.exceptions import AuthorizationException
from app.domains.access.models import AccessPermission, AccessRole, AccessRolePermission, AccessScopeType, AccessUserRole


class AccessService:
    """Evaluates generic RBAC grants. Permission codes support hierarchical wildcards."""

    @staticmethod
    def _matches(grant: str, requested: str) -> bool:
        if grant == "*" or grant == requested:
            return True
        grant_parts = grant.split(".")
        requested_parts = requested.split(".")
        return bool(grant_parts and grant_parts[-1] == "*" and requested_parts[:len(grant_parts)-1] == grant_parts[:-1])

    @staticmethod
    async def grants(user_id: int) -> list[tuple[AccessUserRole, str]]:
        today = date.today()
        async with db.session() as session:
            query = (
                select(AccessUserRole, AccessPermission.code)
                .join(AccessRole, AccessRole.id == AccessUserRole.role_id)
                .join(AccessRolePermission, AccessRolePermission.role_id == AccessRole.id)
                .join(AccessPermission, AccessPermission.id == AccessRolePermission.permission_id)
                .where(AccessUserRole.user_id == user_id, AccessUserRole.active.is_(True),
                       AccessRole.active.is_(True), AccessPermission.active.is_(True),
                       (AccessUserRole.date_start.is_(None) | (AccessUserRole.date_start <= today)),
                       (AccessUserRole.date_end.is_(None) | (AccessUserRole.date_end >= today)))
            )
            return list((await session.execute(query)).all())

    @classmethod
    async def permissions(cls, user_id: int) -> list[str]:
        return sorted({code for _, code in await cls.grants(user_id)})

    @classmethod
    async def has_global_permission(cls, user, permission: str) -> bool:
        return any(
            assignment.scope_type == AccessScopeType.GLOBAL
            and cls._matches(code, permission)
            for assignment, code in await cls.grants(user.id)
        )

    @classmethod
    async def has_permission(cls, user, permission: str, *, company_id: int | None = None,
                             scope_chain: list[tuple[str, UUID]] | None = None) -> bool:
        for assignment, code in await cls.grants(user.id):
            if not cls._matches(code, permission):
                continue
            if assignment.scope_type == AccessScopeType.GLOBAL:
                return True
            target_company = company_id if company_id is not None else user.company_id
            if assignment.scope_type == AccessScopeType.COMPANY and assignment.company_id == target_company:
                return True
            if assignment.scope_type in {AccessScopeType.MODEL, AccessScopeType.RECORD}:
                if any(model == assignment.scope_model and (assignment.scope_record_uuid is None or record_uuid == assignment.scope_record_uuid)
                       for model, record_uuid in (scope_chain or [])):
                    return True
        return False

    @classmethod
    async def require(cls, user, permission: str, **scope) -> None:
        if not await cls.has_permission(user, permission, **scope):
            raise AuthorizationException(f"Permission required: {permission}")
