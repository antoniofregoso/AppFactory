from app.domains.talent.graphql.types import (
    TalentAgentType,
    TalentAreaType,
    TalentPositionType,
    TalentSystemType,
)


def talent_system_to_type(record) -> TalentSystemType:
    return TalentSystemType(
        id=record.id,
        uuid=record.uuid,
        company_id=record.company_id,
        code=record.code,
        name=record.name,
        description=record.description,
        active=record.active,
        sequence=record.sequence,
        color=record.color,
    )


def talent_area_to_type(record) -> TalentAreaType:
    return TalentAreaType(
        id=record.id,
        uuid=record.uuid,
        system_id=record.system_id,
        code=record.code,
        name=record.name,
        description=record.description,
        active=record.active,
        sequence=record.sequence,
    )


def talent_position_to_type(record) -> TalentPositionType:
    return TalentPositionType(
        id=record.id,
        uuid=record.uuid,
        area_id=record.area_id,
        parent_position_id=record.parent_position_id,
        code=record.code,
        name=record.name,
        mission=record.mission,
        active=record.active,
        sequence=record.sequence,
    )


def talent_agent_to_type(record) -> TalentAgentType:
    return TalentAgentType(
        id=record.id,
        uuid=record.uuid,
        name=record.name,
        type=record.type,
        active=record.active,
        sequence=record.sequence,
        color=record.color,
        avatar_url=record.avatar_url,
        party_id=record.party_id,
        company_id=record.company_id,
        position_id=record.position_id,
        user_id=record.user_id,
        date_start=record.date_start,
        date_end=record.date_end,
    )
