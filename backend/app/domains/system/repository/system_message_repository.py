import uuid as uuid_lib

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.database.session import db
from app.domains.system.models.system_message import SystemMessage, MessageStatus
from app.domains.system.models.system_message_user_rel import SystemMessageUserRel
from app.domains.users.models.user_user import UserUser


class SystemMessageRepository:
    @staticmethod
    async def create(message_data: dict):
        from_user_uuid = message_data.pop("from_user_uuid", None)
        to_user_uuids = message_data.pop("to_user_uuids", [])

        async with db.session() as session:
            message = SystemMessage(**message_data)

            if from_user_uuid:
                from_user = await SystemMessageRepository._get_user_by_uuid(
                    session, from_user_uuid
                )
                if from_user:
                    message.from_user_id = from_user.id

            if to_user_uuids:
                message.to_users = await SystemMessageRepository._get_users_by_uuid(
                    session, to_user_uuids
                )

            session.add(message)
            await session.commit()
            await session.refresh(message)
            return await SystemMessageRepository.get_by_uuid(message.uuid)

    @staticmethod
    async def get_all():
        async with db.session() as session:
            query = (
                select(SystemMessage)
                .options(
                    selectinload(SystemMessage.from_user),
                    selectinload(SystemMessage.to_users),
                )
                .order_by(SystemMessage.date.desc(), SystemMessage.created_at.desc())
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_by_uuid(message_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = (
                select(SystemMessage)
                .where(SystemMessage.uuid == message_uuid)
                .options(
                    selectinload(SystemMessage.from_user),
                    selectinload(SystemMessage.to_users),
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def count_unread_by_user_id(user_id: int) -> int:
        async with db.session() as session:
            query = (
                select(func.count(SystemMessage.id))
                .join(
                    SystemMessageUserRel,
                    SystemMessageUserRel.message_id == SystemMessage.id,
                )
                .where(
                    SystemMessageUserRel.user_id == user_id,
                    SystemMessage.status != MessageStatus.read,
                )
            )
            result = await session.execute(query)
            return result.scalar_one()

    @staticmethod
    async def update(message_uuid: uuid_lib.UUID, message_data: dict):
        from_user_uuid = message_data.pop("from_user_uuid", None)
        to_user_uuids = message_data.pop("to_user_uuids", None)

        async with db.session() as session:
            query = (
                select(SystemMessage)
                .where(SystemMessage.uuid == message_uuid)
                .options(
                    selectinload(SystemMessage.from_user),
                    selectinload(SystemMessage.to_users),
                )
            )
            result = await session.execute(query)
            message = result.scalar_one_or_none()
            if not message:
                return None

            for key, value in message_data.items():
                setattr(message, key, value)

            if from_user_uuid is not None:
                from_user = await SystemMessageRepository._get_user_by_uuid(
                    session, from_user_uuid
                )
                message.from_user_id = from_user.id if from_user else None

            if to_user_uuids is not None:
                message.to_users = await SystemMessageRepository._get_users_by_uuid(
                    session, to_user_uuids
                )

            session.add(message)
            await session.commit()
            await session.refresh(message)
            return await SystemMessageRepository.get_by_uuid(message.uuid)

    @staticmethod
    async def delete(message_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = (
                select(SystemMessage)
                .where(SystemMessage.uuid == message_uuid)
                .options(selectinload(SystemMessage.to_users))
            )
            result = await session.execute(query)
            message = result.scalar_one_or_none()
            if not message:
                return False

            await session.delete(message)
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
