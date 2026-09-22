from typing import Optional, Dict, Any
from app.auth.store import BaseSessionStore, InMemorySessionStore, default_session_store
from app.auth.session import UserSession
from app.client.backend_client import BackendClient
from app.config.settings import settings
from app.utils.errors import AuthenticationRequiredError
from app.utils.logging import get_logger

logger = get_logger("auth.manager")


class AuthManager:
    """
    Manages single JWT token session state received from external applications or request headers.
    """

    def __init__(self, store: Optional[BaseSessionStore] = None, client: Optional[BackendClient] = None):
        self.store = store or default_session_store
        self.client = client or BackendClient()

    async def get_or_create_session(self, session_id: str) -> UserSession:
        session = await self.store.get_session(session_id)
        if not session:
            session = UserSession(session_id=session_id)
            await self.store.save_session(session)
        return session

    async def set_jwt_token(self, session_id: str, jwt_token: str) -> UserSession:
        """Store single JWT token for a given session."""
        session = await self.get_or_create_session(session_id)
        session.jwt_token = jwt_token
        await self.store.save_session(session)
        logger.info(f"Updated single JWT token for session_id: {session_id}")
        return session

    async def get_jwt_token(self, session_id: str = "default_session", jwt_token: Optional[str] = None) -> str:
        """
        Retrieve the single JWT token for API calls.
        Precedence:
        1. Explicitly provided `jwt_token` argument
        2. Session-stored token for `session_id`
        3. Session-stored token for `default_session`
        4. Environment/Settings fallback `settings.jwt_token`
        """
        if jwt_token and jwt_token.strip():
            return jwt_token.strip()

        session = await self.store.get_session(session_id)
        if session and session.jwt_token:
            return session.jwt_token

        if session_id != "default_session":
            default_session = await self.store.get_session("default_session")
            if default_session and default_session.jwt_token:
                return default_session.jwt_token

        if settings.jwt_token and settings.jwt_token.strip():
            return settings.jwt_token.strip()

        raise AuthenticationRequiredError(
            "Authentication token missing. Please pass Authorization Bearer token header or jwt_token parameter."
        )


# Shared singleton auth manager instance for tools
default_auth_manager = AuthManager()


