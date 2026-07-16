import uuid as uuid_lib

import strawberry

from app.core.exceptions import AuthorizationException, ResourceNotFoundException
from app.core.security.jwt_bearer import IsAuthenticated
from app.domains.access.service import AccessService
from app.domains.system.graphql.queries import get_current_user
from app.domains.talent.graphql.mappers import (
    talent_agent_to_type,
    talent_area_to_type,
    talent_position_to_type,
    talent_system_to_type,
)
from app.domains.talent.graphql.types import (
    TalentAgentType,
    TalentAreaType,
    TalentPositionType,
    TalentSystemType,
)
from app.domains.talent.models import (
    TalentAgent,
    TalentArea,
    TalentPosition,
    TalentSystem,
)
from app.domains.talent.service import TalentService


def require_company_id(user) -> int:
    if user.company_id is None:
        raise AuthorizationException("User has no company")
    return user.company_id


async def require_talent_permission(user, resource: str, action: str) -> int:
    company_id = require_company_id(user)
    await AccessService.require(
        user,
        f"talent.{resource}.{action}",
        company_id=company_id,
    )
    return company_id


async def _get_record(model, record_uuid, company_id, resource):
    record = await TalentService.get_by_uuid(model, record_uuid, company_id)
    if record is None:
        raise ResourceNotFoundException(resource, record_uuid)
    return record


@strawberry.type
class TalentQuery:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def talent_systems(
        self, info: strawberry.types.Info
    ) -> list[TalentSystemType]:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "system", "read")
        records = await TalentService.get_all(TalentSystem, company_id)
        return [talent_system_to_type(record) for record in records]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def talent_system(
        self, info: strawberry.types.Info, record_uuid: uuid_lib.UUID
    ) -> TalentSystemType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "system", "read")
        record = await _get_record(
            TalentSystem, record_uuid, company_id, "Talent system"
        )
        return talent_system_to_type(record)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def talent_areas(
        self, info: strawberry.types.Info
    ) -> list[TalentAreaType]:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "area", "read")
        records = await TalentService.get_all(TalentArea, company_id)
        return [talent_area_to_type(record) for record in records]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def talent_area(
        self, info: strawberry.types.Info, record_uuid: uuid_lib.UUID
    ) -> TalentAreaType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "area", "read")
        record = await _get_record(
            TalentArea, record_uuid, company_id, "Talent area"
        )
        return talent_area_to_type(record)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def talent_positions(
        self, info: strawberry.types.Info
    ) -> list[TalentPositionType]:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "position", "read")
        records = await TalentService.get_all(TalentPosition, company_id)
        return [talent_position_to_type(record) for record in records]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def talent_position(
        self, info: strawberry.types.Info, record_uuid: uuid_lib.UUID
    ) -> TalentPositionType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "position", "read")
        record = await _get_record(
            TalentPosition, record_uuid, company_id, "Talent position"
        )
        return talent_position_to_type(record)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def talent_agents(
        self, info: strawberry.types.Info
    ) -> list[TalentAgentType]:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "agent", "read")
        records = await TalentService.get_all(TalentAgent, company_id)
        return [talent_agent_to_type(record) for record in records]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def talent_agent(
        self, info: strawberry.types.Info, record_uuid: uuid_lib.UUID
    ) -> TalentAgentType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "agent", "read")
        record = await _get_record(
            TalentAgent, record_uuid, company_id, "Talent agent"
        )
        return talent_agent_to_type(record)
