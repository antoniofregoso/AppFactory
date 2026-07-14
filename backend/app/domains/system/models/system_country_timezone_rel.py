from sqlmodel import SQLModel, Field


class SystemCountryTimezoneRel(SQLModel, table=True):
    __tablename__ = "system_country_timezone_rel"

    country_id: int = Field(foreign_key="system_countries.id", primary_key=True)
    timezone_id: int = Field(foreign_key="system_timezones.id", primary_key=True)
