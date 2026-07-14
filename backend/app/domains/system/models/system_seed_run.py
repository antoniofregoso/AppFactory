from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import DateTime


class SystemSeedRun(SQLModel, table=True):
    __tablename__ = "system_seed_runs"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    seed_key: str = Field(index=True, unique=True)
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
