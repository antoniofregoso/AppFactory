from app.domains.parties.models.parties_party import PartiesParty
from app.domains.parties.repository.party_repository import PartyRepository


class PartyService:
    @staticmethod
    async def create(party: PartiesParty) -> PartiesParty:
        return await PartyRepository.create(party)

    @staticmethod
    async def get_all() -> list[PartiesParty]:
        return await PartyRepository.get_all()

    @staticmethod
    async def get_by_id(party_id: int) -> PartiesParty | None:
        return await PartyRepository.get_by_id(party_id)

    @staticmethod
    async def get_by_uuid(party_uuid) -> PartiesParty | None:
        return await PartyRepository.get_by_uuid(party_uuid)

    @staticmethod
    async def update(party_uuid, party_data: dict) -> PartiesParty | None:
        return await PartyRepository.update(party_uuid, party_data)

    @staticmethod
    async def delete(party_uuid) -> bool:
        return await PartyRepository.delete(party_uuid)
