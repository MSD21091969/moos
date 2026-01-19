# Agent Studio

Integrated DeepAgent Application acting as the **Reference Implementation** for the Factory.
Demonstrates the **Studio Pattern** (Framework-First Design).

## Quick Start

```powershell
# Terminal 1: Install & run backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: Install & run frontend
cd frontend
npm install
npm install lucide-react react-markdown
npm run dev
```

Open http://localhost:3000

## Features

- **Coordinator Agent** with skills and subagent delegation
- **3 Subagents**: Researcher, Coder, Analyst
- **2 Skills**: Math Helper, Code Reviewer
- **WebSocket Streaming** with thinking panel
- **SQLite Persistence** for conversations
- **REST API** for conversation CRUD

## Architecture

```
agent-studio/
├── backend/
│   ├── app/
│   │   ├── main.py      # FastAPI + WebSocket
│   │   ├── agents/      # Coordinator + subagents
│   │   ├── db.py        # SQLite
│   │   └── deps.py      # GCP config
│   ├── skills/          # SKILL.md files
│   └── data/            # File storage
└── frontend/
    └── src/
        ├── app/page.tsx     # Chat UI
        └── hooks/useChat.ts # WebSocket hook
```

## API Endpoints

- `WS /ws/chat` - Chat with streaming
- `GET /api/conversations` - List conversations
- `GET /api/conversations/{id}` - Get conversation
- `DELETE /api/conversations/{id}` - Delete conversation
