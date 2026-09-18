# Build a Remote MCP Server for Our Existing Application

I need to build a **Python-based remote MCP server** that sits between our existing application backend and MCP-compatible AI clients such as ChatGPT, Claude, Gemini, etc.

The MCP server should use **Streamable HTTP** and eventually be deployed on **MCP Cloud** for PoC/testing.

The existing application has:

* Mobile + Web frontend
* Node.js + TypeScript backend
* PostgreSQL
* JWT authentication
* ~500 APIs
* Structured application data exposed through APIs
* PDFs/images stored in AWS S3

For the PoC, we only need to expose **2 selected API sets** from the Postman collection.

The MCP server must be **provider-independent** and must not replace or modify the existing backend.

---

# Phase 1 — Understand Existing Backend & Authentication

Before writing the MCP implementation, inspect the provided **Postman collection**.

Determine:

* Authentication/login flow
* How JWT Token 1 is obtained
* How JWT Token 2 is obtained
* Which APIs require Token 1
* Which APIs require Token 2
* The two API sets required for the PoC
* Request parameters and headers
* API response structures
* Which APIs are read-only
* Which APIs modify data

The application identifies users through **phone-number-based accounts**, not Google accounts.

The backend already performs user-level authorization.

Document the authentication flow and API → JWT mapping before implementing the MCP server.

### Deliverable

Create a short document such as:

```text
docs/api-analysis.md
```

containing:

* Authentication flow
* JWT flow
* API → JWT mapping
* PoC API list
* Important request/response details
* Any assumptions or blockers

Do not proceed with implementation based on guesses.

---

# Phase 2 — Build MCP Server & Backend Integration

Create the MCP server using:

* Python
* MCP SDK
* Streamable HTTP
* Async HTTP client such as `httpx`
* Environment-based configuration

The architecture should be:

```text
ChatGPT / Claude / Gemini
          │
          │ MCP / Streamable HTTP
          ▼
     Python MCP Server
          │
          │ HTTPS REST
          ▼
 Existing Node.js Backend
          │
      ┌───┴────┐
      ▼        ▼
 PostgreSQL   AWS S3
```

The MCP server must **not connect directly to PostgreSQL**.

Create a reusable backend API client responsible for:

* HTTP requests
* Headers
* Authentication
* Timeouts
* Error handling
* JSON responses

Create centralized authentication/token-management logic rather than duplicating JWT handling inside every tool.

Use environment variables for backend URLs and secrets.

### Deliverable

A locally runnable Python MCP server using Streamable HTTP with the basic backend client and project structure in place.

---

# Phase 3 — Authentication & MCP Tools

Implement the authentication flow discovered in Phase 1.

The MCP server must support **per-user authentication**.

Do not use one shared application account for all AI users.

The architecture should establish:

```text
AI/MCP User
     ↓
MCP Authentication
     ↓
Application User
     ↓
Application Login
     ↓
JWT 1
     ↓
JWT 2
     ↓
Backend APIs
```

Use the actual authentication mechanism supported by the target MCP client and the application's APIs.

Never expose JWTs to the LLM or log them.

## MCP Tools

For the PoC, use **one MCP tool per relevant backend API**.

Example:

```text
get_customers()
get_customer_by_id()
get_orders()
get_order_by_id()
get_documents()
```

The actual tools must come from the selected APIs in the Postman collection.

Only expose **read operations** for business/application data.

Do not expose:

* Create
* Update
* Delete
* Arbitrary SQL execution

Authentication POST requests are allowed where required by the login flow.

Each tool should:

1. Validate input.
2. Identify the authenticated user.
3. Select the correct JWT.
4. Call the backend API.
5. Return structured data.
6. Handle errors safely.

Tool descriptions should be clear enough for an LLM to select the correct tool.

The MCP server should allow the LLM to call multiple tools when a question requires multiple backend APIs.

### Deliverable

A working MCP server exposing the two PoC API sets as MCP tools with the correct per-user authentication and JWT selection.

---

# Phase 4 — Testing, Security & Analytics

Test the complete flow:

```text
User question
     ↓
LLM
     ↓
MCP tool
     ↓
MCP Server
     ↓
Backend API
     ↓
JSON response
     ↓
LLM analysis
     ↓
Answer
```

The LLM should be able to analyze JSON returned by the APIs.

Examples:

```text
"Show me my recent records."

"What is the total amount?"

"Compare this month with last month."

"Which entities have the highest value?"

"Find the top 5 and show their associated details."
```

The LLM should perform calculations/analysis on the returned data.

**Do not give the LLM direct PostgreSQL access.**

For large responses, use pagination/filtering/limits where supported by the backend rather than blindly returning huge payloads.

## Security

Verify:

* JWTs are never returned to the LLM.
* JWTs are never logged.
* Users cannot access another user's data.
* Backend authorization remains authoritative.
* Business-data mutation APIs are not exposed.
* Secrets are not hard-coded.
* Internal stack traces are not exposed.
* HTTP requests have appropriate timeouts.

## Testing

Create tests for:

* Authentication
* JWT selection
* Backend API calls
* MCP tools
* Invalid inputs
* 401/403/404/500 responses
* User isolation
* Security-sensitive behavior

### Deliverable

A tested PoC with documented security assumptions and known limitations.

---

# Phase 5 — Docker, MCP Cloud & Client Integration

Containerize the MCP server.

Create:

```text
Dockerfile
.env.example
README.md
```

The server must be deployable remotely using **MCP Cloud** for the PoC.

Provide deployment instructions covering:

1. Configure environment variables/secrets.
2. Build/deploy the MCP server.
3. Obtain the remote MCP endpoint.
4. Verify Streamable HTTP connectivity.
5. Configure the endpoint in a supported MCP client.
6. Authenticate a user.
7. Test the MCP tools.
8. Test multi-tool queries.

The implementation should remain portable so it can later be deployed to AWS, Azure, GCP, Kubernetes, etc.

---

# Final PoC Goal

The completed system should support:

```text
                    ┌───────────────────────┐
                    │ ChatGPT / Claude /    │
                    │ Gemini / MCP Client   │
                    └───────────┬───────────┘
                                │
                         Streamable HTTP
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Python MCP Server   │
                    │                       │
                    │ Authentication        │
                    │ JWT management        │
                    │ MCP Tools             │
                    │ API orchestration     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Existing Backend      │
                    │ Node.js + TypeScript  │
                    └───────────┬───────────┘
                                │
                         ┌──────┴──────┐
                         ▼             ▼
                    PostgreSQL       AWS S3
```

The user should be able to ask natural-language questions through an MCP-compatible AI client, have the LLM select the appropriate MCP tools, retrieve authorized data from the existing backend, call multiple tools when necessary, and analyze the returned JSON to produce the final answer.

The PoC should be designed so that the remaining APIs can be added later without redesigning the MCP server.
