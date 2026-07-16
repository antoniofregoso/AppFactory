import json
from pathlib import Path

import strawberry
from sqlalchemy import inspect
from sqlmodel import SQLModel

from app.domains.talent.graphql.mutations import TalentMutation
from app.domains.talent.graphql.queries import TalentQuery
from app.domains.talent.models import TalentAgent, TalentArea, TalentPosition, TalentSystem


def test_talent_models_are_registered():
    assert {
        "talent_agents",
        "talent_areas",
        "talent_positions",
        "talent_systems",
    }.issubset(SQLModel.metadata.tables)


def test_talent_graphql_exposes_complete_crud():
    @strawberry.type
    class Query(TalentQuery):
        pass

    @strawberry.type
    class Mutation(TalentMutation):
        pass

    schema = strawberry.Schema(query=Query, mutation=Mutation).as_str()

    for operation in (
        "talentSystems",
        "talentSystem",
        "talentAreas",
        "talentArea",
        "talentPositions",
        "talentPosition",
        "talentAgents",
        "talentAgent",
        "createTalentSystem",
        "updateTalentSystem",
        "deleteTalentSystem",
        "createTalentArea",
        "updateTalentArea",
        "deleteTalentArea",
        "createTalentPosition",
        "updateTalentPosition",
        "deleteTalentPosition",
        "createTalentAgent",
        "updateTalentAgent",
        "deleteTalentAgent",
    ):
        assert operation in schema


def test_talent_multilingual_defaults_are_independent():
    first = TalentSystem(company_id=1, code="FIRST")
    second = TalentSystem(company_id=1, code="SECOND")
    area = TalentArea(system_id=1, code="AREA")
    position = TalentPosition(area_id=1, code="POSITION")
    agent = TalentAgent(name="Ada", party_id=1)

    first.name["es"] = "Primero"

    assert second.name == {}
    assert area.description == {}
    assert position.mission == {}
    assert agent.active is True
    assert first.color.value == "Zinc"


def test_talent_agent_user_relation_and_form_placement():
    relationship = inspect(TalentAgent).relationships["user"]
    assert relationship.mapper.class_.__name__ == "UserUser"
    assert relationship.back_populates == "talent_agents"

    schema_path = Path(__file__).parents[1] / "app/domains/talent/data/system_model_schemas.json"
    schemas = json.loads(schema_path.read_text(encoding="utf-8"))
    agent_view = next(item for item in schemas if item["model"] == "talent.agent")
    fields = {item["name"]: item for item in agent_view["view"]}
    assert fields["party_id"]["form"]["leftColumn"] == 0
    assert fields["user_id"]["form"]["leftColumn"] == 1
    assert "list" not in fields["user_id"]
    assert "kanban" not in fields["user_id"]
