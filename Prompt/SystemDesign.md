# Task: Build a Remote, Provider-Independent MCP Server for an Existing Application

## 1. Objective

I have an existing production application consisting of:

* Mobile frontend
* Web frontend
* Node.js + TypeScript backend
* PostgreSQL database
* JWT-based authentication
* Structured data stored in PostgreSQL and exposed through backend REST APIs
* Unstructured files such as PDFs and images stored in AWS S3

The application currently has approximately **500 backend APIs**.

For this proof of concept, we only need to expose **2 selected API sets** through an MCP server.

The goal is to introduce an **MCP layer between an MCP-compatible AI host/client and the existing backend**.

The final architecture should allow users to interact with the application through an AI interface instead of directly using the application's mobile/web UI.

The AI host may be:

* ChatGPT
* Claude
* Gemini
* Or any other application supporting remote MCP servers using Streamable HTTP

The MCP server must therefore be **LLM-provider/host independent**.

---

# 2. Target Architecture

Implement the following architecture:

```
                ┌─────────────────────────────┐
                │       MCP Host / Client     │
                │                             │
                │ ChatGPT / Claude / Gemini   │
                │ / Other MCP-compatible app  │
                └──────────────┬──────────────┘
                               │
                       MCP / Streamable HTTP
                               │
                               ▼
                ┌─────────────────────────────┐
                │          MCP Server         │
                │                             │
                │ Python                      │
                │                             │
                │ Authentication              │
                │ User/session handling       │
                │ MCP tool definitions        │
                │ Backend API orchestration   │
                │ Response normalization      │
                │ Error handling              │
                └──────────────┬──────────────┘
                               │
                          HTTPS REST API
                               │
                               ▼
                ┌─────────────────────────────┐
                │      Existing Backend       │
                │                             │
                │ Node.js + TypeScript        │
                │ Existing REST APIs          │
                │ Existing authorization      │
                └──────────────┬──────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
         ┌──────────────┐              ┌──────────────┐
         │  PostgreSQL  │              │    AWS S3    │
         │ Structured   │              │ PDFs/Images  │
         │ application  │              │              │
         │ data         │              │              │
         └──────────────┘              └──────────────┘
```

The MCP server must **not replace or modify the existing backend**.

It should act as an AI-facing integration/orchestration layer over the existing APIs.

---

# 3. Technology Requirements

Build the MCP server using:

* Python
* An appropriate production-ready Python MCP SDK
* Streamable HTTP transport
* Async I/O where appropriate
* HTTP client such as httpx or an equivalent production-quality library
* Environment-variable based configuration
* Docker support
* Structured logging
* Health/readiness endpoint if appropriate
* Proper error handling
* Type hints
* Clear project structure
* Automated tests

Do not rewrite the existing Node.js/TypeScript backend.

The existing backend belongs to another team and must be treated as an external service.

---

# 4. MCP Transport

Use:

**Streamable HTTP**

The MCP server must be remotely accessible.

Do not design this as a local stdio-only MCP server.

The final server should expose a production/deployment-ready HTTP endpoint that an MCP-compatible client can connect to.

The implementation should be suitable for deployment on **MCP Cloud for the PoC/testing phase**.

Provide clear deployment instructions for MCP Cloud, including:

* Required configuration
* Environment variables/secrets
* Build/start commands
* MCP endpoint configuration
* Authentication configuration if required
* How to test the deployed endpoint
* How to connect the deployed server to an MCP client

Do not assume that the MCP server will permanently run on MCP Cloud. The implementation should remain portable to other cloud/container environments.

---

# 5. Existing Backend APIs

I have a **Postman collection** containing the existing backend APIs.

The Postman collection includes:

* Authentication endpoints
* APIs from the two API sets required for the PoC
* Request parameters
* Headers
* Request bodies
* Response formats
* Information indicating which JWT token must be used for each API

Treat the Postman collection as the source of truth for the PoC API integration.

Before implementing the tools:

