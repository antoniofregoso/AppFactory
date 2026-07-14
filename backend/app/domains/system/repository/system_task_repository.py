import uuid as uuid_lib

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.core.database.session import db
from app.domains.system.models.system_task import SystemTask, TaskStatus
from app.domains.users.models.user_user import UserUser


class SystemTaskRepository:
    @staticmethod
    async def create(task_data: dict):
        user_uuid = task_data.pop("user_uuid", None)

        async with db.session() as session:
            task = SystemTask(**task_data)
            if user_uuid:
                user = await SystemTaskRepository._get_user_by_uuid(session, user_uuid)
                if user:
                    task.user_id = user.id

            session.add(task)
            await session.commit()
            await session.refresh(task)
            return await SystemTaskRepository.get_by_uuid(task.uuid)

    @staticmethod
    async def get_all():
        async with db.session() as session:
            query = (
                select(SystemTask)
                .options(selectinload(SystemTask.user))
                .order_by(SystemTask.sequence, SystemTask.created_at.desc())
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_by_uuid(task_uuid: uuid_lib.UUID):
        async with db.session() as session:
            query = (
                select(SystemTask)
                .where(SystemTask.uuid == task_uuid)
                .options(selectinload(SystemTask.user))
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_pending_with_reminder_dates():
        async with db.session() as session:
            query = (
                select(SystemTask)
                .where(
                    SystemTask.user_id.is_not(None),
                    SystemTask.status.in_(
                        [TaskStatus.pending, TaskStatus.in_progress]
                    ),
                    or_(
                        SystemTask.date_assign.is_not(None),
                        SystemTask.date_due.is_not(None),
                    ),
                )
                .options(selectinload(SystemTask.user))
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def update(task_uuid: uuid_lib.UUID, task_data: dict):
        user_uuid_supplied = "user_uuid" in task_data
        user_uuid = task_data.pop("user_uuid", None)

        async with db.session() as session:
            query = (
                select(SystemTask)
                .where(SystemTask.uuid == task_uuid)
                .options(selectinload(SystemTask.user))
            )
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            if not task:
                return None

            for key, value in task_data.items():
                setattr(task, key, value)

            if user_uuid_supplied:
                user = (
                    await SystemTaskRepository._get_user_by_uuid(session, user_uuid)
                    if user_uuid
                    else None
                )
                task.user_id = user.id if user else None

            session.add(task)
            await session.commit()
            await session.refresh(task)
            return await SystemTaskRepository.get_by_uuid(task.uuid)

    @staticmethod
    async def delete(task_uuid: uuid_lib.UUID):
        async with db.session() as session:
            result = await session.execute(
                select(SystemTask).where(SystemTask.uuid == task_uuid)
            )
            task = result.scalar_one_or_none()
            if not task:
                return False

            await session.delete(task)
            await session.commit()
            return True

    @staticmethod
    async def _get_user_by_uuid(session, user_uuid: uuid_lib.UUID):
        result = await session.execute(
            select(UserUser).where(UserUser.uuid == user_uuid)
        )
        return result.scalar_one_or_none()
