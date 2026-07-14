import uuid as uuid_lib
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Enum as SAEnum
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB

from app.domains.system.models.system_audit import SystemAudit


class CurrencyPosition(str, Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"


class SystemCurrency(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_currencies"

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
    code: str
    iso_numeric: int
    symbol: str
    currency_unit_label: Optional[dict] = Field(default=None, sa_type=JSONB)
    currency_subunit_label: Optional[dict] = Field(default=None, sa_type=JSONB)
    rounding: float = Field(default=0.01)
    position: CurrencyPosition = Field(
        default=CurrencyPosition.BEFORE,
        sa_type=SAEnum(
            CurrencyPosition,
            name="currency_position",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
    )
    active: bool = Field(default=False)

    def get_currency_unit_label(self, lang: str = "es", fallback: str = "en") -> str:
        return (
            self.currency_unit_label.get(lang)
            or self.currency_unit_label.get(fallback)
            or next(iter(self.currency_unit_label.values()), "")
        )
    
    def get_currency_subunit_label(self, lang: str = "es", fallback: str = "en") -> str:
        return (
            self.currency_subunit_label.get(lang)
            or self.currency_subunit_label.get(fallback)
            or next(iter(self.currency_subunit_label.values()), "")
        )