1. Inspect the Postman collection.
2. Identify the authentication flow.
3. Identify all APIs belonging to the two selected API sets.
4. Identify the required JWT token for each API.
5. Identify request parameters and required headers.
6. Identify response schemas.
7. Identify relationships between APIs.
8. Identify which APIs are read-only and which are mutating.
9. Document the mapping between MCP tools and backend APIs.

Do not blindly expose unrelated APIs from the Postman collection.

---

# 6. Authentication Requirements

The existing application uses JWT authentication.

The authentication flow currently works approximately as follows:

1. User logs into the application.
2. The application calls the login/authentication API.
3. The backend returns **JWT Token 1**.
4. Another API is called using Token 1.
5. That process obtains **JWT Token 2**.
6. Different backend APIs require different JWT tokens.

The Postman collection explicitly identifies which token is required by each API.

The MCP implementation must reproduce the required authentication flow correctly.

## Critical requirement

The MCP server must support **per-user authentication**.

Do NOT use a single shared application account for all ChatGPT/Claude users.

The application identifies users using their **phone-number-based application accounts**, not Google accounts.

Therefore, design the authentication flow so that an individual AI-host user can authenticate as their corresponding application user.

The MCP server must preserve the user's identity when making requests to the backend.

The backend already enforces user-level authorization, so the MCP server must pass the correct user credentials/tokens to the backend rather than attempting to bypass backend authorization.

---

# 7. Authentication Design Must Be Explicit

Because MCP hosts such as ChatGPT/Claude may have their own identity systems while the application uses phone-number accounts, carefully design the identity/authentication boundary.

Do not assume:

"ChatGPT user = application user"

without an explicit authentication mechanism.

Investigate the appropriate MCP authentication mechanism for a remote Streamable HTTP MCP server.

The implementation/design should clearly explain:

```text
MCP Host User
      ↓
MCP Authentication
      ↓
Application User Identity
      ↓
Application Login
      ↓
JWT Token 1
      ↓
JWT Token 2
      ↓
Backend API
```

The user should authenticate/authorize access to their application account rather than receiving access to another user's data.

If the selected MCP host has limitations around the required authentication flow, document those limitations and provide the appropriate PoC-compatible approach rather than silently introducing shared credentials.

---

# 8. JWT Token Management

There are two JWT tokens.

Token usage is API-specific.

For example:

```text
API A → JWT 1
API B → JWT 1
API C → JWT 2
API D → JWT 2
```

The actual mapping must be obtained from the Postman collection.

Create a centralized authentication/token-management component.

Do NOT duplicate token-handling logic inside every MCP tool.

For example:

```text
AuthenticationManager
│
├── authenticate_user()
├── obtain_token_1()
├── obtain_token_2()
├── get_token_for_api()
├── refresh_token_if_required()
└── invalidate_session()
```

The exact implementation should follow the actual authentication APIs and token semantics discovered in the Postman collection.

Never log JWT values.

Never expose JWT values to the LLM.

Never return JWT values through MCP tool responses.

---

# 9. Read-Only Requirement

For the PoC, the LLM must be able to **read and analyze application data**.

The LLM must NOT be allowed to create, update, or delete application data.

Therefore:

### Allowed

* Authentication/login
* Required authentication/session operations
* GET/read APIs
* Fetching records
* Searching/filtering
* Retrieving metadata
* Retrieving PDF/image references
* Analytics based on returned data

### Not allowed

* POST operations that create business data
* PUT operations
* PATCH operations
* DELETE operations
* Any operation that mutates business/application data

Authentication endpoints may use POST where required.

Clearly separate authentication operations from business-data mutation operations.

Implement safeguards so that accidentally exposing a mutating API as an MCP tool is difficult.

---

# 10. MCP Tool Design

For the PoC, use **Approach 1: one MCP tool per relevant backend API**.

For example:

```text
get_customers()
get_customer_by_id()
get_customer_orders()
get_order_by_id()
get_products()
search_products()
get_invoice()
get_customer_documents()
```

