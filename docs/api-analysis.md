# Stallion Backend API & Authentication Analysis

This document summarizes the authentication architecture, token lifecycle, and backend API mapping for the Stallion MCP Server proof-of-concept (PoC).

---

## 1. Authentication & Token Lifecycle

The existing backend uses a **two-tier JWT authentication system** mapped to phone-number user accounts.

```
+------------------+         +------------------+         +--------------------------+
|   MCP / AI Host  |         |   MCP Server     |         | Existing Node.js Backend |
+--------+---------+         +--------+---------+         +------------+-------------+
         |                            |                                |
         | 1. send_otp(mobile_number) | POST /auth/send-otp            |
         |--------------------------->|------------------------------->|
         |                            | <------------------------------|
         |                            |                                |
         | 2. verify_otp(mobile,code) | POST /auth/verify-otp          |
         |--------------------------->|------------------------------->|
         |                            | <--- Returns JWT Token 1 -----|
         |                            |      (User Auth Token)         |
         |                            |                                |
         | 3. get_user_projects()     | GET /projects/mobile           |
         |    (Uses Token 1)          | (Bearer Token 1)               |
         |--------------------------->|------------------------------->|
         |                            | <--- List of projects --------|
         |                            |                                |
         | 4. switch_project(proj_id) | POST /auth/mobile/switch-by-project?project_id=194
         |    (Uses Token 1)          | (Bearer Token 1)               |
         |--------------------------->|------------------------------->|
         |                            | <--- Returns JWT Token 2 -----|
         |                            |      (Project Token)           |
         |                            |                                |
         | 5. get_project_towers()    | GET /towers?project_id=194     |
         |    (Uses Token 2)          | (Bearer Token 2)               |
         |--------------------------->|------------------------------->|
```

### Token Definitions

| Token Name | Source Endpoint | Scope | Usage |
| :--- | :--- | :--- | :--- |
| **Token 1 (`authToken`)** | `POST /auth/verify-otp` | Global User Scope | User profile (`/auth/me`), accessible projects (`/projects/mobile`), notifications (`/notifications`), project switching. |
| **Token 2 (`projectToken`)** | `POST /auth/mobile/switch-by-project?project_id=:id` | Project-Specific Scope | Project details (`/projects/:id`), project towers (`/towers`), assignable modules (`/modules/assignable`), developer users (`/developers/:id/users`), project users (`/users/project/:id`), permissions (`/permissions/projects/:id`), and document viewing. |

---

## 2. Token Security & Session Boundaries

1. **Per-User Isolation**:
   - Each MCP client connection/session is bound to a unique `session_id`.
   - Token 1 (`authToken`) and Token 2 (`projectToken`) are maintained inside the isolated server session state (`SessionManager`).
   - Shared accounts across users are strictly prohibited.

2. **Credential Privacy**:
   - JWT tokens are stored securely in-memory in the session state.
   - Tokens are **never** logged in application logs.
   - Tokens are **never** exposed to the LLM or returned in MCP tool output.

3. **Backend Authorization Alignment**:
   - The MCP server passes the user's active tokens directly to the Node.js backend.
   - Authorization checking remains 100% authoritative at the existing backend layer.

---

## 3. API Set 1: User & Core Project APIs

| # | Endpoint | HTTP Method | Auth Token | Read / Mutating | MCP Tool Name | Description |
|---|---|---|---|---|---|---|
| 1 | `/auth/send-otp` | POST | None | Auth (Allowed) | `send_otp` | Requests OTP code to user's mobile number. |
| 2 | `/auth/verify-otp` | POST | None | Auth (Allowed) | `verify_otp` | Verifies OTP code and initializes session with Token 1 (`authToken`). |
| 3 | `/auth/mobile/switch-by-project` | POST | Token 1 | Auth (Allowed) | `switch_project` | Switches active project and obtains Token 2 (`projectToken`). |
| 4 | `/auth/me` | GET | Token 1 | Read-Only | `get_user_profile` | Retrieves profile details of authenticated user. |
| 5 | `/projects/mobile` | GET | Token 1 | Read-Only | `get_user_projects` | Retrieves all project details available to user. |
| 6 | `/projects/:projectId` | GET | Token 2 | Read-Only | `get_project_details` | Retrieves specific details of a project using `projectToken`. |
| 7 | `/towers?project_id=:id` | GET | **Token 2** | Read-Only | `get_project_towers` | Retrieves list of towers for a project using `projectToken`. |
| 8 | `/notifications?page=0&limit=15` | GET | Token 1 | Read-Only | `get_notifications` | Fetches paginated notifications. |
| 9 | `/modules/assignable` | GET | **Token 2** | Read-Only | `get_assigned_modules` | Retrieves list of assigned developer modules using `projectToken`. |
| 10| `/developers/:parentDeveloperId/users` | GET | **Token 2** | Read-Only | `get_developer_users` | Retrieves list of users/employees for developer using `projectToken`. |
| 11| `/users/project/:projectID` | GET | **Token 2** | Read-Only | `get_project_users` | Retrieves list of users assigned to a project using `projectToken`. |

---

## 4. API Set 2: Permission Module APIs

| # | Endpoint | HTTP Method | Auth Token | Read / Mutating | MCP Tool Name | Status |
|---|---|---|---|---|---|---|
| 12| `/permissions/projects/:projectId` | GET | Token 2 | Read-Only | `get_project_permissions` | Exposed as MCP Tool. Retrieves all permissions, categories, attachments, & LOD documents for project. |
| 13| `/permissions/projects/:projectId/:transProjectPerId/documents/:fileId/view` | GET | Token 2 | Read-Only | `view_permission_document` | Exposed as MCP Tool. Retrieves document metadata & view URL reference for sub-permission files. |
| 14| `/permissions/projects/:projectId/:transProjectPerId` | PUT | Token 2 | Mutating | - | **EXCLUDED** from MCP tools (Mutating API). |
| 15| `/permissions/projects/:projectId/:transProjectPerId/documents/upload` | POST | Token 2 | Mutating | - | **EXCLUDED** from MCP tools (Mutating API). |

---

## 5. Security & Read-Only Policy Rules

1. **Mutating APIs Exclusion**:
   - `PUT` endpoints (e.g., updating permission status/remarks) and business-data `POST` endpoints (e.g., file upload) are strictly forbidden from being exposed as tools.
   - Backend client rejects any non-GET request attempted by business tools.

2. **Direct DB / S3 Access Protection**:
   - Direct PostgreSQL connectivity is disabled.
   - S3 credentials are kept server-side; document view endpoints return authorized pre-signed/backend-proxied URLs without exposing raw AWS credentials.
