import uuid as uuid_lib
from datetime import date
from typing import Optional

import strawberry
from strawberry.scalars import JSON

from app.domains.system.models.system_colors import SystemColor
from app.domains.talent.models.talent_agent import AgentType

TalentAgentTypeEnum = strawberry.enum(AgentType)
TalentColorType = strawberry.enum(SystemColor)


@strawberry.type
class TalentSystemType:
    id: int
    uuid: uuid_lib.UUID
    company_id: int
    code: str
    name: JSON
    description: JSON
    active: bool
    sequence: int
    color: TalentColorType


@strawberry.type
class TalentAreaType:
    id: int
    uuid: uuid_lib.UUID
    system_id: int
    code: str
    name: JSON
    description: JSON
    active: bool
    sequence: int


@strawberry.type
class TalentPositionType:
    id: int
    uuid: uuid_lib.UUID
    area_id: int
    parent_position_id: Optional[int]
    code: str
    name: JSON
    mission: JSON
    active: bool
    sequence: int


@strawberry.type
class TalentAgentType:
    id: int
    uuid: uuid_lib.UUID
    name: str
    type: TalentAgentTypeEnum
    active: bool
    sequence: int
    color: TalentColorType
    avatar_url: Optional[str]
    party_id: int
    company_id: Optional[int]
    position_id: Optional[int]
    user_id: Optional[int]
    date_start: Optional[date]
    date_end: Optional[date]


@strawberry.input
class TalentSystemCreateInput:
    code: str
    name: JSON
    description: JSON
    active: bool = True
    sequence: int = 10
    color: TalentColorType = SystemColor.zinc


@strawberry.input
class TalentSystemUpdateInput:
    code: Optional[str] = None
    name: Optional[JSON] = None
    description: Optional[JSON] = None
    active: Optional[bool] = None
    sequence: Optional[int] = None
    color: Optional[TalentColorType] = None


@strawberry.input
class TalentAreaCreateInput:
    system_id: int
    code: str
    name: JSON
    description: JSON
    active: bool = True
    sequence: int = 10


@strawberry.input
class TalentAreaUpdateInput:
    system_id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[JSON] = None
    description: Optional[JSON] = None
    active: Optional[bool] = None
    sequence: Optional[int] = None


@strawberry.input
class TalentPositionCreateInput:
    area_id: int
    code: str
    name: JSON
    mission: JSON
    parent_position_id: Optional[int] = None
    active: bool = True
    sequence: int = 10


@strawberry.input
class TalentPositionUpdateInput:
    area_id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[JSON] = None
    mission: Optional[JSON] = None
    parent_position_id: Optional[int] = None
    active: Optional[bool] = None
    sequence: Optional[int] = None


@strawberry.input
class TalentAgentCreateInput:
    name: str
    party_id: int
    type: TalentAgentTypeEnum = AgentType.HUMAN
    active: bool = True
    sequence: int = 10
    color: TalentColorType = SystemColor.zinc
    avatar_url: Optional[str] = None
    position_id: Optional[int] = None
    user_id: Optional[int] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None


@strawberry.input
class TalentAgentUpdateInput:
    name: Optional[str] = None
    party_id: Optional[int] = None
    type: Optional[TalentAgentTypeEnum] = None
    active: Optional[bool] = None
    sequence: Optional[int] = None
    color: Optional[TalentColorType] = None
    avatar_url: Optional[str] = None
    position_id: Optional[int] = None
    user_id: Optional[int] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
