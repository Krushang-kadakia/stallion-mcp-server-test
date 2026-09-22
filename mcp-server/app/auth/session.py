from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class UserSession:
    session_id: str
    jwt_token: Optional[str] = None  # Single JWT Token received from client app
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_authenticated(self) -> bool:
        return self.jwt_token is not None