The exact tools must be generated from the selected APIs in the Postman collection.

Do not create tools for all ~500 APIs.

Only implement the two API sets required for the PoC.

Each tool should:

1. Validate its input.
2. Authenticate the user/session.
3. Determine which JWT token is required.
4. Call the corresponding backend API.
5. Handle HTTP errors.
6. Normalize the response where necessary.
7. Return useful structured data to the MCP host/LLM.
8. Never expose credentials/secrets.
9. Never bypass backend authorization.

---

# 11. Tool Naming and Descriptions

MCP tool names and descriptions are extremely important because the LLM uses them to decide which tool to call.

Create clear, semantic descriptions.

Bad:

```text
api_17()
```

Good:

```text
get_customer_orders()
```

The tool description should explain:

* What information the tool retrieves
* Required parameters
* Optional parameters
* Important filtering behavior
* Expected result
* Relevant restrictions

Example:

```text
get_customer_orders

Retrieve orders belonging to the authenticated user/customer.

Parameters:
- customer_id
- start_date
- end_date
- status

Returns:
A structured list of orders including order ID, date,
status, amount and associated metadata.

This tool is read-only.
```

Do not make tool descriptions excessively verbose, but provide enough semantic information for reliable tool selection.

---

# 12. Multi-Tool / Multi-Step Queries

The MCP server must support workflows where the LLM needs to call multiple tools.

For example:

User:

> "Find my top 5 customers by revenue and show me their latest invoices."

The expected conceptual flow may be:

```text
LLM
 │
 ├── get_customers()
 │
 ├── analyze returned customer/revenue data
 │
 ├── get_customer_invoices(customer_1)
 │
 ├── get_customer_invoices(customer_2)
 │
 ├── ...
 │
 └── Generate final answer
```

The MCP server should expose the tools independently and allow the MCP host/LLM to orchestrate multiple calls.

Do not build unnecessary hard-coded workflows for every possible question.

---

# 13. Analytics

A key requirement is that the LLM should not only retrieve data but also **analyze the API responses**.

The backend API responses are primarily structured JSON.

The desired flow is:

```text
User Question
      ↓
LLM
      ↓
MCP Tool
      ↓
Existing Backend API
      ↓
JSON Response
      ↓
LLM
      ↓
Analysis
      ↓
Natural-language answer
```

Examples of expected queries:

```text
"How many orders did I place this month?"

"What was the total revenue?"

"Compare this month with last month."

"Which customers generated the most revenue?"

"What percentage of orders are currently pending?"

"Identify the largest transactions."

"Summarize the trends in the returned data."
```

The LLM should be able to perform calculations and analysis over the returned JSON data.

Do **not** give the LLM direct access to PostgreSQL for this PoC.

Do **not** implement arbitrary SQL execution.

The existing APIs remain the controlled data-access layer.

If a query cannot be answered from the available API responses, the system should clearly communicate that the available data/tools are insufficient rather than inventing data.

---

# 14. Large API Responses

Consider the possibility that an API returns a large JSON response.

The MCP server should avoid blindly returning unnecessarily large payloads to the LLM.

Investigate and implement appropriate mechanisms where useful, such as:

* Pagination
* Filtering
* Field selection
* Limits
* Sorting
* Aggregation through existing APIs if available
* Response normalization

Do not truncate data in a way that causes the LLM to unknowingly produce incorrect analytics.

If a response is too large for reliable analysis, the tool should expose pagination/filtering or clearly communicate the limitation.

---

# 15. Structured Data

The structured data resides in PostgreSQL but should be accessed through the existing backend APIs.

Architecture:

```text
MCP Server
    ↓
Backend REST API
    ↓
PostgreSQL
```

The MCP server must not connect directly to PostgreSQL for the PoC.

This preserves the existing:

* Business logic
* Authentication
* Authorization
* Validation
* Data-access rules

---

# 16. Unstructured Data

Some application data is stored as:

* PDF files
* Images

These files are stored in **AWS S3**.

For the PoC, use **Option A**:

