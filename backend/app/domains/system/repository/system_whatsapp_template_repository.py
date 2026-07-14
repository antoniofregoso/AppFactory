import uuid as uuid_lib

from sqlalchemy import select

from app.core.database.session import db
from app.domains.system.models.system_whatsapp import SystemWhatsAppTemplate


class SystemWhatsAppTemplateRepository:
    @staticmethod
    async def create(template_data: dict):
        async with db.session() as session:
            template = SystemWhatsAppTemplate(**template_data)
            session.add(template)
            await session.commit()
            await session.refresh(template)
            return template

    @staticmethod
    async def get_all_by_whatsapp_id(whatsapp_id: int):
        async with db.session() as session:
            query = (
                select(SystemWhatsAppTemplate)
                .where(SystemWhatsAppTemplate.whatsapp_id == whatsapp_id)
                .order_by(SystemWhatsAppTemplate.name)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_by_uuid(template_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = select(SystemWhatsAppTemplate).where(
                SystemWhatsAppTemplate.uuid == template_uuid
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def update(template_uuid: uuid_lib.UUID, template_data: dict):
        async with db.session() as session:
            query = select(SystemWhatsAppTemplate).where(
                SystemWhatsAppTemplate.uuid == template_uuid
            )
            result = await session.execute(query)
            template = result.scalar_one_or_none()
            if not template:
                return None

            for key, value in template_data.items():
                setattr(template, key, value)

            session.add(template)
            await session.commit()
            await session.refresh(template)
            return template

    @staticmethod
    async def delete(template_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = select(SystemWhatsAppTemplate).where(
                SystemWhatsAppTemplate.uuid == template_uuid
            )
            result = await session.execute(query)
            template = result.scalar_one_or_none()
            if not template:
                return False

            await session.delete(template)
            await session.commit()
            return True
