# Stallion MCP Server — Complete Integration & Client Guide

This guide covers how to test, connect, and use the deployed **Stallion Remote MCP Server** across different clients (**MCP Inspector**, **Claude Desktop**, **Antigravity / Gemini**, and **ChatGPT**).

---

## 1. Server Details & Prerequisites

* **Remote MCP Server URL**: `https://stallion-mcp-server-test.onrender.com/sse`
* **Transport**: SSE (Server-Sent Events)
* **Plan Required**: **Free Claude Account** (Claude Pro is **not** required).
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

### Step 3: Test Key Tools in the Inspector UI
Once connected, all 11 tools will appear in the **Tools** tab. You can test them in this sequence:

1. **Authentication (Token 1)**:
   - Select `send_otp` $\rightarrow$ Enter `mobile_number: "8291598930"` and `session_id: "test_session"` $\rightarrow$ Click **Run Tool**.
   - Select `verify_otp` $\rightarrow$ Enter `mobile_number: "8291598930"`, `code: "<received_otp>"`, and `session_id: "test_session"` $\rightarrow$ Click **Run Tool**.
2. **Project Selection (Token 2)**:
   - Select `get_user_projects` $\rightarrow$ Enter `session_id: "test_session"` $\rightarrow$ Run Tool to see available projects (e.g. `194`).
   - Select `switch_project` $\rightarrow$ Enter `project_id: "194"` and `session_id: "test_session"` $\rightarrow$ Run Tool to acquire Token 2.
3. **Data & Document Tools**:
   - Run `get_project_permissions` with `project_id: "194"`. Verify permissions list and check that `view_url` fields contain the full `https://api.dev.batman.co.in/...` URL.
   - Run `view_permission_document` with `project_id: "194"`, `trans_project_per_id`, and `file_id`.

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

> **Why `mcp-remote`?**  
> `npx -y mcp-remote` is a lightweight proxy that bridges Claude Desktop's local `stdio` communication to your remote HTTPS/SSE endpoint on Render seamlessly, without requiring any local Python installation on the client machine.

---

### Step 3: Restart Claude Desktop

1. Completely close Claude Desktop (check the Windows system tray / taskbar to ensure it is not minimized).
2. Re-open **Claude Desktop**.
3. Look at the bottom-right of the chat box for the **Hammer / Tools icon (🔨)**.
4. Click it to verify all 11 Stallion tools are loaded:
   - `send_otp`, `verify_otp`, `switch_project`
   - `get_user_profile`, `get_user_projects`, `get_project_details`, `get_project_towers`
   - `get_notifications`, `get_assigned_modules`, `get_developer_users`, `get_project_users`
   - `get_project_permissions`, `view_permission_document`

---

## 4. How to Converse with the AI Assistant

Claude will orchestrate the two-token authentication flow automatically:

### Example Chat Flow:

```text
1. User: "Please log me in with mobile number 8291598930."
   AI:   [Calls send_otp]
         "An OTP has been sent to your mobile. Please provide the code."

2. User: "1234"
   AI:   [Calls verify_otp -> acquires Token 1]
         [Calls get_user_projects]
         "You are logged in! Found project: 'Sharda Project' (ID: 194)."

3. User: "Switch to Sharda Project and show me the permissions and drawings."
   AI:   [Calls switch_project -> acquires Token 2]
         [Calls get_project_permissions]
         "Here are the permissions for Sharda Project:
          - Last Approved Plan (AutoCAD DWG Drawing)
          - View/Download Link: https://api.dev.batman.co.in/..."

4. User: "Can I view the drawing?"
   AI:   [Calls view_permission_document]
         "This is an AutoCAD DWG CAD drawing. You can download it directly 
          via the view URL and open it using AutoCAD or Autodesk Viewer."
```

---

## 5. Alternative Integrations (Gemini & ChatGPT)

### A. Google Gemini / Antigravity IDE
Add the server to `.agents/mcp_config.json` or `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "stallion-mcp": {
      "url": "https://stallion-mcp-server-test.onrender.com/sse",
      "transport": "sse"
    }
  }
}
```

### B. ChatGPT (via Custom GPT or MCP Web Clients)
- **Custom GPT**: In ChatGPT, create a GPT and add an Action pointing to the backend endpoints.
- **MCP Web Clients**: Use [Cherry Studio](https://cherry-ai.com/) or [LibreChat](https://www.librechat.ai/) with your OpenAI API key and configure the SSE URL `https://stallion-mcp-server-test.onrender.com/sse`.

---

## 6. Common Troubleshooting

| Issue | Cause & Solution |
|---|---|
| **Render Spin-up Delay (30–60s)** | Free tier Render containers sleep when idle. The first request may take ~45 seconds while the server spins up. |
| **Hammer Icon (🔨) Not Showing in Claude** | 1. Check `claude_desktop_config.json` for JSON syntax errors (no trailing commas).<br>2. Confirm Node.js is installed (`node -v`).<br>3. Completely exit and restart Claude from Task Manager. |
| **Viewing DWG vs PDF Files** | - **PDFs**: Have direct view URLs and can be opened in any browser/PDF reader.<br>- **DWGs**: Are AutoCAD binary files. Claude provides the direct download link to open in AutoCAD or [Autodesk Viewer](https://viewer.autodesk.com/). |
