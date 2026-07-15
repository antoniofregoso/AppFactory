# Access Control

The `access` domain implements role-based access control (RBAC) for every
current and future application domain. Permissions are not stored directly on
`user.user`, and the legacy `is_admin` flag is not used.

## Relationship model

```text
user_user
   └─ access_user_roles
         └─ access_roles
               └─ access_role_permissions
                     └─ access_permissions
```

| SQLModel class | Database table | Responsibility |
| --- | --- | --- |
| `UserUser` | `user_user` | Authenticated person or system identity |
| `AccessUserRole` | `access_user_roles` | Assigns a role to a user with a scope and optional dates |
| `AccessRole` | `access_roles` | Reusable collection of permissions, optionally owned by a company |
| `AccessRolePermission` | `access_role_permissions` | Many-to-many link between roles and permissions |
| `AccessPermission` | `access_permissions` | Atomic capability understood by backend services |

The persisted models are defined in
`backend/app/domains/access/models/access_control.py`.

## Permission convention

Permission codes use this format:

```text
<domain>.<resource>.<action>
```

Examples:

```text
talent.system.read
talent.area.create
talent.position.update
operations.order.approve
system.user.manage
system.insight.read
access.manage
```

Wildcard grants are hierarchical:

| Grant | Effect |
| --- | --- |
| `*` | Every permission in the platform |
| `talent.*` | Every permission whose code starts with `talent.` |
| `talent.area.*` | Every action for Talent areas |
| `talent.area.read` | Only the exact permission |

Only a user with global `access.manage` may create new permission definitions.
Adding a domain such as Operations does not require changing the access tables;
the domain registers permission codes such as `operations.order.read`.

## Assignment scopes

`AccessUserRole.scope_type` supports these values:

| Scope | Meaning |
| --- | --- |
| `GLOBAL` | Grant applies across the entire platform |
| `COMPANY` | Grant applies only to `company_id` |
| `MODEL` | Grant applies to a model identified by `scope_model` |
| `RECORD` | Grant applies to `scope_model` and `scope_record_uuid` |
| `OWN` | Reserved for policies that explicitly check record ownership |
| `ASSIGNED` | Reserved for policies that explicitly check record assignment |

For `MODEL` and `RECORD`, the calling domain passes its resource hierarchy as a
scope chain to `AccessService`. This keeps the access domain independent from
Talent, Operations, or any domain added later.

`OWN` and `ASSIGNED` are policy markers. They do not grant access automatically;
the domain service must verify the record's owner or assignee.

Assignments can be temporary using `date_start` and `date_end`. Inactive,
not-yet-started, and expired assignments are ignored.

## Bootstrap administrator

Clean database setup creates:

- Permission `*`.
- Role `platform_admin`.
- A `GLOBAL` assignment from `admin@app.com` to `platform_admin`.

The Alembic migration also converts every existing `user_user.is_admin=true`
account to this global role before dropping the old column.

## GraphQL API

All operations use `/graphql`, require a JWT, and require `access.manage`.
Company-scoped managers cannot manage another company. Creating permissions or
assigning a `GLOBAL` role additionally requires global `access.manage`.

### Read permissions and roles

```graphql
query AccessConfiguration {
  accessPermissions {
    uuid
    code
    domain
    resource
    action
    name
    description
    active
  }
  accessRoles {
    uuid
    companyId
    code
    name
    active
    permissions {
      uuid
      code
    }
  }
  accessUserRoles {
    uuid
    userUuid
    roleUuid
    companyId
    scopeType
    scopeModel
    scopeRecordUuid
    dateStart
    dateEnd
    active
  }
}
```

The authenticated user's effective permission codes are also returned by `me`:

```graphql
query Me {
  me {
    uuid
    name
    permissions
  }
}
```

### Create a permission

```graphql
mutation CreateTalentAreaReadPermission {
  createAccessPermission(input: {
    code: "talent.area.read"
    domain: "talent"
    resource: "area"
    action: "read"
    name: {es_MX: "Consultar áreas", en_US: "Read areas"}
    description: {es_MX: "Permite consultar áreas de talento"}
  }) {
    uuid
    code
  }
}
```

### Create a role

First obtain permission UUIDs with `accessPermissions`, then include them in the
role:

```graphql
mutation CreateTalentManager($permissionUuids: [UUID!]!) {
  createAccessRole(input: {
    code: "talent_manager"
    name: {es_MX: "Gerente de talento", en_US: "Talent manager"}
    description: {es_MX: "Administra talento dentro de su alcance"}
    permissionUuids: $permissionUuids
  }) {
    uuid
    code
    permissions { code }
  }
}
```

When `companyId` is omitted, the role belongs to the current user's company.

### Assign a role to a user

Company-wide assignment:

```graphql
mutation AssignCompanyRole($userUuid: UUID!, $roleUuid: UUID!) {
  assignAccessRole(input: {
    userUuid: $userUuid
    roleUuid: $roleUuid
    scopeType: COMPANY
  }) {
    uuid
    scopeType
    companyId
  }
}
```

Assignment to one Talent system:

```graphql
mutation AssignTalentSystemRole(
  $userUuid: UUID!
  $roleUuid: UUID!
  $systemUuid: UUID!
) {
  assignAccessRole(input: {
    userUuid: $userUuid
    roleUuid: $roleUuid
    scopeType: RECORD
    scopeModel: "talent.system"
    scopeRecordUuid: $systemUuid
  }) {
    uuid
    scopeType
    scopeModel
    scopeRecordUuid
  }
}
```

### Revoke an assignment

`recordUuid` is the UUID of `AccessUserRole`, not the user or role UUID.

```graphql
mutation RevokeRole($recordUuid: UUID!) {
  revokeAccessRole(recordUuid: $recordUuid)
}
```

## Backend enforcement

Resolvers authenticate the caller, but business services must enforce the
specific permission before reading or changing protected data:

```python
await AccessService.require(
    user,
    "talent.area.update",
    company_id=user.company_id,
    scope_chain=[("talent.system", system.uuid), ("talent.area", area.uuid)],
)
```

Frontend menu visibility is only a usability feature. It is never a substitute
for backend authorization.

### Sidebar visibility

Use `permission` in `frontend/src/app/data/sidebar.json`; do not use the legacy
`adminOnly` flag:

```json
{
  "key": "users",
  "labelEn": "Users",
  "labelEs": "Usuarios",
  "url": "/dashboard/configuration/user.user",
  "permission": "system.user.manage"
}
```

The sidebar accepts exact permissions and hierarchical grants such as
`system.*` and `*`. Submenu entries are filtered independently, and a parent is
hidden when none of its children are visible. The `permissions` array comes
from the authenticated GraphQL `me` query.

This only hides navigation. The resolver or service serving the destination
must enforce the same permission with `AccessService.require`.

## Adding a new system

For each new domain:

1. Define its permission vocabulary using `domain.resource.action`.
2. Create the permissions through GraphQL or the domain's seed loader.
3. Create reusable roles and link their permission UUIDs.
4. Assign roles to users with the narrowest useful scope.
5. Call `AccessService.require` from every protected backend operation.
6. Test denied access, company isolation, scoped access, and wildcard access.

Do not add boolean privilege fields to `UserUser` and do not rely exclusively on
frontend route or menu checks.
