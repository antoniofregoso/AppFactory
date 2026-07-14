import asyncio
import json

from pywebpush import WebPushException, webpush

from app.core.config.settings import settings
from app.core.logging import get_logger
from app.domains.system.service.system_push_subscription_service import (
    SystemPushSubscriptionService,
)

logger = get_logger(__name__)

# Push endpoints answer with these when a subscription no longer exists on
# the browser/OS side (user revoked permission, uninstalled, etc).
_EXPIRED_STATUS_CODES = {404, 410}


def _send_one(subscription, payload: str) -> None:
    webpush(
        subscription_info={
            "endpoint": subscription.endpoint,
            "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
        },
        data=payload,
        vapid_private_key=settings.VAPID_PRIVATE_KEY,
        vapid_claims={"sub": settings.VAPID_SUBJECT},
    )


class WebPushService:
    """Sends browser push notifications so users see a native popup even
    when the app tab/window is closed. Best-effort: failures never bubble
    up to the caller creating the underlying SystemNotification."""

    @staticmethod
    async def send_to_user(user_id: int, title: str, body: str, url: str = "/dashboard"):
        if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
            return

        subscriptions = await SystemPushSubscriptionService.get_by_user_id(user_id)
        if not subscriptions:
            return

        payload = json.dumps({"title": title, "body": body, "url": url})

        for subscription in subscriptions:
            try:
                await asyncio.to_thread(_send_one, subscription, payload)
            except WebPushException as exc:
                status_code = getattr(exc.response, "status_code", None)
                if status_code in _EXPIRED_STATUS_CODES:
                    await SystemPushSubscriptionService.unsubscribe(subscription.endpoint)
                else:
                    logger.warning("Web push delivery failed: %s", exc.message)
            except Exception as exc:
                logger.exception("Unexpected error sending web push: %s", exc)
