from app.domains.system.graphql.types import (
    SystemMessageType,
    SystemModelFieldType,
    SystemModelSchemaType,
    SystemModelType,
    SystemNotificationType,
    SystemTaskType,
    SystemUserRefType,
    SystemWhatsAppMessageType,
    SystemWhatsAppTemplateType,
    SystemWhatsAppType,
)


def user_to_type(user):
    if not user:
        return None
    return SystemUserRefType(uuid=user.uuid, name=user.name, email=user.email)


def system_model_to_type(system_model):
    return SystemModelType(
        uuid=system_model.uuid,
        name=system_model.name,
        fields=[
            SystemModelFieldType(
                uuid=field.uuid,
                name=field.name,
                sequence=field.sequence,
                type=field.type,
                required=field.required,
                readonly=field.readonly,
                placeholder=field.placeholder,
                help=field.help,
                search_config=field.search_config,
            )
            for field in system_model.fields
        ],
        search=system_model.search,
        readonly=system_model.readonly,
        schemas=[
            SystemModelSchemaType(
                uuid=schema.uuid,
                name=schema.name,
                use=schema.use,
                view=schema.view,
            )
            for schema in system_model.schemas
        ],
        created_at=system_model.created_at,
    )


def system_message_to_type(message):
    return SystemMessageType(
        uuid=message.uuid,
        status=message.status,
        date=message.date,
        subject=message.subject,
        message=message.message,
        from_user=user_to_type(message.from_user),
        to_users=[user_to_type(user) for user in message.to_users],
        created_at=message.created_at,
    )


def system_notification_to_type(notification):
    return SystemNotificationType(
        uuid=notification.uuid,
        date=notification.date,
        status=notification.status,
        title=notification.title,
        message=notification.message,
        read=notification.read,
        active=notification.active,
        sequence=notification.sequence,
        color=notification.color,
        priority=notification.priority,
        user=user_to_type(notification.user),
        users=[user_to_type(user) for user in notification.users],
        created_at=notification.created_at,
    )


def system_task_to_type(task):
    return SystemTaskType(
        uuid=task.uuid,
        status=task.status,
        color=task.color,
        sequence=task.sequence,
        title=task.title,
        description=task.description,
        priority=task.priority,
        date_assign=task.date_assign,
        date_due=task.date_due,
        user=user_to_type(task.user),
        created_at=task.created_at,
    )


def system_whatsapp_to_type(whatsapp):
    return SystemWhatsAppType(
        uuid=whatsapp.uuid,
        name=whatsapp.name,
        active=whatsapp.active,
        phone_number=whatsapp.phone_number,
        phone_number_id=whatsapp.phone_number_id,
        business_account_id=whatsapp.business_account_id,
        api_version=whatsapp.api_version,
        webhook_url=whatsapp.webhook_url,
        created_at=whatsapp.created_at,
    )


def system_whatsapp_template_to_type(template):
    return SystemWhatsAppTemplateType(
        uuid=template.uuid,
        name=template.name,
        language=template.language,
        category=template.category,
        status=template.status,
        external_template_id=template.external_template_id,
        namespace=template.namespace,
        components=template.components,
        rejected_reason=template.rejected_reason,
        active=template.active,
        created_at=template.created_at,
    )


def system_whatsapp_message_to_type(message):
    return SystemWhatsAppMessageType(
        uuid=message.uuid,
        direction=message.direction,
        status=message.status,
        message_type=message.message_type,
        from_number=message.from_number,
        to_number=message.to_number,
        body=message.body,
        payload=message.payload,
        date=message.date,
        error_message=message.error_message,
        template_uuid=message.template.uuid if message.template else None,
        created_at=message.created_at,
    )
