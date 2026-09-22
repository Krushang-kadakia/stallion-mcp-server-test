import pytest
from app.auth.manager import AuthManager
from app.auth.store import InMemorySessionStore
from app.auth.session import UserSession
from app.client.backend_client import BackendClient
from app.utils.errors import AuthenticationRequiredError


@pytest.mark.asyncio
async def test_session_store_isolation():
    store = InMemorySessionStore()

    session_1 = await store.get_session("session_1")
    assert session_1 is None

    s1 = UserSession(session_id="session_1", jwt_token="token_user_1")
    s2 = UserSession(session_id="session_2", jwt_token="token_user_2")

    await store.save_session(s1)
    await store.save_session(s2)

    res1 = await store.get_session("session_1")
    res2 = await store.get_session("session_2")

    assert res1.jwt_token == "token_user_1"
    assert res2.jwt_token == "token_user_2"
    assert res1.jwt_token != res2.jwt_token


@pytest.mark.asyncio
async def test_single_jwt_token_retrieval_and_overrides():
    client = BackendClient(base_url="https://api.dev.batman.co.in")
    store = InMemorySessionStore()
    manager = AuthManager(store=store, client=client)

    # 1. Without token, raises AuthenticationRequiredError
    with pytest.raises(AuthenticationRequiredError):
        await manager.get_jwt_token("sess_100")

    # 2. Explicit argument token override
    token_explicit = await manager.get_jwt_token("sess_100", jwt_token="override_jwt_123")
    assert token_explicit == "override_jwt_123"

    # 3. Store session token
    await manager.set_jwt_token("sess_100", "stored_jwt_456")
    token_stored = await manager.get_jwt_token("sess_100")
    assert token_stored == "stored_jwt_456"

    await client.close()

