# Factory Pipeline Status

## Current Flow

```
Gödel (CLI/Factory)
    ↓ orchestrates
Pilot (localhost:8001)
    ↓ observes via
ChatAgent (localhost:5174)
    ↓ collects to
data/ (observations, chats, assessments)
    ↓ analyzed by
Gödel → recommends → models/definitions/runtimes
```

## Services

| Service   | Command                              | Port |
| --------- | ------------------------------------ | ---- |
| Frontend  | `npm run dev:demo` (legacy-collider) | 5174 |
| Pilot API | `uv run python godel/pilot_api.py`   | 8001 |
| Gödel CLI | `uv run python cli.py spawn godel`   | -    |

## Data Files

- `data/observations.jsonl` - Grid snapshots from ChatAgent
- `data/pilot_chat.jsonl` - Pilot conversations
- `data/godel_assessments.jsonl` - Architecture recommendations

## Key Endpoints

| Endpoint             | Purpose                               |
| -------------------- | ------------------------------------- |
| `GET /ui`            | Pilot WebUI with chat + assess button |
| `POST /observe`      | Receive grid observation              |
| `POST /chat`         | Chat with Pilot (Ollama)              |
| `POST /godel/assess` | Request architecture recommendations  |

## Goal

Collect data from this pipeline to:

1. Improve Factory parts
2. Feed Antigravity IDE code assist
3. Plan/implement via chat
