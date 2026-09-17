import pytest
import respx
from httpx import Response
from app.auth.manager import AuthManager
from app.auth.store import InMemorySessionStore
from app.client.backend_client import BackendClient
from app.tools import auth_tools, user_project_tools, permission_tools


@pytest.mark.asyncio
@respx.mock
async def test_tool_invocations():
    store = InMemorySessionStore()
    client = BackendClient(base_url="https://api.dev.batman.co.in")
    manager = AuthManager(store=store, client=client)

    auth_tools.auth_manager = manager
    user_project_tools.auth_manager = manager
    user_project_tools.backend_client = client
    permission_tools.auth_manager = manager
    permission_tools.backend_client = client

    # Seed authenticated session
    from app.auth.session import UserSession
    session = UserSession(
        session_id="test_tool_session",
        auth_token="valid_user_token_1",
        active_project_id="194",
        project_token="valid_project_token_2"
    )
    await store.save_session(session)

    # 1. send_otp_tool & verify_otp_tool
    respx.post("https://api.dev.batman.co.in/auth/send-otp").mock(
        return_value=Response(200, json={"success": True, "message": "OTP Sent"})
    )
    send_res = await auth_tools.send_otp_tool("8291598930", "test_tool_session")
    assert send_res["success"] is True

    respx.post("https://api.dev.batman.co.in/auth/verify-otp").mock(
        return_value=Response(200, json={"success": True, "data": {"token": "t1", "user": {"id": "1"}}})
    )
    ver_res = await auth_tools.verify_otp_tool("8291598930", "1234", "test_tool_session")
    assert ver_res["success"] is True

    respx.post("https://api.dev.batman.co.in/auth/mobile/switch-by-project?= 194").mock(
        return_value=Response(200, json={"success": True, "data": {"token": "t2"}})
    )
    switch_res = await auth_tools.switch_project_tool("194", "test_tool_session")
    assert switch_res["success"] is True

    # 2. get_user_profile (Token 1)
    respx.get("https://api.dev.batman.co.in/auth/me").mock(
        return_value=Response(200, json={"success": True, "data": {"id": "439", "name": "Krushang"}})
    )
    profile_res = await user_project_tools.get_user_profile_tool("test_tool_session")
    assert profile_res["data"]["id"] == "439"

    # 3. get_user_projects (Token 1)
    respx.get("https://api.dev.batman.co.in/projects/mobile").mock(
        return_value=Response(200, json={"success": True, "data": {"total_projects": 1, "projects": [{"id": "194", "name": "Sharda Project"}]}})
    )
    projects_res = await user_project_tools.get_user_projects_tool("test_tool_session")
    assert projects_res["success"] is True

    # 4. get_project_details (Token 2)
    respx.get("https://api.dev.batman.co.in/projects/194").mock(
        return_value=Response(200, json={"success": True, "data": {"id": "194", "name": "Sharda Project"}})
    )
    details_res = await user_project_tools.get_project_details_tool("194", "test_tool_session")
    assert details_res["data"]["name"] == "Sharda Project"

    # 5. get_project_towers (Token 2)
    respx.get("https://api.dev.batman.co.in/towers?project_id=194").mock(
        return_value=Response(200, json={"success": True, "data": [{"id": "159", "name": "Tower Name 2"}]})
    )
    towers_res = await user_project_tools.get_project_towers_tool("194", "test_tool_session")
    assert towers_res["success"] is True

    # 6. get_notifications (Token 1)
    respx.get("https://api.dev.batman.co.in/notifications?page=0&limit=15").mock(
        return_value=Response(200, json={"success": True, "data": {"notifications": []}})
    )
    notif_res = await user_project_tools.get_notifications_tool(0, 15, "test_tool_session")
    assert notif_res["success"] is True

    # 7. get_assigned_modules (Token 2)
    respx.get("https://api.dev.batman.co.in/modules/assignable").mock(
        return_value=Response(200, json={"success": True, "data": [{"id": "58", "name": "Permissions"}]})
    )
    modules_res = await user_project_tools.get_assigned_modules_tool("test_tool_session")
    assert modules_res["success"] is True

    # 8. get_developer_users (Token 2)
    respx.get("https://api.dev.batman.co.in/developers/287/users").mock(
        return_value=Response(200, json={"success": True, "data": [{"id": "288", "name": "Karn Barnwal"}]})
    )
    dev_users_res = await user_project_tools.get_developer_users_tool("287", "test_tool_session")
    assert dev_users_res["success"] is True

    # 9. get_project_users (Token 2)
    respx.get("https://api.dev.batman.co.in/users/project/194").mock(
        return_value=Response(200, json={"success": True, "data": [{"id": "322", "name": "Ali Khan"}]})
    )
    proj_users_res = await user_project_tools.get_project_users_tool("194", "test_tool_session")
    assert proj_users_res["success"] is True

    # 10. get_project_permissions (Token 2)
    respx.get("https://api.dev.batman.co.in/permissions/projects/194").mock(
        return_value=Response(200, json={"success": True, "data": {"total_permissions": 2, "permissions": [{"id": "1038", "name": "Last Approved Plan"}]}})
    )
    perm_res = await permission_tools.get_project_permissions_tool("194", "test_tool_session")
    assert perm_res["success"] is True

    # 11. view_permission_document (Token 2)
    respx.get("https://api.dev.batman.co.in/permissions/projects/194/1038/documents/946/view").mock(
        return_value=Response(200, json={"success": True, "data": {"file_id": "946", "view_url": "/permissions/..."}})
    )
    doc_res = await permission_tools.view_permission_document_tool("194", "1038", "946", "test_tool_session")
    assert doc_res["success"] is True

    await client.close()
