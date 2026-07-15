import uuid as uuid_lib
from typing import Any, TypeVar

from sqlmodel import SQLModel

from app.domains.talent.repository import TalentRepository

TalentModel = TypeVar("TalentModel", bound=SQLModel)


class TalentService:
    @staticmethod
    async def create(record: TalentModel) -> TalentModel:
        return await TalentRepository.create(record)

    @staticmethod
    async def get_all(
        model: type[TalentModel], company_id: int
    ) -> list[TalentModel]:
        return await TalentRepository.get_all(model, company_id)

    @staticmethod
    async def get_by_uuid(
        model: type[TalentModel],
        record_uuid: uuid_lib.UUID,
        company_id: int,
    ) -> TalentModel | None:
        return await TalentRepository.get_by_uuid(model, record_uuid, company_id)

    @staticmethod
    async def get_by_id(
        model: type[TalentModel], record_id: int, company_id: int
    ) -> TalentModel | None:
        return await TalentRepository.get_by_id(model, record_id, company_id)

    @staticmethod
    async def update(
        model: type[TalentModel],
        record_uuid: uuid_lib.UUID,
        company_id: int,
        values: dict[str, Any],
    ) -> TalentModel | None:
        protected = {"id", "uuid", "company_id", "created_at", "create_by"}
        clean_values = {k: v for k, v in values.items() if k not in protected}
        return await TalentRepository.update(
            model, record_uuid, company_id, clean_values
        )

    @staticmethod
    async def delete(
        model: type[TalentModel],
        record_uuid: uuid_lib.UUID,
        company_id: int,
    ) -> bool:
        return await TalentRepository.delete(model, record_uuid, company_id)
