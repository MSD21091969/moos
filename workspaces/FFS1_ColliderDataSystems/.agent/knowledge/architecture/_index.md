# Architecture Knowledge

> System architecture documentation for Collider Chrome Extension.

## Documents

### Core Concepts

| File                                         | Purpose                |
| -------------------------------------------- | ---------------------- |
| [nodecontainer.md](nodecontainer.md)         | Universal node pattern |
| [context_hierarchy.md](context_hierarchy.md) | Inheritance system     |
| [domains.md](domains.md)                     | FILESYST, CLOUD, ADMIN |
| [applications.md](applications.md)           | App0, AppX, AppZ, App1 |

### Chrome Extension System

| File                                             | Purpose                        |
| ------------------------------------------------ | ------------------------------ |
| [chrome_extension.md](chrome_extension.md)       | Extension components overview  |
| [ui_ux_pip_sidepanel.md](ui_ux_pip_sidepanel.md) | **DocPiP & Sidepanel UI**      |
| [langgraph_topology.md](langgraph_topology.md)   | **Multi-tab Routing & Events** |
| [native_messaging.md](native_messaging.md)       | Filesystem access              |

### Data & Security

| File                                         | Purpose                          |
| -------------------------------------------- | -------------------------------- |
| [auth_admin_flow.md](auth_admin_flow.md)     | **Login -> Admin Context**       |
| [communication.md](communication.md)         | All protocols (Native, WS, SSE)  |
| [graph_integration.md](graph_integration.md) | LangGraph.js ↔ Pydantic AI Graph |
