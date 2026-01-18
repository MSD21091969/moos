# pydantic-deepagents Research Summary

**Date**: 2026-01-16  
**Purpose**: Phase 4.5 research before building decoupled experiments

---

## Core Architecture

### 1. Agent Creation Pattern

```python
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_ai_backends import StateBackend

agent = create_deep_agent(
    model="openai:gpt-4.1",
    instructions="You are a helpful assistant",
    tools=[...],           # Custom functions
    toolsets=[...],        # FunctionToolset objects
    skill_directories=[...],  # Path to SKILL.md folders
    subagents=[...],       # SubAgentConfig objects
    output_type=...,       # Pydantic model for structured output
    history_processors=[...]  # Summarization processors
)

deps = DeepAgentDeps(backend=StateBackend())
result = await agent.run("Your prompt", deps=deps)
```

**Key Pattern**: `create_deep_agent()` returns a pydantic-ai agent with enhanced capabilities.

---

## Four Core Features

### 📋 1. Planning (TodoToolset)

**Purpose**: Built-in task decomposition and tracking

**Via**: `pydantic-ai-todo` package (extracted, standalone)

**Pattern**:

```python
from pydantic_ai_todo import TodoToolset

agent = create_deep_agent(
    toolsets=[TodoToolset()]
)
```

**Behavior**: Agent automatically breaks down complex tasks into subtasks and tracks progress.

**Collider Relevance**: Could map to Graph nodes + execution tracking.

---

### 📁 2. Filesystem (FilesystemToolset)

**Purpose**: Virtual/real file operations with grep/glob

**Via**: `pydantic-ai-backend` package (extracted, standalone)

**Backends**:

- `StateBackend` - in-memory (testing)
- `FilesystemBackend` - persistent disk storage
- `DockerSandbox` - isolated execution
- `CompositeBackend` - combine multiple

**Pattern**:

```python
from pydantic_ai_backends import FilesystemBackend
from pydantic_deep import DeepAgentDeps

backend = FilesystemBackend(base_path="./outputs")
deps = DeepAgentDeps(backend=backend)

# Agent can now use file tools: read_file, write_file, etc.
```

**File Uploads**:

```python
from pydantic_deep import run_with_files

with open("data.csv", "rb") as f:
    result = await run_with_files(
        agent,
        "Analyze this CSV",
        deps,
        files=[("data.csv", f.read())]
    )
```

**Collider Relevance**: Execution environment for StepNodes.

---

### 🤖 3. Subagents (Delegation)

**Purpose**: Specialized task delegation with context isolation

**Pattern**:

```python
from pydantic_deep import create_deep_agent, SubAgentConfig

# Specialist agents
researcher = create_deep_agent(
    instructions="You research topics thoroughly"
)

coder = create_deep_agent(
    instructions="You write clean code"
)

# Coordinator with subagents
coordinator = create_deep_agent(
    instructions="You coordinate work",
    subagents=[
        SubAgentConfig(
            name="researcher",
            agent=researcher,
            triggers=["research", "investigate"]
        ),
        SubAgentConfig(
            name="coder",
            agent=coder,
            triggers=["code", "implement"]
        )
    ]
)
```

**Behavior**: When keywords match triggers, coordinator delegates to subagent.

**Collider Relevance**: SubgraphNode pattern, nested Definitions.

---

### 🎯 4. Skills (SKILL.md)

**Purpose**: Modular capability packages loaded on-demand

**Pattern**:

```markdown
# skills/math-helper/SKILL.md

---

name: math_helper
description: Advanced mathematical operations

---

## Capabilities

- Complex calculations
- Statistical analysis

## Instructions

When asked for math:

1. Use available tools first
2. Show step-by-step work
```

```python
agent = create_deep_agent(
    skill_directories=["./skills/math-helper", "./skills/code-review"]
)
```

**Behavior**: Markdown content is injected into system prompt, extending capabilities without tool code.

**Collider Relevance**: Definition metadata, agent behavior configuration.

---

## Additional Features

### Structured Output

