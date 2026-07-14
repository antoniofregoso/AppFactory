import uuid as uuid_lib

from app.core.exceptions import ResourceNotFoundException
from app.domains.system.repository.system_message_repository import SystemMessageRepository


class SystemMessageService:
    @staticmethod
    async def create(message_data: dict):
        return await SystemMessageRepository.create(message_data)

    @staticmethod
    async def get_all():
        return await SystemMessageRepository.get_all()

    @staticmethod
    async def get_by_uuid(message_uuid: uuid_lib.UUID):
        message = await SystemMessageRepository.get_by_uuid(message_uuid)
        if not message:
            raise ResourceNotFoundException(
                resource="SystemMessage", resource_id=str(message_uuid)
            )
        return message

    @staticmethod
    async def count_unread_by_user_id(user_id: int):
        return await SystemMessageRepository.count_unread_by_user_id(user_id)

    @staticmethod
    async def update(message_uuid: uuid_lib.UUID, message_data: dict):
        message = await SystemMessageRepository.update(message_uuid, message_data)
        if not message:
            raise ResourceNotFoundException(
                resource="SystemMessage", resource_id=str(message_uuid)
            )
        return message

    @staticmethod
    async def delete(message_uuid: uuid_lib.UUID):
        deleted = await SystemMessageRepository.delete(message_uuid)
        if not deleted:
            raise ResourceNotFoundException(
                resource="SystemMessage", resource_id=str(message_uuid)
            )
        return True
