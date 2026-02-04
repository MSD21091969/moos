# LangGraph.js ↔ Pydantic AI Graph Integration

> How browser agent and server graph logic "meet" in the container.

## The Meeting Point

Both systems read/write the **same container**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      NODE CONTAINER                              │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │ instructions/ │  │ workflows/    │  │ tools/        │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│         ▲                   │ ▲               │                  │
│         │                   │ │               │                  │
│  ┌──────┴──────┐            │ │            ┌──┴───────────┐     │
│  │ LANGGRAPH.JS│            ▼ │            │ PYDANTIC AI  │     │
│  │ (Browser)   │────────────┘ └────────────│ GRAPH        │     │
│  │             │                           │ (Server)     │     │
│  └─────────────┘                           └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow

1. **Agent reads** context from container
2. **Agent generates** workflow (code, instructions)
3. **Agent writes** workflow to container
4. **Server reads** new workflow
5. **Server creates** new subnode with new container

## Shared Schema

Both systems validate against same schema (JSON Schema / Pydantic).

## Communication

- Container sync: REST API
- Real-time: WebSocket
- Events: SSE
