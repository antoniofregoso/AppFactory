import uuid as uuid_lib

from app.core.exceptions import ResourceNotFoundException
from app.domains.system.repository.system_task_repository import SystemTaskRepository


class SystemTaskService:
    @staticmethod
    async def create(task_data: dict):
        return await SystemTaskRepository.create(task_data)

    @staticmethod
    async def get_all():
        return await SystemTaskRepository.get_all()

    @staticmethod
    async def get_by_uuid(task_uuid: uuid_lib.UUID):
        task = await SystemTaskRepository.get_by_uuid(task_uuid)
        if not task:
            raise ResourceNotFoundException(
                resource="SystemTask", resource_id=str(task_uuid)
            )
        return task

    @staticmethod
    async def get_pending_with_reminder_dates():
        return await SystemTaskRepository.get_pending_with_reminder_dates()

    @staticmethod
    async def update(task_uuid: uuid_lib.UUID, task_data: dict):
        task = await SystemTaskRepository.update(task_uuid, task_data)
        if not task:
            raise ResourceNotFoundException(
                resource="SystemTask", resource_id=str(task_uuid)
            )
        return task

    @staticmethod
    async def delete(task_uuid: uuid_lib.UUID):
        deleted = await SystemTaskRepository.delete(task_uuid)
        if not deleted:
            raise ResourceNotFoundException(
                resource="SystemTask", resource_id=str(task_uuid)
            )
        return True
