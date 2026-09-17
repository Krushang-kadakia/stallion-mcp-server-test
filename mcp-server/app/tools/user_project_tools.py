from typing import Dict, Any, Optional
from app.auth.manager import default_auth_manager as auth_manager
from app.client.backend_client import BackendClient

backend_client = BackendClient()


async def get_user_profile_tool(session_id: str = "default_session") -> Dict[str, Any]:
    """
    Retrieve profile details, contact information, role, and context metrics of the authenticated user.

    Parameters:
    - session_id: Client session identifier.

    Returns:
    - Structured profile details including user ID, name, mobile, email, designation, and project list.
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="authToken")
    return await backend_client.request(method="GET", path="/auth/me", token=token)


async def get_user_projects_tool(session_id: str = "default_session") -> Dict[str, Any]:
    """
    Retrieve all projects accessible to the authenticated user.

    Parameters:
    - session_id: Client session identifier.

    Returns:
    - Structured list of projects with project ID, name, developer ID, location, status, and modules.
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="authToken")
    return await backend_client.request(method="GET", path="/projects/mobile", token=token)


async def get_project_details_tool(project_id: str, session_id: str = "default_session") -> Dict[str, Any]:
    """
    Retrieve comprehensive details, address, company info, and subscription status of a specific project.

    Parameters:
    - project_id: The ID of the project to inspect (string).
    - session_id: Client session identifier.

    Returns:
    - Project details including name, location, developer ID, contact info, society name, and RERA number.
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="projectToken")
    return await backend_client.request(method="GET", path=f"/projects/{project_id}", token=token)


async def get_project_towers_tool(project_id: str, session_id: str = "default_session") -> Dict[str, Any]:
    """
    Retrieve the list of towers belonging to a specific project.

    Parameters:
    - project_id: The ID of the project (string).
    - session_id: Client session identifier.

    Returns:
    - Structured list of towers including tower ID, name, floor count, basement count, and active status.
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="projectToken")
    return await backend_client.request(method="GET", path="/towers", params={"project_id": str(project_id)}, token=token)


async def get_notifications_tool(page: int = 0, limit: int = 15, session_id: str = "default_session") -> Dict[str, Any]:
    """
    Retrieve paginated system and activity notifications for the authenticated user.

    Parameters:
    - page: Zero-based page index for pagination (default: 0).
    - limit: Number of notifications per page (default: 15).
    - session_id: Client session identifier.

    Returns:
    - Paginated list of notifications with metadata (total, current_page, total_pages).
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="authToken")
    return await backend_client.request(method="GET", path="/notifications", params={"page": page, "limit": limit}, token=token)


async def get_assigned_modules_tool(session_id: str = "default_session") -> Dict[str, Any]:
    """
    Retrieve the list of licensed scope modules assigned for the current developer/project context.

    Parameters:
    - session_id: Client session identifier.

    Returns:
    - List of assigned modules (ID and module name, e.g., Legal, Permissions, RCC).
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="projectToken")
    return await backend_client.request(method="GET", path="/modules/assignable", token=token)


async def get_developer_users_tool(parent_developer_id: str, session_id: str = "default_session") -> Dict[str, Any]:
    """
    Retrieve the list of users and employees associated with a specific developer ID.

    Parameters:
    - parent_developer_id: The developer account ID (string).
    - session_id: Client session identifier.

    Returns:
    - Structured list of users/employees with ID, name, designation, role, email, and mobile number.
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="projectToken")
    return await backend_client.request(method="GET", path=f"/developers/{parent_developer_id}/users", token=token)


async def get_project_users_tool(project_id: str, session_id: str = "default_session") -> Dict[str, Any]:
    """
    Retrieve the list of users assigned to a particular project.

    Parameters:
    - project_id: The project ID (string).
    - session_id: Client session identifier.

    Returns:
    - List of project user objects containing user ID and name.
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="projectToken")
    return await backend_client.request(method="GET", path=f"/users/project/{project_id}", token=token)
