import uuid as uuid_lib
from datetime import date
from typing import Optional

import strawberry
from strawberry.scalars import JSON

from app.domains.access.models import AccessScopeType

AccessScopeTypeEnum = strawberry.enum(AccessScopeType)


@strawberry.type
class AccessPermissionType:
    uuid: uuid_lib.UUID
    code: str
    domain: str
    resource: str
    action: str
    name: JSON
    description: JSON
    active: bool


@strawberry.type
class AccessRoleType:
    uuid: uuid_lib.UUID
    company_id: Optional[int]
    code: str
    name: JSON
    description: JSON
    active: bool
    sequence: int
    permissions: list[AccessPermissionType]


@strawberry.type
class AccessUserRoleType:
    uuid: uuid_lib.UUID
    user_uuid: uuid_lib.UUID
    role_uuid: uuid_lib.UUID
    company_id: Optional[int]
    scope_type: AccessScopeTypeEnum
    scope_model: Optional[str]
    scope_record_uuid: Optional[uuid_lib.UUID]
    date_start: Optional[date]
    date_end: Optional[date]
    active: bool


@strawberry.input
class AccessPermissionInput:
    code: str
    domain: str
    resource: str
    action: str
    name: JSON
    description: JSON
    active: bool = True


@strawberry.input
class AccessRoleInput:
    code: str
    name: JSON
    description: JSON
    permission_uuids: list[uuid_lib.UUID]
    company_id: Optional[int] = None
    active: bool = True
    sequence: int = 10


@strawberry.input
class AccessUserRoleInput:
    user_uuid: uuid_lib.UUID
    role_uuid: uuid_lib.UUID
    scope_type: AccessScopeTypeEnum = AccessScopeType.COMPANY
    company_id: Optional[int] = None
    scope_model: Optional[str] = None
    scope_record_uuid: Optional[uuid_lib.UUID] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    active: bool = True
