# 🏭 FFS0 Factory

Welcome to the **FFS0 Factory**, the root monorepo for the **Collider Ecosystem**. This repository houses the unified architecture for our multi-agent platform, encompassing our data governance, backend runtimes, and interconnected frontend applications.

---

## 🌐 FFS0 Factory Ecosystem

The Collider Ecosystem is built to seamlessly bridge automated agent workflows, graph-based system context, and high-performance UI interfaces. The FFS0 Factory acts as the central hub, defining the contracts, orchestration layers, and shared knowledge bases that empower the suite of connected applications.

Key Highlights:
- **Unified Governance:** Single source of truth for schemas, system instructions, and `.agent` context chains.
- **Multi-Agent Chrome Extension Backend:** Full support for MOOS (Multi-Agent Operating System) compatibility runtimes.
- **Modular Frontends:** Flexible IDE viewers, sidepanels, and Picture-in-Picture (PiP) interfaces built with React 19 and Nx.

---

## 🔒 Local-First Architecture

We prioritize speed, security, and developer ergonomics through a **Local-First Architecture**:
- **Zero-Latency Execution:** Core data services and vector search run entirely locally.
- **Privacy by Default:** Your code, graph context, and agent conversations never leave your machine unless explicitly routed.
- **Standalone Runtimes:** The MOOS compatibility engine runs as a robust local server, exposing standard interfaces (REST, WebSockets, MCP) to IDEs and extensions without relying on external cloud endpoints.
- **Native Context Delivery:** Tools and context are provided instantly via local Model Context Protocol (MCP) servers on standard ports.

---

## 🗺️ Workspace Map

The monorepo is divided into three primary functional domains:

### 1. `FFS1_ColliderDataSystems`
The governance, orchestration, and shared contracts layer. 
- **Stack:** Python 3.12+, FastAPI, Pydantic v2, UV.
- **Responsibilities:** Core data models, schema definitions, and agent inheritance state (`.agent` backbone).

### 2. `FFS2_ColliderBackends_MultiAgentChromeExtension/moos`
The active backend compatibility runtime.
- **Stack:** Node, Python, SQLite.
- **Responsibilities:** Powers the MOOS runtime, providing data compatibility, tool execution, agent orchestration, and the NanoClaw WebSocket bridge. *(Note: Legacy FFS2 folders are retained for contract parity).*

### 3. `FFS3_ColliderApplicationsFrontendServer`
The frontend presentation layer and shared UI library.
- **Stack:** Nx Monorepo, React 19, TypeScript 5+, Vite 7.
- **Applications:**
  - **`ffs6`**: IDE Viewer (Primary full-screen interface)
  - **`ffs4`**: Chrome Extension Sidepanel (Agent chat & graph view)
  - **`ffs5`**: Picture-in-Picture (PiP) App
  - **`shared-ui`**: Internal design system

---

## 🔌 Active Runtime Ports

The FFS0 architecture relies on standardized ports for seamless communication between the UI, tools, and agents.

| Surface                  | Port    | Protocol  | Owner | Description                                     |
| :----------------------- | :------ | :-------- | :---- | :---------------------------------------------- |
| **MOOS Data Server**     | `8000`  | REST      | FFS2  | Primary data API / workspace graph retrieval    |
| **MOOS Tool/MCP Server** | `8001`  | SSE/HTTP  | FFS2  | Model Context Protocol endpoints                |
| **MOOS Agent Runner**    | `8004`  | REST      | FFS2  | Agent session compatibility & runtime execution |
| **NanoClaw WS Bridge**   | `18789` | WebSocket | FFS2  | Live bidirectional RPC for agents               |
| **FFS6 Frontend**        | `4200`  | HTTP      | FFS3  | IDE Viewer application                          |
| **FFS4 Sidepanel**       | `4201`  | HTTP      | FFS3  | Chrome Extension sidepanel UI                   |
| **FFS5 PiP App**         | `4202`  | HTTP      | FFS3  | Picture-in-Picture application                  |

*Tip: To add the local MCP server to Claude, run:*
`claude mcp add collider-tools --transport sse http://localhost:8001/mcp/sse`

---

## 🚀 Quick Start

Follow these steps to spin up the entire Collider platform locally.

### 1. Install Dependencies
Always use `pnpm` from the `FFS1_ColliderDataSystems` root for package management.
```bash
cd workspaces/FFS1_ColliderDataSystems
pnpm install
```

### 2. Configure Environment
Ensure your API keys (like OpenAI/Anthropic/etc.) are set in the global `.env` file:
```bash
cp ../../secrets/api_keys.example.env ../../secrets/api_keys.env
# Edit ../../secrets/api_keys.env with your keys
```

### 3. Start the Backend Runtimes (MOOS)
Fire up the backend services to enable data APIs, agent runners, and MCP servers:
```bash
pnpm nx run @moos/source:compat:serve:backend
```

### 4. Start the Frontend (FFS6 Viewer)
In a new terminal instance, start the primary UI viewer:
```bash
pnpm nx serve ffs6
```
Open [http://localhost:4200](http://localhost:4200) in your browser.

*(To view the sidepanel, run `pnpm nx serve ffs4` and navigate to `http://localhost:4201`)*