import uuid as uuid_lib
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domains.users.models.user_user import UserUser
from app.core.database.session import db


class UserRepository:

    @staticmethod
    async def create(user: UserUser):
        async with db.session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def get_all():
        async with db.session() as session:
            query = select(UserUser)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_user_by_uuid(user_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = select(UserUser).where(UserUser.uuid == user_uuid)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(user_id: int):
        async with db.session() as session:
            return await session.get(UserUser, user_id)

    @staticmethod
    async def update(user_uuid: uuid_lib.UUID, user_data: dict):
        async with db.session() as session:
            query = select(UserUser).where(UserUser.uuid == user_uuid)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                for key, value in user_data.items():
                    setattr(user, key, value)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
            return None

    @staticmethod
    async def delete(user_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = select(UserUser).where(UserUser.uuid == user_uuid)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                await session.delete(user)
                await session.commit()
                return True
            return False

    @staticmethod
    async def get_by_email(email: str):
        async with db.session() as session:
            query = (
                select(UserUser)
                .where(UserUser.email == email)
                .options(selectinload(UserUser.lang))
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
