import uuid as uuid_lib
from datetime import datetime

from sqlalchemy import select

from app.core.database.session import db
from app.domains.users.models.user_log import UserLog, UserLogStatus
from app.domains.users.models.user_user import UserType, UserUser


class UserLogRepository:
    @staticmethod
    async def get_human_activity_between(
        start: datetime,
        end: datetime,
        company_id: int | None,
    ) -> list[UserLog]:
        async with db.session() as session:
            query = (
                select(UserLog)
                .join(UserUser, UserUser.id == UserLog.user_id)
                .where(
                    UserUser.user_type == UserType.HUMAN,
                    UserLog.start_date < end,
                    UserLog.last_seen_at.is_not(None),
                    UserLog.last_seen_at >= start,
                )
                .order_by(UserLog.start_date.asc())
            )
            if company_id is not None:
                query = query.where(UserUser.company_id == company_id)
            result = await session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    async def get_by_user_id(user_id: int, limit: int = 50):
        async with db.session() as session:
            query = (
                select(UserLog)
                .where(UserLog.user_id == user_id)
                .order_by(UserLog.start_date.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_by_uuid_and_user_id(log_uuid: uuid_lib.UUID, user_id: int):
        async with db.session() as session:
            query = select(UserLog).where(
                UserLog.uuid == log_uuid,
                UserLog.user_id == user_id,
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_open_by_user_id(user_id: int) -> UserLog | None:
        async with db.session() as session:
            query = (
                select(UserLog)
                .where(
                    UserLog.user_id == user_id,
                    UserLog.status == UserLogStatus.ONLINE,
                    UserLog.end_date.is_(None),
                )
                .order_by(UserLog.start_date.desc())
                .limit(1)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def create(log: UserLog) -> UserLog:
        async with db.session() as session:
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log

    @staticmethod
    async def touch(log_id: int, seen_at: datetime) -> UserLog | None:
        async with db.session() as session:
            log = await session.get(UserLog, log_id)
            if log is None:
                return None
            log.last_seen_at = seen_at
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log

    @staticmethod
    async def close_open_by_user_id(user_id: int) -> UserLog | None:
        async with db.session() as session:
            query = select(UserLog).where(
                UserLog.user_id == user_id,
                UserLog.status == UserLogStatus.ONLINE,
                UserLog.end_date.is_(None),
            )
            result = await session.execute(query)
            logs = result.scalars().all()
            if not logs:
                return None
            for log in logs:
                log.status = UserLogStatus.OFFLINE
                log.end_date = log.last_seen_at
                session.add(log)
            await session.commit()
            log = logs[0]
            await session.refresh(log)
            return log

    @staticmethod
    async def close_stale(cutoff: datetime) -> int:
        async with db.session() as session:
            query = select(UserLog).where(
                UserLog.status == UserLogStatus.ONLINE,
                UserLog.end_date.is_(None),
                UserLog.last_seen_at < cutoff,
            )
            result = await session.execute(query)
            stale_logs = result.scalars().all()
            for log in stale_logs:
                log.status = UserLogStatus.OFFLINE
                log.end_date = log.last_seen_at
                session.add(log)
            await session.commit()
            return len(stale_logs)
