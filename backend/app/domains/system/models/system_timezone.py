import uuid as uuid_lib
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import text as sa_text
from app.domains.system.models.system_audit import SystemAudit
from app.domains.system.models.system_country_timezone_rel import SystemCountryTimezoneRel

if TYPE_CHECKING:
    from app.domains.system.models.system_country import SystemCountry


class SystemTimezone(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_timezones"

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
    code: str = Field(index=True, unique=True)
    offset: Optional[int] = Field(default=0)
    countries: list["SystemCountry"] = Relationship(
        back_populates="timezones",
        link_model=SystemCountryTimezoneRel,
    )
