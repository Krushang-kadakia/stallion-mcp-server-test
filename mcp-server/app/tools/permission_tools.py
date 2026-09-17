from typing import Dict, Any
from app.auth.manager import default_auth_manager as auth_manager
from app.client.backend_client import BackendClient

backend_client = BackendClient()


async def get_project_permissions_tool(project_id: str, session_id: str = "default_session") -> Dict[str, Any]:
    """
    Retrieve all permissions, status flags, expiry dates, attachments, and LOD documents for a project.

    Parameters:
    - project_id: The ID of the project to retrieve permissions for (string).
    - session_id: Client session identifier.

    Returns:
    - Detailed permissions array containing permission ID, status (Issued, In Process, Applied, Payment Due, etc.),
      expiry dates, assigned user, remarks, category attachments, and LOD documents.
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="projectToken")
    return await backend_client.request(
        method="GET",
        path=f"/permissions/projects/{project_id}",
        token=token
    )


async def view_permission_document_tool(
    project_id: str,
    trans_project_per_id: str,
    file_id: str,
    session_id: str = "default_session"
) -> Dict[str, Any]:
    """
    Retrieve document reference metadata and view URL for a sub-permission document or attachment.

    Parameters:
    - project_id: The project ID (string).
    - trans_project_per_id: The permission transaction record ID (string).
    - file_id: The target document file ID (string).
    - session_id: Client session identifier.

    Returns:
    - Document metadata and view URL reference.
    """
    token = await auth_manager.get_token_for_api(session_id, token_type="projectToken")
    return await backend_client.request(
        method="GET",
        path=f"/permissions/projects/{project_id}/{trans_project_per_id}/documents/{file_id}/view",
        token=token
    )
