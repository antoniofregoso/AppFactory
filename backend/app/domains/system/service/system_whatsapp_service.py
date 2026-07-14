import uuid as uuid_lib

from app.core.exceptions import ResourceNotFoundException
from app.domains.system.repository.system_whatsapp_repository import (
    SystemWhatsAppRepository,
)


class SystemWhatsAppService:
    @staticmethod
    async def create(whatsapp_data: dict):
        return await SystemWhatsAppRepository.create(whatsapp_data)

    @staticmethod
    async def get_all(company_id: int | None = None):
        return await SystemWhatsAppRepository.get_all(company_id)

    @staticmethod
    async def get_by_uuid(whatsapp_uuid: uuid_lib.UUID):
        whatsapp = await SystemWhatsAppRepository.get_by_uuid(whatsapp_uuid)
        if not whatsapp:
            raise ResourceNotFoundException(
                resource="SystemWhatsApp", resource_id=str(whatsapp_uuid)
            )
        return whatsapp

    @staticmethod
    async def get_by_id(whatsapp_id: int):
        whatsapp = await SystemWhatsAppRepository.get_by_id(whatsapp_id)
        if not whatsapp:
            raise ResourceNotFoundException(
                resource="SystemWhatsApp", resource_id=str(whatsapp_id)
            )
        return whatsapp

    @staticmethod
    async def update(whatsapp_uuid: uuid_lib.UUID, whatsapp_data: dict):
        whatsapp = await SystemWhatsAppRepository.update(whatsapp_uuid, whatsapp_data)
        if not whatsapp:
            raise ResourceNotFoundException(
                resource="SystemWhatsApp", resource_id=str(whatsapp_uuid)
            )
        return whatsapp

    @staticmethod
    async def delete(whatsapp_uuid: uuid_lib.UUID):
        deleted = await SystemWhatsAppRepository.delete(whatsapp_uuid)
        if not deleted:
            raise ResourceNotFoundException(
                resource="SystemWhatsApp", resource_id=str(whatsapp_uuid)
            )
        return True