The MCP server should be able to retrieve/access the relevant document/image information through the existing application APIs.

Do NOT implement document/image AI analysis in the PoC.

Do not introduce OCR, computer vision, embeddings, RAG, or multimodal analysis yet.

The architecture should, however, make it possible to add this functionality later.

Potential future architecture:

```text
MCP Server
     ↓
Backend API
     ↓
S3
     ↓
PDF/Image
     ↓
Document/Image Processing
     ↓
AI Model
     ↓
Analysis
```

For the current PoC, stop before the AI-processing stage.

---

# 17. Security Requirements

Treat this as an externally accessible server.

Implement appropriate security controls.

At minimum:

* Never hard-code secrets.
* Never hard-code JWTs.
* Never log JWTs.
* Never return JWTs to the LLM.
* Never expose database credentials.
* Never expose AWS credentials to the MCP client.
* Use environment variables/secrets.
* Validate tool inputs.
* Preserve backend authorization.
* Prevent cross-user data access.
* Use HTTPS in deployment.
* Implement reasonable request timeouts.
* Handle backend errors safely.
* Do not expose internal stack traces to clients.
* Avoid logging sensitive user/application data unnecessarily.
* Implement rate limiting where appropriate for the deployment environment.

Clearly identify which security mechanisms are provided by:

1. MCP host
2. MCP server
3. Existing backend

Do not assume that authentication at one layer automatically provides authorization at another.

---

# 18. Error Handling

The MCP server must provide useful errors to the LLM without leaking internal implementation details.

Examples:

Backend returns:

```text
401 Unauthorized
```

The MCP layer should return a meaningful authentication/session error.

Backend returns:

```text
403 Forbidden
```

Return an authorization error indicating that the authenticated user does not have permission to access the requested resource.

Backend returns:

```text
404 Not Found
```

Return a meaningful not-found response.

Backend returns:

```text
500
```

Return a safe backend-service error.

Do not expose:

* JWTs
* API keys
* Internal stack traces
* Database credentials
* AWS credentials
* Internal infrastructure information

---

# 19. Configuration

Create a clean configuration system using environment variables.

At minimum, consider:

```text
BACKEND_BASE_URL=
AUTH_ENDPOINT=
...
```

The exact variables must be determined after inspecting the Postman collection.

Do not commit `.env` files containing real credentials.

Provide:

```text
.env.example
```

with placeholders.

---

# 20. Project Structure

Use a maintainable structure similar to:

```text
mcp-server/
│
├── app/
│   ├── main.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── auth/
│   │   ├── manager.py
│   │   ├── token_manager.py
│   │   └── session.py
│   │
│   ├── client/
│   │   └── backend_client.py
│   │
│   ├── tools/
│   │   ├── auth_tools.py
│   │   ├── api_set_1/
│   │   └── api_set_2/
│   │
│   ├── models/
│   │   └── ...
│   │
│   └── utils/
│       ├── errors.py
│       └── logging.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_backend_client.py
│   ├── test_tools.py
│   └── ...
│
├── Dockerfile
├── requirements.txt / pyproject.toml
├── .env.example
├── README.md
└── ...
```

You may modify this structure if a better architecture is appropriate.

Do not over-engineer the PoC.

---

# 21. API Client

Create a reusable backend API client.

For example:

```text
BackendClient
│
├── get()
├── post()
├── put()
├── patch()
└── delete()
```

However, for business-data MCP tools in this PoC, only expose read operations.

The client should centrally handle:

* Base URL
* Authentication headers
* JWT selection
* Timeouts
* Retry behavior where appropriate
* HTTP errors
* JSON parsing
* Logging

Do not duplicate HTTP request code across every MCP tool.

---

# 22. JWT Selection

Because different APIs require different JWTs, implement centralized token selection.

Conceptually:

```text
API Tool
   ↓
Token Requirement
   ↓
Authentication Manager
   ↓
JWT 1 or JWT 2
   ↓
Backend Request
```

