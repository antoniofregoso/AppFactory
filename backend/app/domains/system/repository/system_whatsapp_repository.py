import uuid as uuid_lib

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database.session import db
from app.domains.system.models.system_whatsapp import SystemWhatsApp


class SystemWhatsAppRepository:
    @staticmethod
    async def create(whatsapp_data: dict):
        async with db.session() as session:
            whatsapp = SystemWhatsApp(**whatsapp_data)
            session.add(whatsapp)
            await session.commit()
            await session.refresh(whatsapp)
            return await SystemWhatsAppRepository.get_by_uuid(whatsapp.uuid)

    @staticmethod
    async def get_all(company_id: int | None = None):
        async with db.session() as session:
            query = select(SystemWhatsApp).options(
                selectinload(SystemWhatsApp.company)
            )
            if company_id is not None:
                query = query.where(SystemWhatsApp.company_id == company_id)
            query = query.order_by(SystemWhatsApp.name)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_by_uuid(whatsapp_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = (
                select(SystemWhatsApp)
                .where(SystemWhatsApp.uuid == whatsapp_uuid)
                .options(selectinload(SystemWhatsApp.company))
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(whatsapp_id: int):
        async with db.session() as session:
            query = (
                select(SystemWhatsApp)
                .where(SystemWhatsApp.id == whatsapp_id)
                .options(selectinload(SystemWhatsApp.company))
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def update(whatsapp_uuid: uuid_lib.UUID, whatsapp_data: dict):
        async with db.session() as session:
            query = select(SystemWhatsApp).where(
                SystemWhatsApp.uuid == whatsapp_uuid
            )
            result = await session.execute(query)
            whatsapp = result.scalar_one_or_none()
            if not whatsapp:
                return None

            for key, value in whatsapp_data.items():
                setattr(whatsapp, key, value)

            session.add(whatsapp)
            await session.commit()
            await session.refresh(whatsapp)
            return await SystemWhatsAppRepository.get_by_uuid(whatsapp.uuid)

    @staticmethod
    async def delete(whatsapp_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = select(SystemWhatsApp).where(
                SystemWhatsApp.uuid == whatsapp_uuid
            )
            result = await session.execute(query)
            whatsapp = result.scalar_one_or_none()
            if not whatsapp:
                return False

            await session.delete(whatsapp)
            await session.commit()
            return True
