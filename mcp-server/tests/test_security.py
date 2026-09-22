import logging
import pytest
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
async def test_jwt_auth_middleware():
    from app.main import JWTAuthMiddleware
    from app.auth.manager import default_auth_manager

    async def fake_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": b"OK"})

    mw = JWTAuthMiddleware(fake_app)
    received = []

    async def dummy_send(msg):
        received.append(msg)

    raw_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNDM5In0.secret"
    scope = {
        "type": "http",
        "headers": [
            (b"host", b"localhost:8000"),
            (b"authorization", f"Bearer {raw_jwt}".encode("latin1")),
            (b"x-session-id", b"sec_sess_99")
        ]
    }
    await mw(scope, None, dummy_send)

    token = await default_auth_manager.get_jwt_token("sec_sess_99")
    assert token == raw_jwt


@pytest.mark.asyncio
async def test_absolute_sse_endpoint_middleware():
    from app.main import AbsoluteSSEEndpointMiddleware

    async def fake_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/event-stream")]})
        await send({"type": "http.response.body", "body": b"event: endpoint\r\n", "more_body": True})
        await send({"type": "http.response.body", "body": b"data: /messages/?session_id=test_123\r\n\r\n", "more_body": False})

    mw = AbsoluteSSEEndpointMiddleware(fake_app)
    received = []

    async def dummy_send(msg):
        received.append(msg)

    scope = {
        "type": "http",
        "headers": [
            (b"host", b"stallion-mcp-server-test.onrender.com"),
            (b"x-forwarded-proto", b"https")
        ]
    }
    await mw(scope, None, dummy_send)

    body_chunks = [r["body"].decode("utf-8") for r in received if r.get("type") == "http.response.body"]
    assert len(body_chunks) == 2
    assert "event: endpoint" in body_chunks[0]
    assert "data: https://stallion-mcp-server-test.onrender.com/messages/?session_id=test_123" in body_chunks[1]