The mapping must be derived from the Postman collection rather than guessed.

Prefer a declarative mapping if practical, for example:

```text
API_X → TOKEN_1
API_Y → TOKEN_2
```

This will make the eventual expansion from 2 API sets to approximately 500 APIs easier.

---

# 23. Extensibility

Although the PoC only requires two API sets, design the code so additional APIs can be added without redesigning the MCP server.

The eventual goal is approximately:

```text
500 Backend APIs
        ↓
Selected/curated MCP tools
        ↓
MCP Server
        ↓
ChatGPT / Claude / Gemini / Other MCP clients
```

Do NOT automatically assume that all 500 backend APIs should become MCP tools.

For this PoC, implement one MCP tool per selected read-only backend API.

Later we may introduce higher-level domain tools or aggregation tools to reduce tool count and improve LLM tool selection.

---

# 24. MCP Resources and Prompts

Evaluate whether MCP Resources or MCP Prompts are useful for this architecture.

Do not add them simply for the sake of using every MCP feature.

The primary PoC requirement is **MCP Tools**.

If Resources or Prompts provide a concrete architectural advantage, document it separately.

---

# 25. Observability

Implement basic observability suitable for a PoC:

* Structured logs
* Request/tool name logging
* Backend response status
* Request duration
* Error logging

Do not log:

* JWTs
* Passwords
* API secrets
* AWS credentials
* Sensitive user information unnecessarily

If practical, include a request/correlation ID so that:

```text
MCP request
    ↓
Tool call
    ↓
Backend API request
```

can be traced through logs.

---

# 26. Testing

Create tests for:

### Authentication

* Login flow
* Token 1 acquisition
* Token 2 acquisition
* Token expiration/refresh if applicable
* Invalid credentials
* Authentication failure

### API client

* Correct backend URL
* Correct headers
* Correct JWT selection
* Timeout handling
* HTTP errors
* Invalid JSON

### MCP tools

For every PoC tool:

* Valid parameters
* Invalid parameters
* Correct backend endpoint
* Correct HTTP method
* Correct JWT
* Successful response
* Unauthorized response
* Forbidden response
* Not-found response
* Backend failure

### Security

Verify that:

* JWTs never appear in tool responses.
* JWTs never appear in logs.
* Users cannot access another user's data.
* Mutating APIs cannot be invoked as business-data MCP tools.

Use mocks for backend APIs where appropriate.

Do not make automated tests dependent on production credentials.

---

# 27. Deployment

Provide complete deployment guidance for **MCP Cloud**.

The deployment documentation should cover:

1. Preparing the project.
2. Environment variables.
3. Secrets.
4. Building the application.
5. Starting the MCP server.
6. Exposing the Streamable HTTP endpoint.
7. Configuring the MCP endpoint.
8. Authentication configuration.
9. Testing connectivity.
10. Connecting it to a supported MCP client.
11. Troubleshooting common deployment problems.

The deployment should use HTTPS.

Also document how the same Dockerized application could later be deployed to:

* AWS
* Azure
* GCP
* Kubernetes
* Another container platform

Do not tightly couple the application to MCP Cloud.

---

# 28. README Requirements

Create a comprehensive README containing:

## Architecture

Explain the complete architecture.

## Local development

Show:

```text
git clone ...
python ...
pip install ...
...
```

or the appropriate `uv`/Poetry setup.

## Environment configuration

Explain every required environment variable.

## Running locally

Show how to start the MCP server.

## Testing

Explain how to run the tests.

## MCP inspection/testing

Explain how to verify that:

* The MCP server is reachable.
* Tools are correctly exposed.
* Authentication works.
* Tool calls reach the backend.

## MCP Cloud deployment

Provide step-by-step deployment instructions.

## Connecting to MCP clients

Explain the client configuration at a conceptual and practical level for supported clients.

## Security considerations

Document the security model.

## Adding a new API

Provide an example showing how a future backend API can be converted into an MCP tool.

---

# 29. Important Constraints

Do NOT:

