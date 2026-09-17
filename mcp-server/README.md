# Stallion Remote MCP Server

A remote, provider-independent **Model Context Protocol (MCP) Server** built in Python using **Streamable HTTP**. It acts as an AI integration and orchestration layer between MCP-compatible clients (ChatGPT, Claude, Gemini) and the existing Stallion Node.js REST API backend.

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────┐
│                 MCP Host / Client                       │
│       (ChatGPT / Claude / Gemini / MCP Client)           │
└────────────────────────────┬────────────────────────────┘
                             │
                     Streamable HTTP
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                 Python MCP Server                       │
│                                                         │
│  - SessionStore (Abstract BaseSessionStore / InMemory)  │
│  - AuthManager (Two-Token Flow: Token 1 & Token 2)      │
│  - BackendClient (Async httpx, error normalization)     │
│  - MCP Tools (Read-only GET enforcement)                │
└────────────────────────────┬────────────────────────────┘
                             │
                        HTTPS REST API
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                 Existing Backend                        │
│               Node.js + TypeScript                      │
└────────────────────────────┬────────────────────────────┘
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
       ┌───────────────┐           ┌───────────────┐
       │  PostgreSQL   │           │    AWS S3     │
       │ (Data Store)  │           │ (Files/PDFs)  │
       └───────────────┘           └───────────────┘
```

---

## Authentication & Token Architecture

The Stallion application uses phone-number user accounts with a two-tier JWT token system:

1. **Token 1 (`authToken` / User Auth Token)**:
   - Acquired via `verify_otp(mobile_number, code)`.
   - Scope: User global profile (`/auth/me`), user project list (`/projects/mobile`), notifications (`/notifications`).

2. **Token 2 (`projectToken` / Project Token)**:
   - Acquired via `switch_project(project_id)` using Token 1.
   - Scope: Project details (`/projects/:id`), project towers (`/towers`), assignable modules (`/modules/assignable`), developer users (`/developers/:id/users`), project users (`/users/project/:id`), project permissions (`/permissions/projects/:id`), and document viewing.

### Session Storage & In-Memory Privacy

- **Per-User Session Isolation**: Sessions are tracked via a unique `session_id`.
- **Zero Disk/DB Persistence**: JWTs are kept in-memory only and are never written to disk or database.
- **Pluggable Abstraction**: Implemented via `BaseSessionStore` & `InMemorySessionStore`. In multi-instance production environments, this can be swapped for an encrypted Redis-backed store without breaking tool logic.

---

## MCP Tools Reference Table

| Tool Name | Backend Endpoint | Method | Required JWT | Read/Write | Description |
|---|---|---|---|---|---|
| `send_otp` | `/auth/send-otp` | POST | None | Auth | Request login OTP SMS. |
| `verify_otp` | `/auth/verify-otp` | POST | None | Auth | Verify OTP code & obtain Token 1. |
| `switch_project` | `/auth/mobile/switch-by-project` | POST | Token 1 | Auth | Switch active project & obtain Token 2. |
| `get_user_profile` | `/auth/me` | GET | Token 1 | Read | Retrieve user profile & metrics. |
| `get_user_projects` | `/projects/mobile` | GET | Token 1 | Read | List all projects accessible to user. |
| `get_project_details` | `/projects/:projectId` | GET | Token 2 | Read | Retrieve detailed project specifications. |
| `get_project_towers` | `/towers?project_id=:id` | GET | Token 2 | Read | Retrieve list of towers for a project. |
| `get_notifications` | `/notifications` | GET | Token 1 | Read | Retrieve paginated notifications. |
| `get_assigned_modules` | `/modules/assignable` | GET | Token 2 | Read | Retrieve assigned developer modules. |
| `get_developer_users` | `/developers/:id/users` | GET | Token 2 | Read | Retrieve employee list for developer. |
| `get_project_users` | `/users/project/:id` | GET | Token 2 | Read | Retrieve user list for a project. |
| `get_project_permissions` | `/permissions/projects/:id` | GET | Token 2 | Read | Retrieve permissions & LOD documents. |
| `view_permission_document` | `/permissions/.../view` | GET | Token 2 | Read | Retrieve document metadata & view URL. |

> **Note**: Business-data mutating endpoints (`PUT /permissions/...`, `POST /permissions/.../upload`) are explicitly **excluded** for safety.

---

## Local Development Setup

### Prerequisites

- Python 3.10+
- `pip` or `uv`

### Installation

1. Clone repository and navigate to `mcp-server`:
   ```bash
   cd mcp-server
   ```

2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies in editable mode:
   ```bash
   pip install -e ".[dev]"
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

---

## Environment Configuration

Environment variables configured in `.env`:

| Variable | Default Value | Description |
|---|---|---|
| `BACKEND_BASE_URL` | `https://api.dev.batman.co.in` | Stallion Node.js REST API base URL. |
| `HOST` | `0.0.0.0` | Host interface for Streamable HTTP server. |
| `PORT` | `8000` | Port for Streamable HTTP server. |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `HTTP_TIMEOUT` | `30.0` | HTTP request timeout in seconds. |

---

## Running the Server Locally

Start the MCP Server using Python:
```bash
python -m app.main
```

Or run via `uvicorn`:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Running Automated Tests

Run the complete test suite:
```bash
pytest -v tests/
```

Run test suite with coverage report:
```bash
pytest --cov=app tests/
```

---

## MCP Cloud Deployment Guide

1. **Prepare Project**: Ensure `Dockerfile`, `pyproject.toml`, and `app/` directory are committed.
2. **Deploy Container**: Push repository to GitHub or upload container build to MCP Cloud.
3. **Configure Environment Variables**:
   - Set `BACKEND_BASE_URL` (e.g. `https://api.dev.batman.co.in` or production URL).
   - Set `PORT` to `8000`.
4. **Deploy Endpoint**: Start container service. MCP Cloud will issue an HTTPS URL (e.g. `https://stallion-mcp.mcp.cloud`).
5. **Verify Endpoint**: Send test request to verify Streamable HTTP server connectivity.

---

## Client Integration Guide

To connect MCP clients (ChatGPT, Claude, Gemini):

### Streamable HTTP Endpoint Configuration

```json
{
  "mcpServers": {
    "stallion-backend": {
      "url": "https://stallion-mcp.mcp.cloud/sse",
      "transport": "http"
    }
  }
}
```

---

## How to Expose a New Backend API as an MCP Tool

To add a new API from the backend:

1. Identify endpoint method, path, required token (`authToken` or `projectToken`), and query/body parameters in Postman collection.
2. Add a new tool function in `app/tools/<domain>_tools.py`:
   ```python
   async def get_example_tool(example_id: str, session_id: str = "default_session") -> Dict[str, Any]:
       """Clear semantic description explaining what the tool retrieves and its return structure."""
       token = await auth_manager.get_token_for_api(session_id, token_type="projectToken")
       return await backend_client.request(method="GET", path=f"/example/{example_id}", token=token)
   ```
3. Register the tool in `app/main.py`:
   ```python
   mcp.tool(name="get_example", description="...")(get_example_tool)
   ```
4. Add corresponding test in `tests/test_tools.py`.
