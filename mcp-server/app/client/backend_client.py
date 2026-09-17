import httpx
from typing import Any, Dict, Optional
from app.config.settings import settings
from app.utils.errors import BackendAPIError, MutatingOperationForbiddenError
from app.utils.logging import get_logger

logger = get_logger("client.backend")


class BackendClient:
    """
    Reusable Async HTTP Client for interacting with the Stallion Node.js Backend REST APIs.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.backend_base_url).rstrip("/")
        self.timeout = timeout or settings.http_timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )

    async def close(self):
        await self.client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        is_auth_endpoint: bool = False
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request to the Stallion backend.
        Enforces read-only policy for non-auth endpoints.
        """
        method_upper = method.upper()

        # Enforce read-only policy for business data
        if not is_auth_endpoint and method_upper not in ["GET"]:
            raise MutatingOperationForbiddenError(
                f"Method {method_upper} is forbidden for business data tools. Only read-only (GET) operations are permitted."
            )

        req_headers = headers.copy() if headers else {}
        if token:
            req_headers["Authorization"] = f"Bearer {token}"

        clean_path = path if path.startswith("/") else f"/{path}"
        logger.info(f"Executing {method_upper} {clean_path}")

        try:
            response = await self.client.request(
                method=method_upper,
                url=clean_path,
                params=params,
                json=json_data,
                headers=req_headers
            )
        except httpx.TimeoutException as exc:
            logger.error(f"Timeout request to {clean_path}: {exc}")
            raise BackendAPIError(status_code=504, message="Backend request timed out", details=str(exc))
        except httpx.RequestError as exc:
            logger.error(f"HTTP request error to {clean_path}: {exc}")
            raise BackendAPIError(status_code=502, message="Backend service communication error", details=str(exc))

        if response.status_code >= 400:
            logger.warning(f"Backend returned HTTP {response.status_code} for {clean_path}")
            error_message = "Backend error"
            error_details = None
            try:
                res_json = response.json()
                error_message = res_json.get("message", res_json.get("error", "Backend request failed"))
                error_details = res_json.get("data")
            except Exception:
                error_message = response.text or "Backend request failed"

            raise BackendAPIError(
                status_code=response.status_code,
                message=error_message,
                details=str(error_details) if error_details else None
            )

        try:
            return response.json()
        except Exception as exc:
            logger.error(f"Failed to parse JSON response from {clean_path}: {exc}")
            raise BackendAPIError(status_code=500, message="Invalid JSON response from backend API")
