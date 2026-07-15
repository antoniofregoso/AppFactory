import uuid
from datetime import date
from enum import Enum
from typing import Optional

from sqlalchemy import UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.domains.system.models.system_audit import SystemAudit


class AccessScopeType(str, Enum):
    GLOBAL = "GLOBAL"
    COMPANY = "COMPANY"
    MODEL = "MODEL"
    RECORD = "RECORD"
    OWN = "OWN"
    ASSIGNED = "ASSIGNED"


class AccessPermission(SystemAudit, SQLModel, table=True):
    __tablename__ = "access_permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid.UUID = Field(default_factory=uuid.uuid4, index=True, unique=True,
                            sa_column_kwargs={"server_default": sa_text("gen_random_uuid()")})
    code: str = Field(unique=True, index=True, max_length=160)
    domain: str = Field(index=True, max_length=80)
    resource: str = Field(max_length=80)
    action: str = Field(max_length=80)
    name: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    description: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    active: bool = Field(default=True)


class AccessRole(SystemAudit, SQLModel, table=True):
    __tablename__ = "access_roles"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_access_role_company_code"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid.UUID = Field(default_factory=uuid.uuid4, index=True, unique=True,
                            sa_column_kwargs={"server_default": sa_text("gen_random_uuid()")})
    company_id: Optional[int] = Field(default=None, foreign_key="system_companies.id", index=True)
    code: str = Field(index=True, max_length=100)
    name: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    description: dict[str, str] = Field(default_factory=dict, sa_type=JSONB)
    active: bool = Field(default=True)
    sequence: int = Field(default=10)


class AccessRolePermission(SQLModel, table=True):
    __tablename__ = "access_role_permissions"

    role_id: int = Field(foreign_key="access_roles.id", primary_key=True)
    permission_id: int = Field(foreign_key="access_permissions.id", primary_key=True)


class AccessUserRole(SystemAudit, SQLModel, table=True):
    __tablename__ = "access_user_roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid.UUID = Field(default_factory=uuid.uuid4, index=True, unique=True,
                            sa_column_kwargs={"server_default": sa_text("gen_random_uuid()")})
    user_id: int = Field(foreign_key="user_user.id", index=True)
    role_id: int = Field(foreign_key="access_roles.id", index=True)
    company_id: Optional[int] = Field(default=None, foreign_key="system_companies.id", index=True)
    scope_type: AccessScopeType = Field(default=AccessScopeType.COMPANY, index=True)
    scope_model: Optional[str] = Field(default=None, max_length=160, index=True)
    scope_record_uuid: Optional[uuid.UUID] = Field(default=None, index=True)
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    active: bool = Field(default=True)

