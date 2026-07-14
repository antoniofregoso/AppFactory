from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database.session import db
from app.domains.users.models.user_session import UserSession


class UserSessionRepository:
    @staticmethod
    async def create(session_token: UserSession) -> UserSession:
        async with db.session() as session:
            session.add(session_token)
            await session.commit()
            await session.refresh(session_token)
            return session_token

    @staticmethod
    async def get_active_by_refresh_token_hash(
        refresh_token_hash: str,
    ) -> UserSession | None:
        async with db.session() as session:
            now = datetime.now(timezone.utc)
            query = select(UserSession).where(
                UserSession.refresh_token_hash == refresh_token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
                UserSession.absolute_expires_at > now,
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_refresh_token_hash(refresh_token_hash: str) -> UserSession | None:
        async with db.session() as session:
            query = select(UserSession).where(
                UserSession.refresh_token_hash == refresh_token_hash,
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def revoke(session_token: UserSession) -> UserSession:
        async with db.session() as session:
            stored_session = await session.get(UserSession, session_token.id)
            if stored_session is None:
                return session_token
            stored_session.revoked_at = datetime.now(timezone.utc)
            session.add(stored_session)
            await session.commit()
            await session.refresh(stored_session)
            return stored_session

    @staticmethod
    async def revoke_by_refresh_token_hash(refresh_token_hash: str) -> bool:
        async with db.session() as session:
            query = select(UserSession).where(
                UserSession.refresh_token_hash == refresh_token_hash,
                UserSession.revoked_at.is_(None),
            )
            result = await session.execute(query)
            stored_session = result.scalar_one_or_none()
            if stored_session is None:
                return False
            stored_session.revoked_at = datetime.now(timezone.utc)
            session.add(stored_session)
            await session.commit()
            return True

    @staticmethod
    async def revoke_all_by_user_id(user_id: int) -> int:
        async with db.session() as session:
            query = select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            result = await session.execute(query)
            sessions = result.scalars().all()
            revoked_at = datetime.now(timezone.utc)
            for stored_session in sessions:
                stored_session.revoked_at = revoked_at
                session.add(stored_session)
            await session.commit()
            return len(sessions)
