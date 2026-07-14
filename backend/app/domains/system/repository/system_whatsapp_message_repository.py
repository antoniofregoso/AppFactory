import uuid as uuid_lib

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database.session import db
from app.domains.system.models.system_whatsapp import SystemWhatsAppMessage


class SystemWhatsAppMessageRepository:
    @staticmethod
    async def create(message_data: dict):
        async with db.session() as session:
            message = SystemWhatsAppMessage(**message_data)
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return await SystemWhatsAppMessageRepository.get_by_uuid(message.uuid)

    @staticmethod
    async def get_all_by_whatsapp_id(whatsapp_id: int):
        async with db.session() as session:
            query = (
                select(SystemWhatsAppMessage)
                .where(SystemWhatsAppMessage.whatsapp_id == whatsapp_id)
                .options(selectinload(SystemWhatsAppMessage.template))
                .order_by(SystemWhatsAppMessage.date.desc())
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_by_uuid(message_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = (
                select(SystemWhatsAppMessage)
                .where(SystemWhatsAppMessage.uuid == message_uuid)
                .options(selectinload(SystemWhatsAppMessage.template))
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_external_message_id(external_message_id: str):
        async with db.session() as session:
            query = select(SystemWhatsAppMessage).where(
                SystemWhatsAppMessage.external_message_id == external_message_id
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def update(message_uuid: uuid_lib.UUID, message_data: dict):
        async with db.session() as session:
            query = select(SystemWhatsAppMessage).where(
                SystemWhatsAppMessage.uuid == message_uuid
            )
            result = await session.execute(query)
            message = result.scalar_one_or_none()
            if not message:
                return None

            for key, value in message_data.items():
                setattr(message, key, value)

            session.add(message)
            await session.commit()
            await session.refresh(message)
            return await SystemWhatsAppMessageRepository.get_by_uuid(message.uuid)
