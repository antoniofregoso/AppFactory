import uuid as uuid_lib

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.core.database.session import db
from app.domains.system.models.system_notification import (
    SystemNotification,
    NotificationStatus,
)
from app.domains.system.models.system_notification_user_rel import SystemNotificationUserRel
from app.domains.users.models.user_user import UserUser


class SystemNotificationRepository:
    @staticmethod
    async def create(notification_data: dict):
        user_uuid = notification_data.pop("user_uuid", None)
        user_uuids = notification_data.pop("user_uuids", [])

        async with db.session() as session:
            notification = SystemNotification(**notification_data)

            if user_uuid:
                user = await SystemNotificationRepository._get_user_by_uuid(
                    session, user_uuid
                )
                if user:
                    notification.user_id = user.id

            if user_uuids:
                notification.users = await SystemNotificationRepository._get_users_by_uuid(
                    session, user_uuids
                )

            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            return await SystemNotificationRepository.get_by_uuid(notification.uuid)

    @staticmethod
    async def get_all():
        async with db.session() as session:
            query = (
                select(SystemNotification)
                .options(
                    selectinload(SystemNotification.user),
                    selectinload(SystemNotification.users),
                )
                .order_by(
                    SystemNotification.date.desc(),
                    SystemNotification.created_at.desc(),
                )
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_by_uuid(notification_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = (
                select(SystemNotification)
                .where(SystemNotification.uuid == notification_uuid)
                .options(
                    selectinload(SystemNotification.user),
                    selectinload(SystemNotification.users),
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_recent_by_user_id(user_id: int, limit: int = 30):
        async with db.session() as session:
            query = (
                select(SystemNotification)
                .outerjoin(
                    SystemNotificationUserRel,
                    SystemNotificationUserRel.notification_id == SystemNotification.id,
                )
                .where(
                    or_(
                        SystemNotification.user_id == user_id,
                        SystemNotificationUserRel.user_id == user_id,
                    )
                )
                .options(
                    selectinload(SystemNotification.user),
                    selectinload(SystemNotification.users),
                )
                .order_by(
                    SystemNotification.date.desc(),
                    SystemNotification.created_at.desc(),
                )
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().unique().all()

    @staticmethod
    async def get_existing_dedupe_keys(keys: list[str]) -> set[str]:
        if not keys:
            return set()
        async with db.session() as session:
            query = select(SystemNotification.dedupe_key).where(
                SystemNotification.dedupe_key.in_(keys)
            )
            result = await session.execute(query)
            return set(result.scalars().all())

    @staticmethod
    async def count_unread_by_user_id(user_id: int) -> int:
        async with db.session() as session:
            query = (
                select(func.count(func.distinct(SystemNotification.id)))
                .outerjoin(
                    SystemNotificationUserRel,
                    SystemNotificationUserRel.notification_id == SystemNotification.id,
                )
                .where(
                    or_(
                        SystemNotification.user_id == user_id,
                        SystemNotificationUserRel.user_id == user_id,
                    ),
                    SystemNotification.status != NotificationStatus.read,
                )
            )
            result = await session.execute(query)
            return result.scalar_one()

    @staticmethod
    async def update(notification_uuid: uuid_lib.UUID, notification_data: dict):
        user_uuid = notification_data.pop("user_uuid", None)
        user_uuids = notification_data.pop("user_uuids", None)

        async with db.session() as session:
            query = (
                select(SystemNotification)
                .where(SystemNotification.uuid == notification_uuid)
                .options(
                    selectinload(SystemNotification.user),
                    selectinload(SystemNotification.users),
                )
            )
            result = await session.execute(query)
            notification = result.scalar_one_or_none()
            if not notification:
                return None

            for key, value in notification_data.items():
                setattr(notification, key, value)

            if user_uuid is not None:
                user = await SystemNotificationRepository._get_user_by_uuid(
                    session, user_uuid
                )
                notification.user_id = user.id if user else None

            if user_uuids is not None:
                notification.users = await SystemNotificationRepository._get_users_by_uuid(
                    session, user_uuids
                )

            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            return await SystemNotificationRepository.get_by_uuid(notification.uuid)

    @staticmethod
    async def delete(notification_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = (
                select(SystemNotification)
                .where(SystemNotification.uuid == notification_uuid)
                .options(selectinload(SystemNotification.users))
            )
            result = await session.execute(query)
            notification = result.scalar_one_or_none()
            if not notification:
                return False

            await session.delete(notification)
            await session.commit()
            return True

    @staticmethod
    async def _get_user_by_uuid(session, user_uuid: uuid_lib.UUID):
        query = select(UserUser).where(UserUser.uuid == user_uuid)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_users_by_uuid(session, user_uuids: list[uuid_lib.UUID]):
        query = select(UserUser).where(UserUser.uuid.in_(user_uuids))
        result = await session.execute(query)
        return result.scalars().all()
