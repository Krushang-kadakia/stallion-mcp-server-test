import pytest
import respx
from httpx import Response
from app.client.backend_client import BackendClient
from app.utils.errors import BackendAPIError, MutatingOperationForbiddenError


@pytest.mark.asyncio
@respx.mock
async def test_backend_client_headers_and_errors():
    client = BackendClient(base_url="https://api.dev.batman.co.in")

    # Mock GET endpoint with token
    respx.get("https://api.dev.batman.co.in/projects/mobile").mock(
        return_value=Response(200, json={"success": True, "data": {"projects": []}})
    )

    res = await client.request("GET", "/projects/mobile", token="test_token_123")
    assert res["success"] is True

    # Test 401 Unauthorized handling
    respx.get("https://api.dev.batman.co.in/auth/me").mock(
        return_value=Response(401, json={"success": False, "message": "Unauthorized access"})
    )

    with pytest.raises(BackendAPIError) as exc_info:
        await client.request("GET", "/auth/me", token="invalid_token")
    assert exc_info.value.status_code == 401
    assert "Unauthorized access" in exc_info.value.message

    # Test Mutating Operation Forbidden for non-auth GET requirement
    with pytest.raises(MutatingOperationForbiddenError):
        await client.request("PUT", "/permissions/projects/194/1038", is_auth_endpoint=False)

    with pytest.raises(MutatingOperationForbiddenError):
        await client.request("POST", "/permissions/projects/194/1038/documents/upload", is_auth_endpoint=False)

    await client.close()
