import uuid as uuid_lib

from app.core.exceptions import ResourceNotFoundException
from app.domains.system.repository.system_whatsapp_repository import (
    SystemWhatsAppRepository,
)
from app.domains.system.repository.system_whatsapp_template_repository import (
    SystemWhatsAppTemplateRepository,
)


class SystemWhatsAppTemplateService:
    @staticmethod
    async def create(template_data: dict):
        whatsapp_uuid = template_data.pop("whatsapp_uuid")
        whatsapp = await SystemWhatsAppRepository.get_by_uuid(whatsapp_uuid)
        if not whatsapp:
            raise ResourceNotFoundException(
                resource="SystemWhatsApp", resource_id=str(whatsapp_uuid)
            )
        template_data["whatsapp_id"] = whatsapp.id
        return await SystemWhatsAppTemplateRepository.create(template_data)

    @staticmethod
    async def get_all_by_whatsapp(whatsapp_uuid: uuid_lib.UUID):
        whatsapp = await SystemWhatsAppRepository.get_by_uuid(whatsapp_uuid)
        if not whatsapp:
            raise ResourceNotFoundException(
                resource="SystemWhatsApp", resource_id=str(whatsapp_uuid)
            )
        return await SystemWhatsAppTemplateRepository.get_all_by_whatsapp_id(
            whatsapp.id
        )

    @staticmethod
    async def get_by_uuid(template_uuid: uuid_lib.UUID):
        template = await SystemWhatsAppTemplateRepository.get_by_uuid(template_uuid)
        if not template:
            raise ResourceNotFoundException(
                resource="SystemWhatsAppTemplate", resource_id=str(template_uuid)
            )
        return template

    @staticmethod
    async def update(template_uuid: uuid_lib.UUID, template_data: dict):
        template = await SystemWhatsAppTemplateRepository.update(
            template_uuid, template_data
        )
        if not template:
            raise ResourceNotFoundException(
                resource="SystemWhatsAppTemplate", resource_id=str(template_uuid)
            )
        return template

    @staticmethod
    async def delete(template_uuid: uuid_lib.UUID):
        deleted = await SystemWhatsAppTemplateRepository.delete(template_uuid)
        if not deleted:
            raise ResourceNotFoundException(
                resource="SystemWhatsAppTemplate", resource_id=str(template_uuid)
            )
        return True
