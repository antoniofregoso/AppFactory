import uuid as uuid_lib
from enum import Enum
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import text as sa_text
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit


class PartyRole(str, Enum):
    EMPLOYEE = "employee"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"


class PartyType(str, Enum):
    PERSON = "person"
    COMPANY = "company"
    AI_AGENT = "ai_agent"


class PartyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class PartiesParty(SystemAudit, SQLModel, table=True):
    __tablename__ = "parties_party"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )

    name: str
    avatar: Optional[str] = None

    party_type: PartyType = Field(default=PartyType.PERSON)

    is_employee: bool = Field(default=False)
    is_customer: bool = Field(default=False)
    is_supplier: bool = Field(default=False)

    employee_status: PartyStatus = Field(default=PartyStatus.PENDING)
    customer_status: PartyStatus = Field(default=PartyStatus.PENDING)
    supplier_status: PartyStatus = Field(default=PartyStatus.PENDING)

    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    street: Optional[str] = None
    street2: Optional[str] = None
    zip: Optional[str] = None
    city: Optional[str] = None
    state_id: Optional[int] = Field(default=None, foreign_key="system_country_states.id")
    country_id: Optional[int] = Field(default=None, foreign_key="system_countries.id")
    lang_id: Optional[int] = Field(default=None, foreign_key="system_langs.id")
    currency_id: Optional[int] = Field(default=None, foreign_key="system_currencies.id")
    website: Optional[str] = None
    vat: Optional[str] = None

    active: bool = Field(default=True)
    sequence: Optional[int] = Field(default=10)
    color: Optional[str] = Field(default=None)

    company_id: Optional[int] = Field(
        default=None, foreign_key="system_companies.id", nullable=True
    )

    partner_id: Optional[int] = Field(
        default=None, foreign_key="parties_party.id", nullable=True, index=True
    )
    partner: Optional["PartiesParty"] = Relationship(
        back_populates="employees",
        sa_relationship_kwargs={
            "foreign_keys": "[PartiesParty.partner_id]",
            "remote_side": "[PartiesParty.id]",
        },
    )
    employees: List["PartiesParty"] = Relationship(
        back_populates="partner",
        sa_relationship_kwargs={"foreign_keys": "[PartiesParty.partner_id]"},
    )

    @property
    def roles(self) -> List[PartyRole]:
        roles: List[PartyRole] = []
        if self.is_employee:
            roles.append(PartyRole.EMPLOYEE)
        if self.is_customer:
            roles.append(PartyRole.CUSTOMER)
        if self.is_supplier:
            roles.append(PartyRole.SUPPLIER)
        return roles


Party = PartiesParty
