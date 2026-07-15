import strawberry
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
