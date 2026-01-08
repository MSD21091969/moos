# Agent Factory

Engineering workspace for Collider agent definitions, models, and runtime environments.

## Purpose

This workspace is dedicated to developing:

- **Definitions**: Pydantic models for agent specifications
- **Runtimes**: Execution environments for agents
- **Templates**: Starter kits for new agent projects

## Structure

```
D:\agent-factory\
├── definitions/     # ColliderPilotDefinition models
├── runtimes/        # Runtime execution patterns
├── templates/       # Project scaffolds
└── docs/            # Design documentation
```

## Related Projects

| Project                     | Purpose                         |
| --------------------------- | ------------------------------- |
| `D:\dev-assistant\`         | First agent (dev tools + gmail) |
| `D:\my-tiny-data-collider\` | Main Collider application       |

## Stack

- **Python 3.14** + uv
- **Pydantic v2** for definitions
- **Ollama** for local LLM
- **PydanticAI** for agent framework

## Quick Start

```powershell
cd D:\agent-factory
uv run python -c "print('Ready')"
```
