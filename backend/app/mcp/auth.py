from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from app.core.security.jwt_manager import JWTManager
from app.core.exceptions import ResourceNotFoundException
from app.domains.users.models.user_user import UserUser
from app.domains.users.service.user_service import UserService


async def get_authenticated_user(ctx: Context) -> UserUser:
    """Autentica una llamada MCP a partir del header Authorization: Bearer <token-mcp>."""
    request = ctx.request_context.request
    authorization = request.headers.get("authorization", "") if request else ""

    if not authorization.startswith("Bearer "):
        raise ToolError("Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = JWTManager.verify_token(token, expected_token_type="mcp")
    except ValueError as exc:
        raise ToolError(str(exc)) from exc

    email = payload.get("sub")
    if not email:
        raise ToolError("Invalid token subject")

    try:
        user = await UserService.get_by_email(email)
    except ResourceNotFoundException as exc:
        raise ToolError("User not found") from exc

    if not user.active:
        raise ToolError("User account is disabled")

    # Re-checked on every call (not just when the token was issued) so that an
    # admin revoking mcp_access takes effect immediately, without waiting for
    # the 30-day token to expire.
    if not user.mcp_access:
        raise ToolError("MCP access has been revoked for this user")

    return user
