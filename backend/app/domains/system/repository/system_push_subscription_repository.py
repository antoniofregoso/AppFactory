from sqlalchemy import select

from app.core.database.session import db
from app.domains.system.models.system_push_subscription import SystemPushSubscription


class SystemPushSubscriptionRepository:
    @staticmethod
    async def upsert(user_id: int, endpoint: str, p256dh: str, auth: str, user_agent: str | None):
        async with db.session() as session:
            query = select(SystemPushSubscription).where(
                SystemPushSubscription.endpoint == endpoint
            )
            result = await session.execute(query)
            subscription = result.scalar_one_or_none()

            if subscription:
                subscription.user_id = user_id
                subscription.p256dh = p256dh
                subscription.auth = auth
                subscription.user_agent = user_agent
            else:
                subscription = SystemPushSubscription(
                    user_id=user_id,
                    endpoint=endpoint,
                    p256dh=p256dh,
                    auth=auth,
                    user_agent=user_agent,
                )

            session.add(subscription)
            await session.commit()
            await session.refresh(subscription)
            return subscription

    @staticmethod
    async def delete_by_endpoint(endpoint: str) -> bool:
        async with db.session() as session:
            query = select(SystemPushSubscription).where(
                SystemPushSubscription.endpoint == endpoint
            )
            result = await session.execute(query)
            subscription = result.scalar_one_or_none()
            if not subscription:
                return False

            await session.delete(subscription)
            await session.commit()
            return True

    @staticmethod
    async def get_by_user_id(user_id: int):
        async with db.session() as session:
            query = select(SystemPushSubscription).where(
                SystemPushSubscription.user_id == user_id
            )
            result = await session.execute(query)
            return result.scalars().all()
