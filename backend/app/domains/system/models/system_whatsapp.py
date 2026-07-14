import enum
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy import DateTime
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel

from app.domains.system.models.system_audit import SystemAudit

if TYPE_CHECKING:
    from app.domains.system.models.system_company import SystemCompany


class WhatsAppMessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class WhatsAppMessageStatus(str, enum.Enum):
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


class WhatsAppTemplateCategory(str, enum.Enum):
    marketing = "marketing"
    utility = "utility"
    authentication = "authentication"


class WhatsAppTemplateStatus(str, enum.Enum):
    approved = "approved"
    pending = "pending"
    rejected = "rejected"
    disabled = "disabled"
    paused = "paused"


class SystemWhatsApp(SystemAudit, SQLModel, table=True):
    """WhatsApp Business configuration owned by one company."""

    __tablename__ = "system_whatsapp"
    __table_args__ = (
        sa.UniqueConstraint(
            "company_id",
            "phone_number_id",
            name="uq_system_whatsapp_company_phone_number_id",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    company_id: int = Field(
        foreign_key="system_companies.id",
        nullable=False,
        index=True,
    )
    name: str = Field(max_length=100, nullable=False)
    active: bool = Field(default=True, nullable=False)
    phone_number: str = Field(max_length=32, nullable=False)
    phone_number_id: str = Field(max_length=64, nullable=False)
    business_account_id: str = Field(max_length=64, nullable=False)
    api_version: Optional[str] = Field(default=None, max_length=16)
    access_token: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text(), nullable=True),
    )
    verify_token: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text(), nullable=True),
    )
    app_secret: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text(), nullable=True),
    )
    webhook_url: Optional[str] = Field(default=None, max_length=512)

    company: "SystemCompany" = Relationship(back_populates="whatsapp_configurations")
    messages: list["SystemWhatsAppMessage"] = Relationship(
        back_populates="whatsapp",
        cascade_delete=True,
    )
    templates: list["SystemWhatsAppTemplate"] = Relationship(
        back_populates="whatsapp",
        cascade_delete=True,
    )


class SystemWhatsAppTemplate(SystemAudit, SQLModel, table=True):
    """Meta-approved message template required to open a WhatsApp conversation.

    Business-initiated messages sent outside the 24-hour customer service
    window must use a template pre-approved by Meta; this mirrors the
    template resource returned by the WhatsApp Business Management API.
    """

    __tablename__ = "system_whatsapp_templates"
    __table_args__ = (
        sa.UniqueConstraint(
            "whatsapp_id",
            "name",
            "language",
            name="uq_system_whatsapp_templates_whatsapp_name_language",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    whatsapp_id: int = Field(
        foreign_key="system_whatsapp.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    external_template_id: Optional[str] = Field(default=None, max_length=64)
    namespace: Optional[str] = Field(default=None, max_length=64)
    name: str = Field(max_length=512, nullable=False)
    language: str = Field(max_length=16, nullable=False)
    category: WhatsAppTemplateCategory = Field(
        default=WhatsAppTemplateCategory.utility,
        sa_column=sa.Column(
            sa.String(16),
            nullable=False,
            server_default=WhatsAppTemplateCategory.utility.value,
        ),
    )
    status: WhatsAppTemplateStatus = Field(
        default=WhatsAppTemplateStatus.pending,
        sa_column=sa.Column(
            sa.String(16),
            nullable=False,
            server_default=WhatsAppTemplateStatus.pending.value,
        ),
    )
    components: dict = Field(
        default_factory=dict,
        sa_column=Column(
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    rejected_reason: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text(), nullable=True),
    )
    active: bool = Field(default=True, nullable=False)

    whatsapp: SystemWhatsApp = Relationship(back_populates="templates")
    messages: list["SystemWhatsAppMessage"] = Relationship(back_populates="template")


class SystemWhatsAppMessage(SystemAudit, SQLModel, table=True):
    """Inbound or outbound WhatsApp message and its provider payload."""

    __tablename__ = "system_whatsapp_messages"
    __table_args__ = (
        sa.Index(
            "ix_system_whatsapp_messages_record",
            "model_id",
            "record_uuid",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        sa_column_kwargs={
            "server_default": sa_text("gen_random_uuid()"),
            "unique": True,
        },
        index=True,
    )
    whatsapp_id: int = Field(
        foreign_key="system_whatsapp.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    external_message_id: Optional[str] = Field(
        default=None,
        max_length=255,
        unique=True,
        index=True,
    )
    model_id: Optional[int] = Field(
        default=None,
        foreign_key="system_models.id",
        nullable=True,
    )
    record_uuid: Optional[uuid_lib.UUID] = Field(default=None, nullable=True)
    template_id: Optional[int] = Field(
        default=None,
        foreign_key="system_whatsapp_templates.id",
        nullable=True,
        ondelete="SET NULL",
    )
    direction: WhatsAppMessageDirection = Field(
        default=WhatsAppMessageDirection.outbound,
        sa_column=sa.Column(
            sa.String(16),
            nullable=False,
            server_default=WhatsAppMessageDirection.outbound.value,
        ),
    )
    status: WhatsAppMessageStatus = Field(
        default=WhatsAppMessageStatus.queued,
        sa_column=sa.Column(
            sa.String(16),
            nullable=False,
            server_default=WhatsAppMessageStatus.queued.value,
        ),
    )
    message_type: str = Field(default="text", max_length=32, nullable=False)
    from_number: str = Field(max_length=32, nullable=False)
    to_number: str = Field(max_length=32, nullable=False)
    body: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text(), nullable=True),
    )
    payload: dict = Field(
        default_factory=dict,
        sa_column=Column(
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": sa_text("CURRENT_TIMESTAMP")},
    )
    error_message: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text(), nullable=True),
    )

    whatsapp: SystemWhatsApp = Relationship(back_populates="messages")
    template: Optional["SystemWhatsAppTemplate"] = Relationship(
        back_populates="messages"
    )
