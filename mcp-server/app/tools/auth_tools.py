from typing import Dict, Any
from app.auth.manager import default_auth_manager as auth_manager




async def send_otp_tool(mobile_number: str, session_id: str = "default_session") -> Dict[str, Any]:
    """
    Request a login OTP code to be sent to the user's mobile number.

    Parameters:
    - mobile_number: User's registered mobile number (string).
    - session_id: Unique session identifier for the client session.

    Returns:
    - Confirmation status and OTP expiry details.
    """
    return await auth_manager.send_otp(session_id=session_id, mobile_number=mobile_number)


async def verify_otp_tool(mobile_number: str, code: str, session_id: str = "default_session") -> Dict[str, Any]:
    """
    Verify the OTP code sent to the user's mobile number to authenticate and log in.

    Parameters:
    - mobile_number: User's registered mobile number (string).
    - code: The OTP code received on SMS (string).
    - session_id: Unique session identifier for the client session.

    Returns:
    - Authentication status and user account summary.
    """
    return await auth_manager.verify_otp(session_id=session_id, mobile_number=mobile_number, code=code)


async def switch_project_tool(project_id: str, session_id: str = "default_session") -> Dict[str, Any]:
    """
    Switch active project context for the authenticated user and acquire project access permissions.

    Parameters:
    - project_id: ID of the project to switch context to (string).
    - session_id: Unique session identifier for the client session.

    Returns:
    - Confirmation of project context switch.
    """
    return await auth_manager.switch_project(session_id=session_id, project_id=str(project_id))
