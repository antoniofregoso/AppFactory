from dataclasses import asdict
import uuid as uuid_lib

import strawberry

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.core.security.jwt_bearer import IsAuthenticated
from app.domains.system.graphql.queries import get_current_user
from app.domains.talent.graphql.mappers import (
    talent_agent_to_type,
    talent_area_to_type,
    talent_position_to_type,
    talent_system_to_type,
)
from app.domains.talent.graphql.queries import require_talent_permission
from app.domains.talent.graphql.types import (
    TalentAgentCreateInput,
    TalentAgentType,
    TalentAgentUpdateInput,
    TalentAreaCreateInput,
    TalentAreaType,
    TalentAreaUpdateInput,
    TalentPositionCreateInput,
    TalentPositionType,
    TalentPositionUpdateInput,
    TalentSystemCreateInput,
    TalentSystemType,
    TalentSystemUpdateInput,
)
from app.domains.talent.models import (
    TalentAgent,
    TalentArea,
    TalentPosition,
    TalentSystem,
)
from app.domains.talent.service import TalentService
from app.domains.users.repository.user_repository import UserRepository


def _input_values(value, *, partial: bool = False) -> dict:
    values = asdict(value)
    if partial:
        return {key: item for key, item in values.items() if item is not None}
    return values


async def _require_related(model, record_id, company_id, field_name):
    if record_id is None:
        return
    if await TalentService.get_by_id(model, record_id, company_id) is None:
        raise ValidationException(f"Invalid {field_name}")


async def _validate_relations(model, values: dict, company_id: int):
    if model is TalentArea and "system_id" in values:
        await _require_related(
            TalentSystem, values["system_id"], company_id, "system_id"
        )
    if model is TalentPosition:
        if "area_id" in values:
            await _require_related(
                TalentArea, values["area_id"], company_id, "area_id"
            )
        if "parent_position_id" in values:
            await _require_related(
                TalentPosition,
                values["parent_position_id"],
                company_id,
                "parent_position_id",
            )
    if model is TalentAgent:
        if "position_id" in values:
            await _require_related(
                TalentPosition, values["position_id"], company_id, "position_id"
            )
        if values.get("user_id") is not None:
            linked_user = await UserRepository.get_by_id(values["user_id"])
            if linked_user is None or linked_user.company_id != company_id:
                raise ValidationException("Invalid user_id")


async def _update(model, record_uuid, values, company_id, resource):
    await _validate_relations(model, values, company_id)
    record = await TalentService.update(model, record_uuid, company_id, values)
    if record is None:
        raise ResourceNotFoundException(resource, record_uuid)
    return record


async def _delete(model, record_uuid, company_id, resource):
    if not await TalentService.delete(model, record_uuid, company_id):
        raise ResourceNotFoundException(resource, record_uuid)
    return True


@strawberry.type
class TalentMutation:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_talent_system(
        self, info: strawberry.types.Info, input: TalentSystemCreateInput
    ) -> TalentSystemType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "system", "create")
        record = TalentSystem(
            company_id=company_id, **_input_values(input)
        )
        return talent_system_to_type(await TalentService.create(record))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_talent_system(
        self,
        info: strawberry.types.Info,
        record_uuid: uuid_lib.UUID,
        input: TalentSystemUpdateInput,
    ) -> TalentSystemType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "system", "update")
        record = await _update(
            TalentSystem,
            record_uuid,
            _input_values(input, partial=True),
            company_id,
            "Talent system",
        )
        return talent_system_to_type(record)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_talent_system(
        self, info: strawberry.types.Info, record_uuid: uuid_lib.UUID
    ) -> bool:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "system", "delete")
        return await _delete(
            TalentSystem, record_uuid, company_id, "Talent system"
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_talent_area(
        self, info: strawberry.types.Info, input: TalentAreaCreateInput
    ) -> TalentAreaType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "area", "create")
        values = _input_values(input)
        await _validate_relations(TalentArea, values, company_id)
        return talent_area_to_type(
            await TalentService.create(TalentArea(**values))
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_talent_area(
        self,
        info: strawberry.types.Info,
        record_uuid: uuid_lib.UUID,
        input: TalentAreaUpdateInput,
    ) -> TalentAreaType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "area", "update")
        record = await _update(
            TalentArea,
            record_uuid,
            _input_values(input, partial=True),
            company_id,
            "Talent area",
        )
        return talent_area_to_type(record)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_talent_area(
        self, info: strawberry.types.Info, record_uuid: uuid_lib.UUID
    ) -> bool:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "area", "delete")
        return await _delete(
            TalentArea, record_uuid, company_id, "Talent area"
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_talent_position(
        self, info: strawberry.types.Info, input: TalentPositionCreateInput
    ) -> TalentPositionType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "position", "create")
        values = _input_values(input)
        await _validate_relations(TalentPosition, values, company_id)
        return talent_position_to_type(
            await TalentService.create(TalentPosition(**values))
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_talent_position(
        self,
        info: strawberry.types.Info,
        record_uuid: uuid_lib.UUID,
        input: TalentPositionUpdateInput,
    ) -> TalentPositionType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "position", "update")
        record = await _update(
            TalentPosition,
            record_uuid,
            _input_values(input, partial=True),
            company_id,
            "Talent position",
        )
        return talent_position_to_type(record)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_talent_position(
        self, info: strawberry.types.Info, record_uuid: uuid_lib.UUID
    ) -> bool:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "position", "delete")
        return await _delete(
            TalentPosition,
            record_uuid,
            company_id,
            "Talent position",
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_talent_agent(
        self, info: strawberry.types.Info, input: TalentAgentCreateInput
    ) -> TalentAgentType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "agent", "create")
        values = _input_values(input)
        await _validate_relations(TalentAgent, values, company_id)
        record = TalentAgent(company_id=company_id, **values)
        return talent_agent_to_type(await TalentService.create(record))

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def update_talent_agent(
        self,
        info: strawberry.types.Info,
        record_uuid: uuid_lib.UUID,
        input: TalentAgentUpdateInput,
    ) -> TalentAgentType:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "agent", "update")
        record = await _update(
            TalentAgent,
            record_uuid,
            _input_values(input, partial=True),
            company_id,
            "Talent agent",
        )
        return talent_agent_to_type(record)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def delete_talent_agent(
        self, info: strawberry.types.Info, record_uuid: uuid_lib.UUID
    ) -> bool:
        user = await get_current_user(info)
        company_id = await require_talent_permission(user, "agent", "delete")
        return await _delete(
            TalentAgent, record_uuid, company_id, "Talent agent"
        )
