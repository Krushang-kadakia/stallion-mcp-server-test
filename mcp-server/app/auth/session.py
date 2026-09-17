from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class UserSession:
    session_id: str
    mobile_number: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    auth_token: Optional[str] = None  # Token 1 (User Auth Token)
    active_project_id: Optional[str] = None
    project_token: Optional[str] = None  # Token 2 (Project Token)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_authenticated(self) -> bool:
        return self.auth_token is not None

    def has_project_context(self, project_id: Optional[str] = None) -> bool:
        if self.project_token is None:
            return False
        if project_id and self.active_project_id != str(project_id):
            return False
        return True
