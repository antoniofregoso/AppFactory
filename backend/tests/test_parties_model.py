from app.domains.parties.models import PartiesParty, PartyRole, PartyStatus, PartyType
from app.domains.system.repository.system_model_repository import MODEL_CLASS_BY_NAME
from sqlalchemy.orm import configure_mappers


def test_party_supports_multiple_roles_with_independent_statuses():
    party = PartiesParty(
        name="María López",
        party_type=PartyType.PERSON,
        is_employee=True,
        employee_status=PartyStatus.ACTIVE,
        is_customer=True,
        customer_status=PartyStatus.PENDING,
        is_supplier=False,
        supplier_status=PartyStatus.INACTIVE,
        email="maria@example.com",
        phone="5551234",
        street="Av. Principal 123",
        city="Ciudad",
    )

    assert party.roles == [PartyRole.EMPLOYEE, PartyRole.CUSTOMER]
    assert party.employee_status == PartyStatus.ACTIVE
    assert party.customer_status == PartyStatus.PENDING
    assert party.supplier_status == PartyStatus.INACTIVE
    assert party.party_type == PartyType.PERSON
    assert party.email == "maria@example.com"
    assert party.phone == "5551234"


def test_company_partner_exposes_its_employees():
    configure_mappers()

    company = PartiesParty(name="App Factory", party_type=PartyType.COMPANY)
    employee = PartiesParty(
        name="María López",
        party_type=PartyType.PERSON,
        is_employee=True,
        partner=company,
    )

    assert employee.partner is company
    assert employee in company.employees


def test_party_position_is_multilingual_json():
    first = PartiesParty(
        name="María López",
        position={"es": "Directora", "en": "Director"},
    )
    second = PartiesParty(name="Juan Pérez")

    assert first.position["es"] == "Directora"
    assert first.position["en"] == "Director"
    assert second.position == {}


def test_party_is_registered_for_graphql_model_views():
    assert MODEL_CLASS_BY_NAME["parties.party"] is PartiesParty
