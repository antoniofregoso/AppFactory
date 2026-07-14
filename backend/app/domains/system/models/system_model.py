from typing import TYPE_CHECKING, Optional
import enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text as sa_text
import sqlalchemy as sa
from sqlmodel import Field, Column, Relationship, SQLModel
import uuid

from app.domains.system.models.system_audit import SystemAudit

if TYPE_CHECKING:
    from app.domains.system.models.system_model_followers import SystemModelFollowers


class FieldType(str, enum.Enum):
    string = "string"
    integer = "integer"
    decimal = "decimal"
    monetary = "monetary"
    percentage = "percentage"
    date = "date"
    datetime = "datetime"
    boolean = "boolean"
    color = "color"
    image = "image"
    text = "text"
    password = "password"
    selection = "selection"
    status_badge = "status_badge"
    html = "html"
    json = "json"
    many2one = "many2one"
    many2one_avatar = "many2one_avatar"
    one2many = "one2many"
    one2many_kanban = "one2many_kanban"
    one2many_list = "one2many_list"
    one2many_followers = "one2many_followers"
    many2many = "many2many"
    many2many_pills = "many2many_pills"


class SystemModelSchemaUse(str, enum.Enum):
    view = "view"
    insight = "insight"


class SystemModel(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_models"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    name: str
    search: bool = Field(default=False, nullable=False)
    readonly: bool = Field(default=False, nullable=False)
    label: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    group_by: Optional[str] = Field(default=None)
    group_by_values: list[dict] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    tags: list[dict] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    fields: list["SystemModelField"] = Relationship(
        back_populates="model",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    schemas: list["SystemModelSchema"] = Relationship(
        back_populates="model",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    model_followers: list["SystemModelFollowers"] = Relationship(
        back_populates="model"
    )

    def get_label(self, lang: str = "es", fallback: str = "en") -> str:
        return (
            self.label.get(lang)
            or self.label.get(fallback)
            or next(iter(self.label.values()), "")
        )


class SystemModelField(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_model_fields"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    name: str
    sequence: Optional[int] = Field(default=10)
    type: FieldType = Field(
        default=FieldType.string,
        sa_column=sa.Column(sa.String(32), nullable=False),
    )
    required: bool = Field(default=False)
    readonly: bool = Field(default=False)
    placeholder: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    help: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    search_config: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    model_id: int = Field(foreign_key="system_models.id")
    model: SystemModel = Relationship(back_populates="fields")

    def get_placeholder(self, lang: str = "es", fallback: str = "en") -> str:
        return self.placeholder.get(lang) or self.placeholder.get(fallback) or next(iter(self.placeholder.values()), "")

    def get_help(self, lang: str = "es", fallback: str = "en") -> str:
        return self.help.get(lang) or self.help.get(fallback) or next(iter(self.help.values()), "")


class SystemModelSchema(SystemAudit, SQLModel, table=True):
    __tablename__ = "system_model_schemas"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    name: str
    use: SystemModelSchemaUse = Field(
        default=SystemModelSchemaUse.view,
        sa_type=sa.Enum(
            SystemModelSchemaUse,
            name="system_model_schema_use",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            validate_strings=True,
        ),
    )
    view: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    model_id: int = Field(foreign_key="system_models.id")
    model: SystemModel = Relationship(back_populates="schemas")
