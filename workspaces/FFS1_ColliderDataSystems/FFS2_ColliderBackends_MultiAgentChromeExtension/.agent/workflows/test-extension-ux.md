---
description: How to test the Multi-Agent Chrome Extension Sidepanel UX and
WebSocket connection
---

# Testing the Chrome Extension Sidepanel

This workflow provides the exact steps to verify that the Chrome Extension
sidepanel can successfully connect to the `NanoClawBridge` WebSocket, retrieve
contexts, and stream responses from the `AnthropicAgent`.

## Prerequisites

Ensure all required services are running, specifically:

1. `ColliderDataServer` (REST API - port 8000)
2. `ColliderAgentRunner` (Context gRPC - port 8004)
3. `NanoClawBridge` (WebSocket Bridge - port 18789)
4. `FFS6` (Frontend Viewer - port 4200)

(You can run the `/dev-start` workflow to launch all of these).

## Step-by-Step UI Verification

### 1. Open Service Verification Tabs

Before testing the extension, open your browser and load the following service
endpoints in separate tabs to verify they are running:

1. **Frontend:** `http://localhost:4200/`
2. **DataServer Docs:** `http://localhost:8000/docs`
3. **GraphToolServer Docs:** `http://localhost:8001/docs`
4. *(Skip `8002` VectorDB and `8003` SQLite Web)*
5. **AgentRunner Docs:** `http://localhost:8004/docs`

### 2. Load the Extension Sidepanel

1. While on any page, click the browser's side panel icon and select "Collider Multi-Agent Chrome Extension".
2. **IMPORTANT:** You must operate the agent interface from *within the
   sidepanel itself*, not from the main FFS6 web page. The NanoClaw agent is
   designed to be hosted in the extension.

### 2. Compose Context

1. In the sidepanel, under the **Collider** header, verify you are on the **Tree** tab.
2. Click the **Select application...** dropdown and choose your seeded application (e.g., `Application 2XZ`).
3. Click on a node in the tree (e.g., `admin` or a child node) to select it as the context root.

### 3. Start the Session

1. Switch to the **Agent** tab in the sidepanel.
2. The UI should now display a "Context Composer" section indicating the selected node.
3. Click the button to **Start Session**.
4. The UI should show "Session active" with a session ID displayed.

### 4. Verify WebSocket Streaming

1. In the chat input box at the bottom ("Message the agent..."), type a test message: `Hello Agent, are you connected?`
2. Press `Enter` or click the Send button.
3. **Expected Behavior:**
   - The message should immediately appear in the chat history.
   - Within 5-10 seconds, the agent should reply in the chat history (e.g., "Yes, I am connected...").
   - If you check the terminal running `NanoClawBridge` (port 18789), you should see pino logs confirming the `text_delta` and `message_end` events streaming.

## Troubleshooting

- **"Connection Refused" in Sidepanel UI:** Ensure `npm run dev` in
   `NanoClawBridge` is actually running on port 18789 and you have a valid
   `ANTHROPIC_API_KEY` in `NanoClawBridge/.env`.
- **Extension fails to load application tree:** Ensure `ColliderDataServer` is running on port 8000 and the database is seeded.
- **Agent fails to reply:** Check the `ColliderAgentRunner` logs (port 8004)
   to see if the gRPC context request failed. Ensure `GEMINI_API_KEY` is set in
   the `secrets/api_keys.env`.
