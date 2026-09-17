from mcp.server.fastmcp import FastMCP
from app.config.settings import settings
from app.tools.auth_tools import send_otp_tool, verify_otp_tool, switch_project_tool
from app.tools.user_project_tools import (
    get_user_profile_tool,
    get_user_projects_tool,
    get_project_details_tool,
    get_project_towers_tool,
    get_notifications_tool,
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

# --- Register Auth Tools ---
mcp.tool(
    name="send_otp",
    description="Send a login OTP code to user's mobile number."
)(send_otp_tool)

mcp.tool(
    name="verify_otp",
    description="Verify OTP code and authenticate user session."
)(verify_otp_tool)

mcp.tool(
    name="switch_project",
    description="Switch active project context and acquire project authorization."
)(switch_project_tool)

# --- Register User & Core Project Tools ---
mcp.tool(
    name="get_user_profile",
    description="Retrieve profile details of the authenticated user."
)(get_user_profile_tool)

mcp.tool(
    name="get_user_projects",
    description="Retrieve list of all accessible projects for the user."
)(get_user_projects_tool)

mcp.tool(
    name="get_project_details",
    description="Retrieve detailed specifications and metadata of a specific project."
)(get_project_details_tool)

mcp.tool(
    name="get_project_towers",
    description="Retrieve list of towers for a project."
)(get_project_towers_tool)

mcp.tool(
    name="get_notifications",
    description="Retrieve paginated notifications for the user."
)(get_notifications_tool)

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

# --- Register Permission Module Tools ---
mcp.tool(
    name="get_project_permissions",
    description="Retrieve permissions, categories, attachments, and LOD documents for a project."
)(get_project_permissions_tool)

mcp.tool(
    name="view_permission_document",
    description="Retrieve view URL reference for a permission document attachment."
)(view_permission_document_tool)


if __name__ == "__main__":
    logger.info(f"Starting Stallion MCP Server on {settings.host}:{settings.port} (SSE Transport)")
    mcp.run(transport="sse")

