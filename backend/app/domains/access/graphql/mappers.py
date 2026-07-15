from app.domains.access.graphql.types import AccessPermissionType, AccessRoleType, AccessUserRoleType


def permission_type(record):
    return AccessPermissionType(uuid=record.uuid, code=record.code, domain=record.domain, resource=record.resource, action=record.action, name=record.name, description=record.description, active=record.active)


def role_type(record, permissions):
    return AccessRoleType(uuid=record.uuid, company_id=record.company_id, code=record.code, name=record.name, description=record.description, active=record.active, sequence=record.sequence, permissions=[permission_type(item) for item in permissions])


def user_role_type(record, user_uuid, role_uuid):
    return AccessUserRoleType(uuid=record.uuid, user_uuid=user_uuid, role_uuid=role_uuid, company_id=record.company_id, scope_type=record.scope_type, scope_model=record.scope_model, scope_record_uuid=record.scope_record_uuid, date_start=record.date_start, date_end=record.date_end, active=record.active)
