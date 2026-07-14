import uuid as uuid_lib

from app.core.exceptions import ResourceNotFoundException
from app.domains.system.repository.system_model_repository import SystemModelRepository
from app.domains.system.repository.system_whatsapp_message_repository import (
    SystemWhatsAppMessageRepository,
)
from app.domains.system.repository.system_whatsapp_repository import (
    SystemWhatsAppRepository,
)
from app.domains.system.repository.system_whatsapp_template_repository import (
    SystemWhatsAppTemplateRepository,
)


class SystemWhatsAppMessageService:
    @staticmethod
    async def create(message_data: dict):
        whatsapp_uuid = message_data.pop("whatsapp_uuid")
        whatsapp = await SystemWhatsAppRepository.get_by_uuid(whatsapp_uuid)
        if not whatsapp:
            raise ResourceNotFoundException(
                resource="SystemWhatsApp", resource_id=str(whatsapp_uuid)
            )
        message_data["whatsapp_id"] = whatsapp.id

        template_uuid = message_data.pop("template_uuid", None)
        if template_uuid is not None:
            template = await SystemWhatsAppTemplateRepository.get_by_uuid(
                template_uuid
            )
            if not template:
                raise ResourceNotFoundException(
                    resource="SystemWhatsAppTemplate", resource_id=str(template_uuid)
                )
            message_data["template_id"] = template.id

        model_uuid = message_data.pop("model_uuid", None)
        if model_uuid is not None:
            model = await SystemModelRepository.get_by_uuid(model_uuid)
            if not model:
                raise ResourceNotFoundException(
                    resource="SystemModel", resource_id=str(model_uuid)
                )
            message_data["model_id"] = model.id

        return await SystemWhatsAppMessageRepository.create(message_data)

    @staticmethod
    async def get_all_by_whatsapp(whatsapp_uuid: uuid_lib.UUID):
        whatsapp = await SystemWhatsAppRepository.get_by_uuid(whatsapp_uuid)
        if not whatsapp:
            raise ResourceNotFoundException(
                resource="SystemWhatsApp", resource_id=str(whatsapp_uuid)
            )
        return await SystemWhatsAppMessageRepository.get_all_by_whatsapp_id(
            whatsapp.id
        )

    @staticmethod
    async def get_by_uuid(message_uuid: uuid_lib.UUID):
        message = await SystemWhatsAppMessageRepository.get_by_uuid(message_uuid)
        if not message:
            raise ResourceNotFoundException(
                resource="SystemWhatsAppMessage", resource_id=str(message_uuid)
            )
        return message

    @staticmethod
    async def update(message_uuid: uuid_lib.UUID, message_data: dict):
        message = await SystemWhatsAppMessageRepository.update(
            message_uuid, message_data
        )
        if not message:
            raise ResourceNotFoundException(
                resource="SystemWhatsAppMessage", resource_id=str(message_uuid)
            )
        return message
