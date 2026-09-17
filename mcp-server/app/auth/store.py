from abc import ABC, abstractmethod
from typing import Optional, Dict
from app.auth.session import UserSession
from app.utils.logging import get_logger

logger = get_logger("auth.store")


class BaseSessionStore(ABC):
    """
    Abstract interface for session storage.
    Enables swapping InMemorySessionStore with an encrypted RedisSessionStore in production.
    """

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Retrieve user session by session_id."""
        pass

    @abstractmethod
    async def save_session(self, session: UserSession) -> None:
        """Save or update user session."""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """Delete user session."""
        pass


class InMemorySessionStore(BaseSessionStore):
    """
    In-memory session store implementation for PoC testing.
    Keeps session data isolated per session_id without disk/DB persistence.
    """

    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        return self._sessions.get(session_id)

    async def save_session(self, session: UserSession) -> None:
        self._sessions[session.session_id] = session
        logger.debug(f"Saved session state for session_id: {session.session_id}")

    async def delete_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"Deleted session_id: {session_id}")


# Shared singleton session store instance for server runtime
default_session_store = InMemorySessionStore()

