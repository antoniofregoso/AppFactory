import uuid

from sqlalchemy import delete, select

from app.core.database.session import db
from app.domains.access.models import AccessPermission, AccessRole, AccessRolePermission, AccessUserRole
from app.domains.users.models import UserUser


class AccessRepository:
    @staticmethod
    async def permissions():
        async with db.session() as session:
            return list((await session.execute(select(AccessPermission).order_by(AccessPermission.code))).scalars())

    @staticmethod
    async def roles(company_id: int | None):
        async with db.session() as session:
            roles = list((await session.execute(select(AccessRole).where((AccessRole.company_id.is_(None)) | (AccessRole.company_id == company_id)).order_by(AccessRole.sequence, AccessRole.code))).scalars())
            links = (await session.execute(select(AccessRolePermission, AccessPermission).join(AccessPermission, AccessPermission.id == AccessRolePermission.permission_id))).all()
            permissions = {role.id: [] for role in roles}
            for link, permission in links:
                if link.role_id in permissions:
                    permissions[link.role_id].append(permission)
            return [(role, permissions[role.id]) for role in roles]

    @staticmethod
    async def create_permission(values: dict, actor_id: int):
        async with db.session() as session:
            record = AccessPermission(**values, create_by=actor_id, updated_by=actor_id)
            session.add(record); await session.commit(); await session.refresh(record)
            return record

    @staticmethod
    async def create_role(values: dict, permission_uuids: list[uuid.UUID], actor_id: int):
        async with db.session() as session:
            permissions = list((await session.execute(select(AccessPermission).where(AccessPermission.uuid.in_(permission_uuids)))).scalars())
            if len(permissions) != len(set(permission_uuids)):
                return None
            role = AccessRole(**values, create_by=actor_id, updated_by=actor_id)
            session.add(role); await session.flush()
            session.add_all([AccessRolePermission(role_id=role.id, permission_id=item.id) for item in permissions])
            await session.commit(); await session.refresh(role)
            return role, permissions

    @staticmethod
    async def assign(values: dict, user_uuid: uuid.UUID, role_uuid: uuid.UUID, actor_id: int, allowed_company_id: int | None = None):
        async with db.session() as session:
            user_query = select(UserUser).where(UserUser.uuid == user_uuid)
            role_query = select(AccessRole).where(AccessRole.uuid == role_uuid)
            if allowed_company_id is not None:
                user_query = user_query.where(UserUser.company_id == allowed_company_id)
                role_query = role_query.where((AccessRole.company_id.is_(None)) | (AccessRole.company_id == allowed_company_id))
            user = (await session.execute(user_query)).scalar_one_or_none()
            role = (await session.execute(role_query)).scalar_one_or_none()
            if user is None or role is None:
                return None
            assignment = AccessUserRole(**values, user_id=user.id, role_id=role.id, create_by=actor_id, updated_by=actor_id)
            session.add(assignment); await session.commit(); await session.refresh(assignment)
            return assignment, user.uuid, role.uuid

    @staticmethod
    async def user_roles(company_id: int | None):
        async with db.session() as session:
            rows = (await session.execute(select(AccessUserRole, UserUser.uuid, AccessRole.uuid).join(UserUser, UserUser.id == AccessUserRole.user_id).join(AccessRole, AccessRole.id == AccessUserRole.role_id).where((AccessUserRole.company_id.is_(None)) | (AccessUserRole.company_id == company_id)))).all()
            return list(rows)

    @staticmethod
    async def revoke(record_uuid: uuid.UUID, allowed_company_id: int | None = None) -> bool:
        async with db.session() as session:
            query = delete(AccessUserRole).where(AccessUserRole.uuid == record_uuid)
            if allowed_company_id is not None:
                query = query.where(AccessUserRole.company_id == allowed_company_id)
            result = await session.execute(query)
            await session.commit()
            return bool(result.rowcount)
