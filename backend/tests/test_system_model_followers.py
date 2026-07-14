from sqlalchemy import inspect

from app.domains.system.models import SystemModel, SystemModelFollowers
from app.domains.users.models import UserUser


def test_system_model_followers_uses_generic_record_identity():
    table = SystemModelFollowers.__table__

    assert list(table.primary_key.columns.keys()) == [
        "user_id",
        "model_id",
        "record_uuid",
    ]
    assert "ix_system_model_followers_record" in {
        index.name for index in table.indexes
    }


def test_user_has_model_followers_relationship():
    relationship = inspect(UserUser).relationships["model_followers"]

    assert relationship.mapper.class_ is SystemModelFollowers
    assert relationship.back_populates == "user"


def test_model_followers_is_linked_to_system_model():
    follower_model = inspect(SystemModelFollowers).relationships["model"]
    model_followers = inspect(SystemModel).relationships["model_followers"]

    assert follower_model.mapper.class_ is SystemModel
    assert follower_model.back_populates == "model_followers"
    assert model_followers.mapper.class_ is SystemModelFollowers
    assert model_followers.back_populates == "model"


def test_system_model_has_metadata_columns():
    table = SystemModel.__table__

    assert {
        "name",
        "label",
        "group_by",
        "group_by_values",
        "tags",
    }.issubset(table.columns.keys())
