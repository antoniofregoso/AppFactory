# MCP server (read-only reports)

The backend exposes a [Model Context Protocol](https://modelcontextprotocol.io)
server so MCP clients (e.g. Claude Desktop, or any client that supports a
remote Streamable HTTP server with custom headers) can connect and build
reports for directors: task status, team activity, and a users overview —
all scoped to the authenticated user's company. It is **read-only**: there
are no tools that create, update, or delete data.

- Endpoint: `POST/GET/DELETE /mcp` (Streamable HTTP transport), mounted on
  the same FastAPI app as `/graphql`.
- Implementation: `app/mcp/server.py` (tool definitions), `app/mcp/auth.py`
  (token check), `app/mcp/reports.py` (aggregation logic, framework-free so
  it's unit-testable without the MCP transport).

## 1. Grant access

Generating an MCP token requires `mcp_access = true` on the `UserUser` row.
By default no one has it (the seed admin gets it via `is_admin`/`mcp_access`
in `user_users.json`). An **admin** (`is_admin = true`) grants it to specific
users (e.g. directors) from the existing generic users screen
(`Configuration > Users` in the frontend, or the `updateSystemModelRecord`
GraphQL mutation) by toggling the "MCP access" checkbox on that user's
record. Only an admin can change `is_admin`, `mcp_access`, `active`, or
`email` on a `user.user` record — see
`app/domains/system/service/system_model_service.py:_require_admin_for_user_fields`.

## 2. Generate a token

MCP clients are usually configured once with a static header, so a normal
15-minute access token (`ACCESS_TOKEN_EXPIRE_MINUTES`) is impractical. Instead,
a user with `mcp_access = true` can mint a long-lived MCP token
(`MCP_TOKEN_EXPIRE_DAYS`, 30 days by default) via GraphQL:

```graphql
mutation {
  generateMcpToken
}
```

```http
Authorization: Bearer <your normal access token>
```

The response is the MCP token string. It is shown once and not stored in the
database — save it somewhere safe. It is a JWT signed with the same
`SECRET_KEY` as the rest of the app. `mcp_access` is re-checked on **every**
tool call (not just when the token was minted), so an admin unchecking "MCP
access" for a user takes effect immediately on their next tool call, even
before the 30-day token expires.

## 3. Configure your MCP client

Point your client at `https://<your-host>/mcp` and send the token as a
Bearer header. Example (Claude Desktop-style remote server config):

```json
{
  "mcpServers": {
    "webapp-reports": {
      "url": "https://your-host/mcp",
      "headers": {
        "Authorization": "Bearer <mcp-token>"
      }
    }
  }
}
```

## 4. Available tools

| Tool | Description |
|------|-------------|
| `get_tasks_report` | Totals by status/priority, overdue count, and up to 10 overdue tasks. |
| `get_team_activity_report` | Active users, sessions, and minutes connected over the last `days` (default 7). |
| `get_users_overview` | Company users with active/inactive state and last seen timestamp. |

All three infer the company from the authenticated user
(`UserUser.company_id`) — there is no cross-company access.

## Known limitations (phase 1)

- No frontend UI to generate/copy the token yet; use the GraphQL mutation
  directly (GraphQL Playground, Insomnia, curl, etc.).
- No write tools (e.g. creating a follow-up task from Claude).
- Company scoping is done in Python after loading rows via the existing
  repositories (`SystemTaskRepository.get_all()`, `UserRepository.get_all()`),
  since no repository filters by company at the query level today. Fine at
  template/demo scale; revisit if data volume grows.
- Revocation is per-user (`mcp_access = false`), not per-token — there is no
  way to revoke a single token while leaving the user's other tokens valid.
- There is no self-service password change flow; `updateSystemModelRecord`
  intentionally rejects `password` changes for `user.user` to avoid storing
  a plaintext password (see `system_model_service.py`).
