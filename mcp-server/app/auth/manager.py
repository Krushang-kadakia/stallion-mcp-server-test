from app.auth.store import BaseSessionStore, InMemorySessionStore, default_session_store
from app.auth.session import UserSession
from app.client.backend_client import BackendClient
from app.utils.errors import AuthenticationRequiredError, ProjectContextRequiredError
from app.utils.logging import get_logger

logger = get_logger("auth.manager")


class AuthManager:
    """
    Manages user session state and token acquisition flows (OTP verification and project switching).
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

    async def send_otp(self, session_id: str, mobile_number: str) -> Dict[str, Any]:
        """Request login OTP code for mobile_number."""
        session = await self.get_or_create_session(session_id)
        session.mobile_number = mobile_number
        await self.store.save_session(session)

        response = await self.client.request(
            method="POST",
            path="/auth/send-otp",
            json_data={"mobile_number": mobile_number},
            is_auth_endpoint=True
        )
        logger.info(f"OTP requested for mobile number (session_id: {session_id})")
        return response

    async def verify_otp(self, session_id: str, mobile_number: str, code: str) -> Dict[str, Any]:
        """
        Verify OTP code. Returns response and stores Token 1 (authToken) in user session.
        """
        session = await self.get_or_create_session(session_id)

        response = await self.client.request(
            method="POST",
            path="/auth/verify-otp",
            json_data={"mobile_number": mobile_number, "code": code},
            is_auth_endpoint=True
        )

        data = response.get("data", {})
        token = data.get("token")
        user_info = data.get("user", {})

        if not token:
            raise AuthenticationRequiredError("Verification response did not contain a valid auth token.")

        session.mobile_number = mobile_number
        session.auth_token = token  # Token 1
        session.user_id = user_info.get("id")
        session.user_name = user_info.get("name")
        await self.store.save_session(session)

        logger.info(f"User authenticated successfully (session_id: {session_id}, user_id: {session.user_id})")

        # Clean token from response dict returned to callers to prevent accidental LLM logging
        sanitized_data = data.copy()
        if "token" in sanitized_data:
            sanitized_data["token"] = "[AUTHENTICATED_TOKEN_1]"
        return {"success": response.get("success", True), "message": response.get("message"), "data": sanitized_data}

    async def switch_project(self, session_id: str, project_id: str) -> Dict[str, Any]:
        """
        Switch active project context using Token 1. Returns response and stores Token 2 (projectToken).
        """
        session = await self.store.get_session(session_id)
        if not session or not session.is_authenticated():
            raise AuthenticationRequiredError("Authentication required before switching project context. Please run verify_otp first.")

        response = await self.client.request(
            method="POST",
            path=f"/auth/mobile/switch-by-project?= {project_id}",
            token=session.auth_token,
            json_data={"project_id": str(project_id)},
            is_auth_endpoint=True
        )

        data = response.get("data", {})
        project_token = data.get("token")
        if not project_token:
            raise ProjectContextRequiredError(f"Switch project response for project_id {project_id} did not contain a project token.")

        session.active_project_id = str(project_id)
        session.project_token = project_token  # Token 2
        await self.store.save_session(session)

        logger.info(f"Project context switched successfully (session_id: {session_id}, project_id: {project_id})")

        sanitized_data = data.copy()
        if "token" in sanitized_data:
            sanitized_data["token"] = f"[PROJECT_TOKEN_2_PROJECT_{project_id}]"
        return {"success": response.get("success", True), "message": response.get("message"), "data": sanitized_data}

    async def get_token_for_api(self, session_id: str, token_type: str = "authToken") -> str:
        """
        Retrieve the appropriate JWT token ('authToken' or 'projectToken') for an API request.
        """
        session = await self.store.get_session(session_id)
        if not session or not session.is_authenticated():
            raise AuthenticationRequiredError("User is not authenticated. Call send_otp and verify_otp first.")

        if token_type == "projectToken":
            if not session.project_token:
                raise ProjectContextRequiredError("Project context token required. Please call switch_project(project_id) first.")
            return session.project_token

        return session.auth_token  # default authToken (Token 1)


# Shared singleton auth manager instance for tools
default_auth_manager = AuthManager()

