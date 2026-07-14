import uuid as uuid_lib

from sqlalchemy import select

from app.core.database.session import db
from app.domains.system.models.system_note import SystemNote
from app.domains.users.models.user_user import UserUser


class SystemNoteRepository:
    @staticmethod
    async def create(note: SystemNote) -> SystemNote:
        async with db.session() as session:
            session.add(note)
            await session.commit()
            await session.refresh(note)
            return note

    @staticmethod
    async def get_by_record(model_id: int, record_uuid: uuid_lib.UUID, company_id: int | None):
        async with db.session() as session:
            result = await session.execute(
                select(SystemNote, UserUser.uuid, UserUser.name)
                .outerjoin(UserUser, UserUser.id == SystemNote.create_by)
                .where(
                    SystemNote.model_id == model_id,
                    SystemNote.record_uuid == record_uuid,
                    SystemNote.company_id == company_id,
                )
                .order_by(SystemNote.created_at.desc())
            )
            return list(result.all())

    @staticmethod
    async def get_author(note: SystemNote):
        async with db.session() as session:
            result = await session.execute(
                select(UserUser.uuid, UserUser.name).where(UserUser.id == note.create_by)
            )
            return result.one_or_none()

    @staticmethod
    async def delete(note_uuid: uuid_lib.UUID, company_id: int | None) -> bool:
        async with db.session() as session:
            result = await session.execute(
                select(SystemNote).where(
                    SystemNote.uuid == note_uuid,
                    SystemNote.company_id == company_id,
                )
            )
            note = result.scalar_one_or_none()
            if note is None:
                return False
            await session.delete(note)
            await session.commit()
            return True
