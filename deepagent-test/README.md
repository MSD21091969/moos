# VStorm DeepAgent Framework & Full-Stack Template

> **AI-Optimized Documentation** for the Factory Workspace  
> Covers `pydantic-deepagents` (Exp 1-7) and `full-stack-fastapi-nextjs-llm-template`

---

## Quick Reference

| Repository                                                                                                    | Purpose                                   | Factory Location              |
| ------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ----------------------------- |
| [pydantic-deepagents](https://github.com/vstorm-co/pydantic-deepagents)                                       | Agent creation framework on Pydantic-AI   | `deepagent-test/experiments/` |
| [full-stack-fastapi-nextjs-llm-template](https://github.com/vstorm-co/full-stack-fastapi-nextjs-llm-template) | Production template with 20+ integrations | `demos/full-stack-agent/`     |

---

## Part 1: pydantic-deepagents

### Core Pattern

```python
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_ai_backends import FilesystemBackend

agent = create_deep_agent(
    model="google-vertex:gemini-2.5-flash",
    instructions="Your system prompt",
    tools=[...],              # Custom @tool functions
    toolsets=[...],           # FunctionToolset objects
    skill_directories=[...],  # Paths to SKILL.md folders
    subagents=[...],          # SubAgentConfig objects
    output_type=MyModel,      # Pydantic model for structured output
    history_processors=[...]  # Summarization processors
)

deps = DeepAgentDeps(backend=FilesystemBackend("./data"))
result = await agent.run("User query", deps=deps)
```

### Features Implemented & Verified

| Feature                 | Experiment | Status      | Notes                                           |
| ----------------------- | ---------- | ----------- | ----------------------------------------------- |
| **Basic Toolset**       | exp1       | ✅ Verified | `@agent.tool` decorator pattern                 |
| **Skills System**       | exp2       | ✅ Verified | SKILL.md loading via `skill_directories`        |
| **Subagent Delegation** | exp3       | ✅ Verified | `SubAgentConfig` + register in `deps.subagents` |
| **File Uploads**        | exp4       | ✅ Verified | `run_with_files()` + `FilesystemBackend`        |
| **Streaming**           | exp5       | ⏸️ Pending  | Token-by-token output (tested in Full Stack)    |
| **Sessions**            | exp6       | ⏸️ Pending  | `SessionManager` for isolation                  |
| **Vision/Multimodal**   | exp7       | ✅ Verified | Image analysis with Gemini                      |

### Key Learnings

1. **Subagent Registration**: Pre-created agents **must** be registered in `deps.subagents`:

   ```python
   deps.subagents["researcher"] = researcher
   deps.subagents["coder"] = coder
   ```

2. **Backend Initialization**: Use positional argument, not keyword:

   ```python
   backend = FilesystemBackend("./data")  # Correct
   # backend = FilesystemBackend(base_path="./data")  # Wrong
   ```

3. **Streaming is Snapshots**: Gemini stream chunks are cumulative (snapshots), not deltas.

---

## Part 2: Full-Stack Template

### Architecture

```
backend/
├── app/
│   ├── main.py           # FastAPI + WebSocket
│   ├── agents/           # pydantic-deep agents
│   ├── deps.py           # GCP auth + backend injection
│   └── models.py         # WebSocket message types
frontend/
├── src/
│   ├── app/page.tsx      # Chat UI
│   └── hooks/useChat.ts  # WebSocket hook
```

### What We Implemented

| Component           | VStorm Feature          | Factory Implementation                |
| ------------------- | ----------------------- | ------------------------------------- |
| Backend Framework   | FastAPI + Pydantic v2   | ✅ `demos/full-stack-agent/backend/`  |
| Agent Integration   | PydanticAI              | ✅ `coordinator.py`                   |
| WebSocket Streaming | Real-time responses     | ✅ `/ws/chat` endpoint                |
| Frontend Framework  | Next.js 15 + React      | ✅ `demos/full-stack-agent/frontend/` |
| Chat Interface      | Message display + input | ✅ `page.tsx`                         |
| State Hook          | useChat / useWebSocket  | ✅ `useChat.ts`                       |
| File Storage        | FilesystemBackend       | ✅ `./data/full-stack-storage/`       |

### What We Did NOT Implement (Yet)

| VStorm Feature           | Category             | Priority |
| ------------------------ | -------------------- | -------- |
| PostgreSQL/MongoDB       | Database             | Future   |
| JWT + Refresh Tokens     | Auth                 | Future   |
| OAuth2 (Google)          | Auth                 | Future   |
| Celery/Taskiq/ARQ        | Background Tasks     | Future   |
| Django-style CLI         | CLI Commands         | Future   |
| Redis Caching            | Performance          | Future   |
| Rate Limiting (slowapi)  | Security             | Future   |
| Admin Panel (SQLAdmin)   | Admin                | Future   |
| Logfire/LangSmith        | Observability        | Future   |
| Sentry                   | Error Tracking       | Future   |
| Prometheus               | Metrics              | Future   |
| Webhooks                 | Integrations         | Future   |
| i18n                     | Internationalization | Future   |
| Dark Mode Toggle         | UI                   | Future   |
| Playwright E2E Tests     | Testing              | Future   |
| Docker Compose           | Deployment           | Future   |
| Conversation Persistence | DB Storage           | Future   |

---

## Part 3: Model Verification

### GCP Vertex AI (Primary)

| Model                                | Role              | Tool Support |
| ------------------------------------ | ----------------- | ------------ |
| `google-vertex:gemini-2.5-flash`     | Primary           | ✅ Verified  |
| `google-vertex:gemini-2.5-pro`       | Complex Reasoning | ✅ Verified  |
| `google-vertex:gemini-3-pro-preview` | Vision (Preview)  | ✅ Verified  |

### Local Ollama (Legacy)

| Model           | Tool Support |
| --------------- | ------------ |
| qwen3:14b       | ✅ Yes       |
| codellama:13b   | ❌ No        |
| deepseek-r1:14b | ❌ No        |

---

## Usage Guide

### Running the Full Stack Demo

```powershell
# Terminal 1: Backend
cd D:\agent-factory\demos\full-stack-agent\backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd D:\agent-factory\demos\full-stack-agent\frontend
npm run dev
```

Open http://localhost:3001

### Creating a New Agent

```python
from pydantic_deep import create_deep_agent, SubAgentConfig

my_agent = create_deep_agent(
    model="google-vertex:gemini-2.5-flash",
    instructions="You are a specialized assistant for X.",
    skill_directories=["./skills/my-skill"],
    retries=3
)
```

### Adding Skills

Create `skills/my-skill/SKILL.md`:

```markdown
---
name: my_skill
description: What this skill does
---

## Instructions

When the user asks for X, do Y.
```

---

## Open Questions for Next Phase

1. **TodoToolset Integration**: How to map to Collider Graph execution?
2. **GraphBackend**: Can we create a custom backend for Collider persistence?
3. **Session Isolation**: How to integrate with Collider's user context?
4. **Context Summarization**: Use VStorm's processor or wait for pydantic-ai core?

---

## References

- [pydantic-deepagents Docs](https://vstorm-co.github.io/pydantic-deepagents/)
- [Full-Stack Template Docs](https://github.com/vstorm-co/full-stack-fastapi-nextjs-llm-template)
- [VStorm GitHub](https://github.com/vstorm-co)
