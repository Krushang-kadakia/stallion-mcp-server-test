import pytest
from app.auth.store import InMemorySessionStore
from app.auth.manager import AuthManager
from app.client.backend_client import BackendClient


@pytest.fixture
def session_store():
    return InMemorySessionStore()


@pytest.fixture
def backend_client():
    client = BackendClient(base_url="https://api.dev.batman.co.in")
    yield client


@pytest.fixture
def auth_manager(session_store, backend_client):
    return AuthManager(store=session_store, client=backend_client)
