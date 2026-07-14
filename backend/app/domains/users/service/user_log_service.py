import uuid as uuid_lib
from datetime import datetime, timedelta, timezone

from app.core.config.settings import settings
from app.core.exceptions import ResourceNotFoundException
from app.domains.users.models.user_log import UserLog
from app.domains.users.repository.user_log_repository import UserLogRepository


class UserLogService:
    @staticmethod
    async def get_by_user_id(user_id: int, limit: int = 50):
        return await UserLogRepository.get_by_user_id(user_id, limit)

    @staticmethod
    async def get_by_uuid_and_user_id(log_uuid: uuid_lib.UUID, user_id: int):
        log = await UserLogRepository.get_by_uuid_and_user_id(log_uuid, user_id)
        if not log:
            raise ResourceNotFoundException(
                resource="UserLog",
                resource_id=str(log_uuid),
            )
        return log

    @staticmethod
    async def heartbeat(user_id: int):
        seen_at = datetime.now(timezone.utc)
        log = await UserLogRepository.get_open_by_user_id(user_id)
        if log is None:
            return await UserLogRepository.create(
                UserLog(
                    user_id=user_id,
                    start_date=seen_at,
                    last_seen_at=seen_at,
                )
            )
        touched = await UserLogRepository.touch(log.id, seen_at)
        if touched is None:
            raise ResourceNotFoundException(resource="UserLog", resource_id=str(log.id))
        return touched

    @staticmethod
    async def close_open_for_user(user_id: int):
        return await UserLogRepository.close_open_by_user_id(user_id)

    @staticmethod
    async def close_stale_logs(timeout_seconds: int | None = None) -> int:
        seconds = timeout_seconds or settings.USER_LOG_STALE_TIMEOUT_SECONDS
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        return await UserLogRepository.close_stale(cutoff)
