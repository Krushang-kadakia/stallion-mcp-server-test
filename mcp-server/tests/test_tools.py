import pytest
import respx
from httpx import Response
from app.auth.manager import AuthManager
from app.auth.store import InMemorySessionStore
from app.client.backend_client import BackendClient
from app.tools import user_project_tools, permission_tools


@pytest.mark.asyncio
@respx.mock
async def test_tool_invocations():
    store = InMemorySessionStore()
    client = BackendClient(base_url="https://api.dev.batman.co.in")
    manager = AuthManager(store=store, client=client)

    user_project_tools.auth_manager = manager
    user_project_tools.backend_client = client
    permission_tools.auth_manager = manager
    permission_tools.backend_client = client

    # Seed authenticated session with single JWT token
    from app.auth.session import UserSession
    session = UserSession(
        session_id="test_tool_session",
        jwt_token="valid_single_jwt_token"
    )
    await store.save_session(session)

    # 1. get_user_profile
    respx.get("https://api.dev.batman.co.in/auth/me").mock(
        return_value=Response(200, json={"success": True, "data": {"id": "439", "name": "Krushang"}})
    )
    profile_res = await user_project_tools.get_user_profile_tool(session_id="test_tool_session")
    assert profile_res["data"]["id"] == "439"

    # 2. get_project_details
    respx.get("https://api.dev.batman.co.in/projects/194").mock(
        return_value=Response(200, json={"success": True, "data": {"id": "194", "name": "Sharda Project"}})
    )
    details_res = await user_project_tools.get_project_details_tool("194", session_id="test_tool_session")
    assert details_res["data"]["name"] == "Sharda Project"

    # 3. get_project_towers
    respx.get("https://api.dev.batman.co.in/towers?project_id=194").mock(
        return_value=Response(200, json={"success": True, "data": [{"id": "159", "name": "Tower Name 2"}]})
    )
    towers_res = await user_project_tools.get_project_towers_tool("194", session_id="test_tool_session")
    assert towers_res["success"] is True

    # 4. get_assigned_modules
    respx.get("https://api.dev.batman.co.in/modules/assignable").mock(
        return_value=Response(200, json={"success": True, "data": [{"id": "58", "name": "Permissions"}]})
    )
    modules_res = await user_project_tools.get_assigned_modules_tool(session_id="test_tool_session")
    assert modules_res["success"] is True

    # 5. get_developer_users
    respx.get("https://api.dev.batman.co.in/developers/287/users").mock(
        return_value=Response(200, json={"success": True, "data": [{"id": "288", "name": "Karn Barnwal"}]})
    )
    dev_users_res = await user_project_tools.get_developer_users_tool("287", session_id="test_tool_session")
    assert dev_users_res["success"] is True

    # 6. get_project_users
    respx.get("https://api.dev.batman.co.in/users/project/194").mock(
        return_value=Response(200, json={"success": True, "data": [{"id": "322", "name": "Ali Khan"}]})
    )
    proj_users_res = await user_project_tools.get_project_users_tool("194", session_id="test_tool_session")
    assert proj_users_res["success"] is True

    # 7. get_project_permissions
    respx.get("https://api.dev.batman.co.in/permissions/projects/194").mock(
        return_value=Response(200, json={"success": True, "data": {"total_permissions": 2, "permissions": [{"id": "1038", "name": "Last Approved Plan"}]}})
    )
    perm_res = await permission_tools.get_project_permissions_tool("194", session_id="test_tool_session")
    assert perm_res["success"] is True

    # 8. view_permission_document (JSON with relative URL)
    respx.get("https://api.dev.batman.co.in/permissions/projects/194/1038/documents/946/view").mock(
        return_value=Response(200, json={"success": True, "data": {"file_id": "946", "view_url": "/permissions/projects/194/1038/documents/946/view"}})
    )
    doc_res = await permission_tools.view_permission_document_tool("194", "1038", "946", session_id="test_tool_session")
    assert doc_res["success"] is True
    assert doc_res["data"]["view_url"].startswith("https://api.dev.batman.co.in")

    # 9. view_permission_document (explicit jwt_token parameter override)
    respx.get("https://api.dev.batman.co.in/permissions/projects/194/1038/documents/947/view").mock(
        return_value=Response(
            200,
            content=b"dummy binary dwg content",
            headers={
                "content-type": "image/vnd.dwg",
                "content-disposition": 'attachment; filename="structure_drawing.dwg"'
            }
        )
    )
    binary_res = await permission_tools.view_permission_document_tool("194", "1038", "947", jwt_token="explicit_token_override")
    assert binary_res["success"] is True
    assert binary_res["is_binary"] is True

    await client.close()

