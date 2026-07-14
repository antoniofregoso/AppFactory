import uuid as uuid_lib
from sqlalchemy import select

from app.core.database.session import db
from app.domains.parties.models.parties_party import PartiesParty


class PartyRepository:
    @staticmethod
    async def create(party: PartiesParty) -> PartiesParty:
        async with db.session() as session:
            session.add(party)
            await session.commit()
            await session.refresh(party)
            return party

    @staticmethod
    async def get_all() -> list[PartiesParty]:
        async with db.session() as session:
            query = select(Party).order_by(Party.created_at.desc())
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_by_uuid(party_uuid: uuid_lib.UUID) -> PartiesParty | None:
        async with db.session() as session:
            query = select(Party).where(Party.uuid == party_uuid)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(party_id: int) -> PartiesParty | None:
        async with db.session() as session:
            return await session.get(Party, party_id)

    @staticmethod
    async def update(party_uuid: uuid_lib.UUID, party_data: dict) -> PartiesParty | None:
        async with db.session() as session:
            query = select(Party).where(Party.uuid == party_uuid)
            result = await session.execute(query)
            party = result.scalar_one_or_none()

            if party:
                for key, value in party_data.items():
                    setattr(party, key, value)
                session.add(party)
                await session.commit()
                await session.refresh(party)
                return party
            return None

    @staticmethod
    async def delete(party_uuid: uuid_lib.UUID) -> bool:
        async with db.session() as session:
            query = select(Party).where(Party.uuid == party_uuid)
            result = await session.execute(query)
            party = result.scalar_one_or_none()

            if party:
                await session.delete(party)
                await session.commit()
                return True
            return False
