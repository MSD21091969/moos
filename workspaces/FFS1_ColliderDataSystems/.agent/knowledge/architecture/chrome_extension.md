# Chrome Extension Architecture

> Multi-agent Chrome Extension built with Plasmo.

## Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHROME EXTENSION                              │
│                                                                  │
│  ┌─────────────────┐     ┌──────────────────────────────────┐  │
│  │ SERVICE WORKER  │────▶│ OFFSCREEN DOCUMENT               │  │
│  │ (Orchestrator)  │     │ ─────────────────────            │  │
│  │                 │     │ • WebGPU                         │  │
│  └────────┬────────┘     │ • LangGraph.js Agent             │  │
│           │              │ • Heavy computation              │  │
│           ▼              └──────────────────────────────────┘  │
│  ┌─────────────────┐                                           │
│  │ CONTENT SCRIPTS │     ┌──────────────────────────────────┐  │
│  │ (Per-tab agent) │     │ SIDEPANEL / DocPiP               │  │
│  └─────────────────┘     │ • User interface                 │  │
│                          │ • Chat / controls                 │  │
│                          └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Communication

- **Internal**: chrome.runtime messaging
- **External**:
  - Native Messaging → Filesystem
  - REST/SSE → Data Server
  - WebSocket → GraphTool Server

## Context Layering

- **Layer 0**: App0 default (always present)
- **Layer N**: Active tab appnode (additive)
