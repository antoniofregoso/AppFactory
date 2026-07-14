from app.domains.system.repository.system_push_subscription_repository import (
    SystemPushSubscriptionRepository,
)


class SystemPushSubscriptionService:
    @staticmethod
    async def subscribe(user_id: int, endpoint: str, p256dh: str, auth: str, user_agent: str | None = None):
        return await SystemPushSubscriptionRepository.upsert(
            user_id, endpoint, p256dh, auth, user_agent
        )

    @staticmethod
    async def unsubscribe(endpoint: str) -> bool:
        return await SystemPushSubscriptionRepository.delete_by_endpoint(endpoint)

    @staticmethod
    async def get_by_user_id(user_id: int):
        return await SystemPushSubscriptionRepository.get_by_user_id(user_id)
