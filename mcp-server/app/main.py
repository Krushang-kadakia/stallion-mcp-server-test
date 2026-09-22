from mcp.server.fastmcp import FastMCP
from app.config.settings import settings
from app.auth.manager import default_auth_manager as auth_manager
from app.tools.user_project_tools import (
    get_user_profile_tool,
    get_project_details_tool,
    get_project_towers_tool,
    get_assigned_modules_tool,
    get_developer_users_tool,
    get_project_users_tool,
)
from app.tools.permission_tools import (
    get_project_permissions_tool,
    view_permission_document_tool,
)
from app.utils.logging import get_logger

logger = get_logger("main")

# Initialize FastMCP Server
mcp = FastMCP(
    "Stallion MCP Server",
    host=settings.host,
    port=settings.port,
)

# Disable local-only DNS rebinding restrictions so remote deployment hosts (Render, Cloudflare, Clients) can connect
if hasattr(mcp.settings, "transport_security") and mcp.settings.transport_security is not None:
    mcp.settings.transport_security.enable_dns_rebinding_protection = False
else:
    try:
        from mcp.server.transport_security import TransportSecuritySettings
        mcp.settings.transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    except Exception:
        pass


# --- Register 8 Authorized Tools ---
mcp.tool(
    name="get_user_profile",
    description="Retrieve profile details of the authenticated user."
)(get_user_profile_tool)

mcp.tool(
    name="get_project_details",
    description="Retrieve detailed specifications and metadata of a specific project."
)(get_project_details_tool)

mcp.tool(
    name="get_project_towers",
    description="Retrieve list of towers for a project."
)(get_project_towers_tool)

mcp.tool(
    name="get_assigned_modules",
    description="Retrieve list of assigned developer modules."
)(get_assigned_modules_tool)

mcp.tool(
    name="get_developer_users",
    description="Retrieve list of users/employees for a developer."
)(get_developer_users_tool)

mcp.tool(
    name="get_project_users",
    description="Retrieve list of users assigned to a project."
)(get_project_users_tool)

mcp.tool(
    name="get_project_permissions",
    description="Retrieve permissions, categories, attachments, and LOD documents for a project."
)(get_project_permissions_tool)

mcp.tool(
    name="view_permission_document",
    description="Retrieve view URL reference for a permission document attachment."
)(view_permission_document_tool)


import re
from starlette.middleware.cors import CORSMiddleware
import uvicorn


class JWTAuthMiddleware:
    """
    ASGI middleware extracting Bearer JWT token from HTTP Authorization or X-JWT-Token header
    and populating the session store for incoming tool requests.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = {}
            for k, v in scope.get("headers", []):
                headers[k.lower().decode("latin1")] = v.decode("latin1")

            auth_header = headers.get("authorization", "") or headers.get("x-jwt-token", "")
            token = None
            if auth_header.lower().startswith("bearer "):
                token = auth_header[7:].strip()
            elif auth_header:
                token = auth_header.strip()

            if token:
                session_id = headers.get("x-session-id", "default_session")
                await auth_manager.set_jwt_token(session_id, token)

        await self.app(scope, receive, send)


class AbsoluteSSEEndpointMiddleware:
    """
    ASGI middleware ensuring SSE endpoint event contains the absolute public HTTPS URL.
    This enables remote web clients (MCP Inspector web UI, Claude, ChatGPT) to POST messages correctly.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {}
        for k, v in scope.get("headers", []):
            headers[k.lower().decode("latin1")] = v.decode("latin1")

        proto = headers.get("x-forwarded-proto", "http").split(",")[0].strip()
        host = headers.get("x-forwarded-host", headers.get("host", "localhost:8000")).split(",")[0].strip()

        # Enforce https for remote cloud deployments (e.g. Render)
        if host.endswith(".onrender.com") or headers.get("x-forwarded-ssl") == "on":
            proto = "https"

        base_url = f"{proto}://{host}"

        async def send_wrapper(message):
            if message.get("type") == "http.response.body":
                body = message.get("body", b"")
                if b"data: /" in body:
                    text = body.decode("utf-8", errors="ignore")
                    text = re.sub(r"data: /(?!/)", f"data: {base_url}/", text)
                    message = dict(message)
                    message["body"] = text.encode("utf-8")
            await send(message)

        await self.app(scope, receive, send_wrapper)


# Create Starlette ASGI application with CORS, JWT Auth, and Absolute SSE Endpoint Middleware
app = mcp.sse_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(AbsoluteSSEEndpointMiddleware)

if __name__ == "__main__":
    logger.info(f"Starting Stallion MCP Server on {settings.host}:{settings.port} (SSE Transport with CORS & Single JWT Auth)")
    uvicorn.run(app, host=settings.host, port=settings.port, proxy_headers=True, forwarded_allow_ips="*")




