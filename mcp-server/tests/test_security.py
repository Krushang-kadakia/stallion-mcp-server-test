import logging
import io
import pytest
import respx
from httpx import Response
from app.utils.logging import SecretMaskingFormatter
from app.auth.manager import AuthManager
from app.auth.store import InMemorySessionStore
from app.client.backend_client import BackendClient


def test_jwt_log_masking():
    formatter = SecretMaskingFormatter("%(message)s")
    jwt_sample = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNDM5In0.signature"
    log_msg = f"User token is {jwt_sample} in session."
    record = logging.LogRecord("test", logging.INFO, "", 0, log_msg, (), None)

    formatted = formatter.format(record)
    assert jwt_sample not in formatted
    assert "[REDACTED_JWT]" in formatted


@pytest.mark.asyncio
@respx.mock
async def test_token_sanitization_in_verify_otp():
    client = BackendClient(base_url="https://api.dev.batman.co.in")
    store = InMemorySessionStore()
    manager = AuthManager(store=store, client=client)

    raw_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNDM5In0.secret"
    respx.post("https://api.dev.batman.co.in/auth/verify-otp").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "message": "Login successfull",
                "data": {"token": raw_jwt, "user": {"id": "439"}}
            }
        )
    )

    res = await manager.verify_otp("sec_sess", "8291598930", "1234")
    # Verify raw JWT is NOT present in returned data payload
    assert raw_jwt not in str(res)
    assert res["data"]["token"] == "[AUTHENTICATED_TOKEN_1]"

    # Verify session store DOES contain the actual token for backend API use
    session = await store.get_session("sec_sess")
    assert session.auth_token == raw_jwt

    await client.close()
