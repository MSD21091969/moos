# Communication Protocols

> All communication channels in Collider architecture.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           COMMUNICATION MAP                                      │
│                                                                                  │
│  CHROME EXTENSION                                                               │
│  ┌─────────────────┐                                                            │
│  │ Service Worker  │                                                            │
│  │ (Orchestrator)  │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                      │
│    ┌──────┼───────┬────────────────┬────────────────┐                           │
│    │      │       │                │                │                           │
│    ▼      ▼       ▼                ▼                ▼                           │
│  ┌────┐ ┌────┐ ┌────────┐    ┌──────────┐    ┌──────────────┐                  │
│  │Tab │ │Side│ │Offscr  │    │Native    │    │External      │                  │
│  │CS  │ │Panl│ │Doc     │    │Host      │    │Servers       │                  │
│  └────┘ └────┘ └────────┘    └──────────┘    └──────────────┘                  │
│    ▲               ▲              │                │                            │
│    │               │              │                │                            │
│ chrome.runtime  chrome.runtime    │                │                            │
│    .sendMessage  .sendMessage     │                │                            │
│                                   │                │                            │
│                            ┌──────┴────┐    ┌──────┴──────────────┐            │
│                            │ Filesystem│    │ Data    │ GraphTool │            │
│                            │ .agent/   │    │ Server  │ Server    │            │
│                            └───────────┘    └─────────┴───────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Internal (Chrome Extension)

| Channel             | Method                         | Use Case                |
| ------------------- | ------------------------------ | ----------------------- |
| SW ↔ Content Script | `chrome.tabs.sendMessage`      | Tab-specific operations |
| SW ↔ Sidepanel      | `chrome.runtime.sendMessage`   | UI updates              |
| SW ↔ Offscreen      | `chrome.runtime.sendMessage`   | Heavy compute           |
| Any ↔ Storage       | `chrome.storage.local/session` | State persistence       |

## External

| Channel                 | Protocol               | Use Case                    |
| ----------------------- | ---------------------- | --------------------------- |
| Extension ↔ Native Host | JSON over stdin/stdout | FILESYST access             |
| Extension ↔ Data Server | REST/HTTP + SSE        | CRUD, real-time updates     |
| Extension ↔ GraphTool   | WebSocket              | Graph operations, streaming |

## Data Server Endpoints

| Endpoint          | Method    | Purpose                  |
| ----------------- | --------- | ------------------------ |
| `/api/v1/context` | GET/POST  | Read/write nodecontainer |
| `/api/v1/nodes`   | CRUD      | Node operations          |
| `/api/v1/users`   | CRUD      | User/account operations  |
| `/api/v1/sse`     | GET (SSE) | Real-time events         |

## GraphTool Server

| Endpoint       | Protocol  | Purpose                       |
| -------------- | --------- | ----------------------------- |
| `/ws/graph`    | WebSocket | Graph queries, mutations      |
| `/ws/workflow` | WebSocket | Workflow execution, streaming |