```python
from pydantic import BaseModel

class TaskAnalysis(BaseModel):
    priority: str
    hours: float

agent = create_deep_agent(output_type=TaskAnalysis)
result = await agent.run("Analyze task")
print(result.output.priority)  # Type-safe
```

### Streaming

```python
async for chunk in agent.run_stream("Generate story", deps=deps):
    print(chunk, end="", flush=True)
```

### Session Management

```python
from pydantic_deep import SessionManager

manager = SessionManager(
    default_runtime="local",
    default_idle_timeout=3600
)
manager.start_cleanup_loop(interval=300)

session = await manager.get_or_create("user-123")
await agent.run("Task", deps=session.deps)
```

### Context Summarization

```python
from pydantic_deep.processors import create_summarization_processor

processor = create_summarization_processor(
    trigger=("tokens", 100000),  # Summarize at 100k tokens
    keep=("messages", 20)  # Keep last 20 messages
)

agent = create_deep_agent(history_processors=[processor])
```

---

## llms.txt Standard

**URL**: https://llmstxt.org/

**Purpose**: Standardized markdown format for LLM-friendly documentation

**Format**:

```markdown
# Project Name

> Brief description

Detailed context here.

## Core Documentation

- [Getting Started](url): Setup guide
- [API Reference](url): Complete API

## Optional

- [Advanced Topics](url): Can skip for shorter context
```

**Key Points**:

- Located at `/llms.txt` in site root
- Markdown lists with hyperlinks `[name](url)`
- Optional section can be skipped for shorter context
- Companion `.md` files for each HTML page (e.g., `page.html.md`)

**Collider Relevance**: Could standardize Definition documentation, graph metadata.

---

## Modular Components (Standalone)

| Package               | Purpose                  | Use Independently? |
| --------------------- | ------------------------ | ------------------ |
| `pydantic-ai`         | Core agent framework     | ✅ Foundation      |
| `pydantic-ai-backend` | File storage + sandboxes | ✅ Yes             |
| `pydantic-ai-todo`    | Task planning toolset    | ✅ Yes             |
| `pydantic-deep`       | Integrates all above     | ✅ Wrapper         |

**Architecture Pattern**: Small, composable packages vs monolithic.

---

## Key Insights for Collider

### 1. Separation of Concerns

- **Agent Definition** (YAML/Python config) separate from **Runtime** (SessionManager, Backend)
- **Toolsets** (functions) separate from **Skills** (prompts)
- **Backend abstraction** allows switching storage without changing agent code

### 2. Dependency Injection

- `RunContext[DeepAgentDeps]` pattern allows tools to access shared state
- `DeepAgentDeps` can be extended with custom fields
- Session isolation via `SessionManager`

### 3. Delegation Patterns

- Subagents triggered by keywords (`triggers=["research"]`)
- Each subagent has isolated context
- Coordinator orchestrates, specialists execute

### 4. Skills as Prompts

- Alternative to tools: markdown instructions
- Lighter weight (no function code)
- Can combine with toolsets

### 5. File Handling

- Backend abstraction (in-memory, disk, docker)
- Upload files → available in agent context
- Tools can access via `ctx.deps.backend`

---

## Questions for Experiments

1. **TodoToolset**: How does task decomposition work internally? Can we adapt for Graph execution plans?
2. **Skills**: How are SKILL.md files discovered and loaded? Can we auto-generate from Definition metadata?
3. **Subagents**: How is context passed between coordinator and subagent? Does it share conversation history?
4. **Backends**: Can we create a GraphBackend that persists to our database?
5. **Streaming**: How does streaming interact with tool calls? Can we stream intermediate results?
6. **Sessions**: How does session cleanup work? What happens to running tasks?

---

## Next Steps

1. Set up `deepagent-test/` directory
2. Install dependencies (`pydantic-deep`, `pydantic-ai-backend`, `pydantic-ai-todo`)
3. Run 6 experiments to answer questions above
4. Document patterns in `learnings.md`
5. Create recommendations for Phase 5 integration
