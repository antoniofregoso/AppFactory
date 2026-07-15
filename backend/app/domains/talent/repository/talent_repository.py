import uuid as uuid_lib
from typing import Any, TypeVar

from sqlalchemy import select
from sqlmodel import SQLModel

from app.core.database.session import db
from app.domains.talent.models import (
    TalentAgent,
    TalentArea,
    TalentPosition,
    TalentSystem,
)

TalentModel = TypeVar("TalentModel", bound=SQLModel)


class TalentRepository:
    @staticmethod
    def _company_query(model: type[TalentModel], company_id: int):
        query = select(model)
        if model is TalentSystem:
            return query.where(TalentSystem.company_id == company_id)
        if model is TalentArea:
            return query.join(TalentSystem).where(TalentSystem.company_id == company_id)
        if model is TalentPosition:
            return (
                query.join(TalentArea)
                .join(TalentSystem)
                .where(TalentSystem.company_id == company_id)
            )
        if model is TalentAgent:
            return query.where(TalentAgent.company_id == company_id)
        raise ValueError(f"Unsupported talent model: {model.__name__}")

    @classmethod
    async def create(cls, record: TalentModel) -> TalentModel:
        async with db.session() as session:
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @classmethod
    async def get_all(
        cls, model: type[TalentModel], company_id: int
    ) -> list[TalentModel]:
        async with db.session() as session:
            query = cls._company_query(model, company_id).order_by(
                model.sequence, model.id
            )
            result = await session.execute(query)
            return list(result.scalars().all())

    @classmethod
    async def get_by_uuid(
        cls,
        model: type[TalentModel],
        record_uuid: uuid_lib.UUID,
        company_id: int,
    ) -> TalentModel | None:
        async with db.session() as session:
            query = cls._company_query(model, company_id).where(
                model.uuid == record_uuid
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_by_id(
        cls,
        model: type[TalentModel],
        record_id: int,
        company_id: int,
    ) -> TalentModel | None:
        async with db.session() as session:
            query = cls._company_query(model, company_id).where(model.id == record_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def update(
        cls,
        model: type[TalentModel],
        record_uuid: uuid_lib.UUID,
        company_id: int,
        values: dict[str, Any],
    ) -> TalentModel | None:
        async with db.session() as session:
            query = cls._company_query(model, company_id).where(
                model.uuid == record_uuid
            )
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record is None:
                return None
            for key, value in values.items():
                setattr(record, key, value)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @classmethod
    async def delete(
        cls,
        model: type[TalentModel],
        record_uuid: uuid_lib.UUID,
        company_id: int,
    ) -> bool:
        async with db.session() as session:
            query = cls._company_query(model, company_id).where(
                model.uuid == record_uuid
            )
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record is None:
                return False
            await session.delete(record)
            await session.commit()
            return True
