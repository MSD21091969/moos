# Agent Studio

Integrated DeepAgent Application acting as the **Reference Implementation** for the Factory.
Demonstrates the **Studio Pattern** (Framework-First Design).

## Quick Start (Factory Environment)

Run the studio from the factory root using the provided PowerShell script. This handles ports (Backend: 9001, Frontend: 3001) and environment variables automatically.

```powershell
# In d:\agent-factory
.\run_studio.ps1
```

Access the application:

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:9001/docs

### Standalone Development

To run standalone (default ports 8000/3000):

```powershell
# Terminal 1: Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

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
