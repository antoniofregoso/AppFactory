import uuid as uuid_lib

from app.core.exceptions import ResourceNotFoundException
from app.domains.system.repository.system_notification_repository import (
    SystemNotificationRepository,
)
from app.domains.system.service.web_push_service import WebPushService


class SystemNotificationService:
    @staticmethod
    async def create(notification_data: dict):
        notification = await SystemNotificationRepository.create(notification_data)
        await SystemNotificationService._send_web_push(notification)
        return notification

    @staticmethod
    async def _send_web_push(notification):
        recipient_ids = {user.id for user in notification.users}
        if notification.user:
            recipient_ids.add(notification.user.id)

        title = notification.get_title("es", "en")
        body = notification.get_message("es", "en")
        for user_id in recipient_ids:
            await WebPushService.send_to_user(user_id, title, body)

    @staticmethod
    async def get_all():
        return await SystemNotificationRepository.get_all()

    @staticmethod
    async def get_by_uuid(notification_uuid: uuid_lib.UUID):
        notification = await SystemNotificationRepository.get_by_uuid(notification_uuid)
        if not notification:
            raise ResourceNotFoundException(
                resource="SystemNotification", resource_id=str(notification_uuid)
            )
        return notification

    @staticmethod
    async def get_recent_by_user_id(user_id: int, limit: int = 30):
        return await SystemNotificationRepository.get_recent_by_user_id(user_id, limit)

    @staticmethod
    async def get_existing_dedupe_keys(keys: list[str]):
        return await SystemNotificationRepository.get_existing_dedupe_keys(keys)

    @staticmethod
    async def count_unread_by_user_id(user_id: int):
        return await SystemNotificationRepository.count_unread_by_user_id(user_id)

    @staticmethod
    async def update(notification_uuid: uuid_lib.UUID, notification_data: dict):
        notification = await SystemNotificationRepository.update(
            notification_uuid, notification_data
        )
        if not notification:
            raise ResourceNotFoundException(
                resource="SystemNotification", resource_id=str(notification_uuid)
            )
        return notification

    @staticmethod
    async def delete(notification_uuid: uuid_lib.UUID):
        deleted = await SystemNotificationRepository.delete(notification_uuid)
        if not deleted:
            raise ResourceNotFoundException(
                resource="SystemNotification", resource_id=str(notification_uuid)
            )
        return True
