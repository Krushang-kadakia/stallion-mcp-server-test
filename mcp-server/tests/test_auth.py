import pytest
import respx
from httpx import Response
from app.auth.manager import AuthManager
from app.auth.store import InMemorySessionStore
from app.client.backend_client import BackendClient
from app.utils.errors import AuthenticationRequiredError, ProjectContextRequiredError


@pytest.mark.asyncio
async def test_session_store_isolation():
    store = InMemorySessionStore()

    session_1 = await store.get_session("session_1")
    assert session_1 is None

    from app.auth.session import UserSession
    s1 = UserSession(session_id="session_1", auth_token="token_user_1")
    s2 = UserSession(session_id="session_2", auth_token="token_user_2")

    await store.save_session(s1)
    await store.save_session(s2)

    res1 = await store.get_session("session_1")
    res2 = await store.get_session("session_2")

    assert res1.auth_token == "token_user_1"
    assert res2.auth_token == "token_user_2"
    assert res1.auth_token != res2.auth_token


@pytest.mark.asyncio
@respx.mock
async def test_auth_flow_and_tokens():
    client = BackendClient(base_url="https://api.dev.batman.co.in")
    store = InMemorySessionStore()
    manager = AuthManager(store=store, client=client)

    # 1. Mock send OTP
    respx.post("https://api.dev.batman.co.in/auth/send-otp").mock(
        return_value=Response(200, json={"success": True, "message": "OTP Sent", "data": {"expires_in_seconds": 600}})
    )

    send_res = await manager.send_otp("sess_100", "8291598930")
    assert send_res["success"] is True

    # 2. Mock verify OTP
    respx.post("https://api.dev.batman.co.in/auth/verify-otp").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "message": "Login successfull",
                "data": {
                    "token": "mock_jwt_token_1",
                    "user": {"id": "439", "name": "Krushang"}
                }
            }
        )
    )

    verify_res = await manager.verify_otp("sess_100", "8291598930", "1234")
    assert verify_res["success"] is True

    token_1 = await manager.get_token_for_api("sess_100", token_type="authToken")
    assert token_1 == "mock_jwt_token_1"

    # Attempting to get project token before switch should fail
    with pytest.raises(ProjectContextRequiredError):
        await manager.get_token_for_api("sess_100", token_type="projectToken")

    # 3. Mock switch project
    respx.post("https://api.dev.batman.co.in/auth/mobile/switch-by-project?= 194").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "message": "Login successfull",
                "data": {
                    "token": "mock_project_token_2",
                    "user": {"id": "291", "developer_id": "287"}
                }
            }
        )
    )

    switch_res = await manager.switch_project("sess_100", "194")
    assert switch_res["success"] is True

    token_2 = await manager.get_token_for_api("sess_100", token_type="projectToken")
    assert token_2 == "mock_project_token_2"

    await client.close()
