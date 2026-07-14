from typing import TYPE_CHECKING, List, Optional
import uuid
import sqlalchemy as sa
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit
from app.domains.system.models.system_colors import SystemColor

if TYPE_CHECKING:
    from app.domains.system.models.system_app import SystemApp
    from app.domains.system.models.system_currency import SystemCurrency
    from app.domains.system.models.system_whatsapp import SystemWhatsApp
    from app.domains.users.models.user_user import UserUser


class SystemCompany(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_companies"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    name: str
    active: bool = Field(default=True)
    sequence: Optional[int] = Field(default=10)
    color: SystemColor = Field(
        default=SystemColor.zinc,
        sa_column=sa.Column(sa.String(32), nullable=False),
    )
    currency_id: Optional[int] = Field(default=None, foreign_key="system_currencies.id")
    currency: Optional["SystemCurrency"] = Relationship()
    logo_url: Optional[str] = None
    street: Optional[str] = None
    street2: Optional[str] = None
    zip: Optional[str] = None
    city: Optional[str] = None
    state_id: Optional[int] = Field(
        default=None, foreign_key="system_country_states.id"
    )
    country_id: Optional[int] = Field(default=None, foreign_key="system_countries.id")
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    vat: Optional[str] = None
    lang_id: Optional[int] = Field(default=None, foreign_key="system_langs.id")
    users: List["UserUser"] = Relationship(
        back_populates="company",
        sa_relationship_kwargs={"foreign_keys": "[UserUser.company_id]"},
    )
    apps: List["SystemApp"] = Relationship(back_populates="company")
    whatsapp_configurations: List["SystemWhatsApp"] = Relationship(
        back_populates="company"
    )
