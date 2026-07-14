import uuid as uuid_lib
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field as PydanticField

from app.domains.parties.models.parties_party import (
    PartiesParty,
    PartyRole,
    PartyStatus,
    PartyType,
)
from app.domains.parties.service.party_service import PartyService
from app.domains.system.api.dependencies import get_current_user
from app.domains.users.models.user_user import UserUser

router = APIRouter(prefix="/api/parties", tags=["parties"])


class PartyCreateRequest(BaseModel):
    name: str
    document_number: str | None = None
    notes: str | None = None
    party_type: PartyType = PartyType.PERSON
    is_employee: bool = False
    is_customer: bool = False
    is_supplier: bool = False
    employee_status: PartyStatus | None = None
    customer_status: PartyStatus | None = None
    supplier_status: PartyStatus | None = None
    company_id: int | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    street: str | None = None
    street2: str | None = None
    zip: str | None = None
    city: str | None = None
    state_id: int | None = None
    country_id: int | None = None
    website: str | None = None
    tax_id: str | None = None
    active: bool = True
    sequence: int | None = 10
    color: str | None = None


class PartyResponse(BaseModel):
    uuid: uuid_lib.UUID
    name: str
    document_number: str | None = None
    notes: str | None = None
    party_type: PartyType
    is_employee: bool
    is_customer: bool
    is_supplier: bool
    employee_status: PartyStatus
    customer_status: PartyStatus
    supplier_status: PartyStatus
    company_id: int | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    street: str | None = None
    street2: str | None = None
    zip: str | None = None
    city: str | None = None
    state_id: int | None = None
    country_id: int | None = None
    website: str | None = None
    tax_id: str | None = None
    active: bool
    sequence: int | None = None
    color: str | None = None
    roles: list[PartyRole]

    @classmethod
    def from_party(cls, party: PartiesParty) -> "PartyResponse":
        return cls(
            uuid=party.uuid,
            name=party.name,
            document_number=party.document_number,
            notes=party.notes,
            party_type=party.party_type,
            is_employee=party.is_employee,
            is_customer=party.is_customer,
            is_supplier=party.is_supplier,
            employee_status=party.employee_status,
            customer_status=party.customer_status,
            supplier_status=party.supplier_status,
            company_id=party.company_id,
            email=party.email,
            phone=party.phone,
            mobile=party.mobile,
            street=party.street,
            street2=party.street2,
            zip=party.zip,
            city=party.city,
            state_id=party.state_id,
            country_id=party.country_id,
            website=party.website,
            tax_id=party.tax_id,
            active=party.active,
            sequence=party.sequence,
            color=party.color,
            roles=party.roles,
        )


@router.post("", response_model=PartyResponse, status_code=201)
async def create_party(
    payload: PartyCreateRequest,
    user: UserUser = Depends(get_current_user),
) -> PartyResponse:
    party = PartiesParty(
        name=payload.name,
        document_number=payload.document_number,
        notes=payload.notes,
        party_type=payload.party_type,
        is_employee=payload.is_employee,
        is_customer=payload.is_customer,
        is_supplier=payload.is_supplier,
        employee_status=payload.employee_status or PartyStatus.PENDING,
        customer_status=payload.customer_status or PartyStatus.PENDING,
        supplier_status=payload.supplier_status or PartyStatus.PENDING,
        company_id=payload.company_id or user.company_id,
        email=payload.email,
        phone=payload.phone,
        mobile=payload.mobile,
        street=payload.street,
        street2=payload.street2,
        zip=payload.zip,
        city=payload.city,
        state_id=payload.state_id,
        country_id=payload.country_id,
        website=payload.website,
        tax_id=payload.tax_id,
        active=payload.active,
        sequence=payload.sequence,
        color=payload.color,
    )
    created = await PartyService.create(party)
    return PartyResponse.from_party(created)


@router.get("", response_model=list[PartyResponse])
async def list_parties(
    user: UserUser = Depends(get_current_user),
) -> list[PartyResponse]:
    parties = await PartyService.get_all()
    return [PartyResponse.from_party(party) for party in parties]


@router.get("/{party_uuid}", response_model=PartyResponse)
async def get_party(
    party_uuid: uuid_lib.UUID,
    user: UserUser = Depends(get_current_user),
) -> PartyResponse:
    party = await PartyService.get_by_uuid(party_uuid)
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    return PartyResponse.from_party(party)


@router.put("/{party_uuid}", response_model=PartyResponse)
async def update_party(
    party_uuid: uuid_lib.UUID,
    payload: PartyCreateRequest,
    user: UserUser = Depends(get_current_user),
) -> PartyResponse:
    updated = await PartyService.update(
        party_uuid,
        payload.model_dump(exclude_unset=True),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Party not found")
    return PartyResponse.from_party(updated)


@router.delete("/{party_uuid}", status_code=204)
async def delete_party(
    party_uuid: uuid_lib.UUID,
    user: UserUser = Depends(get_current_user),
) -> None:
    deleted = await PartyService.delete(party_uuid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Party not found")