* Rewrite the backend.
* Connect directly to PostgreSQL.
* Expose arbitrary SQL execution.
* Expose AWS credentials.
* Expose JWTs to the LLM.
* Use shared application credentials for all users.
* Expose business-data POST/PUT/PATCH/DELETE APIs in the PoC.
* Hard-code secrets.
* Implement OCR/vision/RAG for the PoC.
* Build a solution specific to only ChatGPT.
* Build a solution specific to only Claude.
* Assume MCP host identity automatically equals application identity.
* Automatically expose all 500 APIs.

---

# 30. Expected Deliverables

Produce the following:

### 1. Working Python MCP server

Using Streamable HTTP.

### 2. Authentication implementation

Supporting the actual two-token authentication flow discovered from the Postman collection.

### 3. Two API sets

Implement the selected read-only APIs as MCP tools.

### 4. Reusable backend API client

With centralized authentication/token handling.

### 5. Per-user authentication/session design

Clearly documenting how an MCP user is mapped to an application user.

### 6. Security controls

Including credential protection and user-level isolation.

### 7. Automated tests

Covering authentication, tools, API integration and security-sensitive behavior.

### 8. Docker configuration

For portable deployment.

### 9. Environment configuration

Including `.env.example`.

### 10. MCP Cloud deployment instructions

Complete enough for another developer to deploy the PoC.

### 11. README

Including architecture, setup, testing, deployment and extension instructions.

### 12. API-to-MCP mapping document

Create a concise mapping such as:

| Backend API    | HTTP Method | MCP Tool                | JWT   | Read/Write |
| -------------- | ----------- | ----------------------- | ----- | ---------- |
| `/example/...` | GET         | `get_example()`         | JWT 1 | Read       |
| `/example/...` | GET         | `get_example_details()` | JWT 2 | Read       |

Populate this from the actual Postman collection.

---

# 31. Definition of Done

The PoC is considered complete when the following workflow works:

```text
User
  │
  │ Natural language question
  ▼
ChatGPT / Claude / Gemini
  │
  │ MCP tool selection
  ▼
Remote MCP Server
  │
  │ Authenticate user
  │ Select correct JWT
  │ Call backend API
  ▼
Existing Node.js Backend
  │
  ▼
Application Data
  │
  └── PostgreSQL / S3 references
  │
  ▼
JSON Response
  │
  ▼
MCP Server
  │
  ▼
LLM
  │
  │ Analyze / calculate / summarize
  ▼
Natural-language answer
```

A successful demonstration should include at least:

### Example 1 — Simple retrieval

> "Show me my recent records."

### Example 2 — Filtering

> "Show me records from the last 30 days."

### Example 3 — Aggregation

> "What is the total amount across these records?"

### Example 4 — Analysis

> "Compare this month's data with last month's data."

### Example 5 — Multi-tool workflow

> "Find my top 5 entities and retrieve their associated details."

The LLM should be able to call multiple MCP tools when necessary and produce an answer based only on the data returned by the application's authorized APIs.

---

# 32. Development Approach

Before writing substantial code:

1. Inspect the Postman collection.
2. Understand the authentication flow completely.
3. Identify JWT 1 and JWT 2.
4. Identify how token 2 is obtained from token 1.
5. Identify the two API sets.
6. Identify all read-only APIs required for the PoC.
7. Identify API-to-JWT mappings.
8. Inspect representative JSON responses.
9. Design the MCP tool interface.
10. Design the per-user authentication flow.
11. Identify any MCP-host authentication limitations.
12. Then implement.

Do not make assumptions where the Postman collection or backend behavior provides the answer.

If something required for implementation cannot be determined from the available information, explicitly identify it as an assumption or blocker rather than silently inventing behavior.

At the end, provide:

* Architecture summary
* Files created
* Tools implemented
* Authentication flow
* API-to-tool mapping
* Security model
* Local setup
* Test results
* MCP Cloud deployment steps
* Known limitations
* Recommended next steps for expanding from the PoC to the full application
