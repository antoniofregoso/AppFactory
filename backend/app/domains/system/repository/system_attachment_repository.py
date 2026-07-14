import uuid as uuid_lib

from sqlalchemy import func, select

from app.core.database.session import db
from app.domains.system.models.system_attachment import SystemAttachment
from app.domains.users.models.user_user import UserUser


class SystemAttachmentRepository:
    @staticmethod
    async def create(attachment: SystemAttachment) -> SystemAttachment:
        async with db.session() as session:
            session.add(attachment)
            await session.commit()
            await session.refresh(attachment)
            return attachment

    @staticmethod
    async def get_by_uuid(
        attachment_uuid: uuid_lib.UUID,
        company_id: int | None,
    ) -> SystemAttachment | None:
        async with db.session() as session:
            query = select(SystemAttachment).where(
                SystemAttachment.uuid == attachment_uuid,
                SystemAttachment.company_id == company_id,
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_record(
        model_id: int,
        record_uuid: uuid_lib.UUID,
        company_id: int | None,
    ) -> list:
        async with db.session() as session:
            query = (
                select(SystemAttachment, UserUser.uuid, UserUser.name)
                .outerjoin(UserUser, UserUser.id == SystemAttachment.create_by)
                .where(
                    SystemAttachment.model_id == model_id,
                    SystemAttachment.record_uuid == record_uuid,
                    SystemAttachment.company_id == company_id,
                )
                .order_by(SystemAttachment.created_at.desc())
            )
            result = await session.execute(query)
            return list(result.all())

    @staticmethod
    async def delete(
        attachment_uuid: uuid_lib.UUID,
        company_id: int | None,
    ) -> tuple[SystemAttachment | None, int]:
        async with db.session() as session:
            result = await session.execute(
                select(SystemAttachment).where(
                    SystemAttachment.uuid == attachment_uuid,
                    SystemAttachment.company_id == company_id,
                )
            )
            attachment = result.scalar_one_or_none()
            if attachment is None:
                return None, 0

            storage_key = attachment.storage_key
            await session.delete(attachment)
            await session.flush()
            references = await session.scalar(
                select(func.count(SystemAttachment.id)).where(
                    SystemAttachment.storage_key == storage_key
                )
            )
            await session.commit()
            return attachment, int(references or 0)

    @staticmethod
    async def count_by_storage_key(storage_key: str) -> int:
        async with db.session() as session:
            count = await session.scalar(
                select(func.count(SystemAttachment.id)).where(
                    SystemAttachment.storage_key == storage_key
                )
            )
            return int(count or 0)
