# Stallion MCP Server — Complete Integration & Client Guide

This guide covers how to test, connect, and use the deployed **Stallion Remote MCP Server** across different clients (**MCP Inspector**, **Claude Desktop**, **Antigravity / Gemini**, and **ChatGPT**).

---

## 1. Server Details & Prerequisites

* **Remote MCP Server URL**: `https://stallion-mcp-server-test.onrender.com/sse`
* **Transport**: SSE (Server-Sent Events)
* **Authentication**: Single JWT Token (passed via `Authorization: Bearer <token>` header, `STALLION_JWT_TOKEN` environment variable, or `jwt_token` tool argument)
* **Software Required on the Client PC**:
  1. **Node.js** (includes `npx`): [Download Node.js](https://nodejs.org/)
  2. **Claude Desktop App** (optional for Claude chat): [Download Claude Desktop](https://claude.ai/download)

---

## 2. Quick Test with MCP Inspector (Verify Server First)

Before connecting to Claude or other AI clients, it's recommended to test your remote server directly using the official MCP Inspector.

### Step 1: Launch MCP Inspector
Open your terminal (PowerShell / Command Prompt / Terminal) and run:

```bash
npx @modelcontextprotocol/inspector
```

### Step 2: Connect to Your Render Server
1. The terminal will output a local URL (typically `http://localhost:5173` or `http://localhost:6274`). Open it in your web browser.
2. In the connection configuration pane on the left:
   - **Transport Type**: Select **`SSE`** (or Server-Sent Events)
   - **URL**: Enter your full Render SSE URL:
     ```text
     https://stallion-mcp-server-test.onrender.com/sse
     ```
3. Click **Connect**.

> [!NOTE]
> If your Render server is on the free tier and was idle, it may take 30–60 seconds on the first connection while the container spins up.

### Step 3: Test Tools in the Inspector UI
Once connected, all 8 registered tools will appear in the **Tools** tab:

1. `get_user_profile`
2. `get_project_details`
3. `get_project_towers`
4. `get_assigned_modules`
5. `get_developer_users`
6. `get_project_users`
7. `get_project_permissions`
8. `view_permission_document`

Provide `jwt_token` in tool calls or set `STALLION_JWT_TOKEN` on the server host.

---

## 3. Setting Up Claude Desktop (Windows & Mac)

### Step 1: Open the Configuration File

#### On Windows:
1. Press <kbd>Win</kbd> + <kbd>R</kbd>
2. Paste the following path and press <kbd>Enter</kbd>:
   ```text
   %APPDATA%\Claude\claude_desktop_config.json
   ```
   *(If the file or `Claude` folder does not exist, create it in `C:\Users\<username>\AppData\Roaming\Claude\`)*

#### On macOS:
Open `~/Library/Application Support/Claude/claude_desktop_config.json` in any text editor.

---

### Step 2: Add the MCP Server Configuration

Add or merge the `"mcpServers"` block at the top level of your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "stallion-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://stallion-mcp-server-test.onrender.com/sse"
      ]
    }
  }
}
```

---

### Step 3: Restart Claude Desktop

1. Completely close Claude Desktop (check system tray / taskbar to ensure it is fully closed).
2. Re-open **Claude Desktop**.
3. Click the **Hammer / Tools icon (🔨)** to verify all 8 Stallion tools are loaded:
   - `get_user_profile`, `get_project_details`, `get_project_towers`, `get_assigned_modules`
   - `get_developer_users`, `get_project_users`, `get_project_permissions`, `view_permission_document`

