"""Pilot API - FastAPI server for ChatAgent ↔ Pilot communication.

This is the bridge between the frontend ChatAgent and the local Collider Pilot.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from pathlib import Path
import json
import ollama

app = FastAPI(
    title="Collider Pilot API",
    description="Bridge between ChatAgent (frontend) and Collider Pilot (local)",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data paths
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OBSERVATIONS_FILE = DATA_DIR / "observations.jsonl"
COMMANDS_FILE = DATA_DIR / "commands.jsonl"
CHAT_FILE = DATA_DIR / "pilot_chat.jsonl"

# Static files (WebUI)
STATIC_DIR = Path(__file__).parent / "pilot_ui"


# --- Models ---

class GridObservation(BaseModel):
    """Observation from ChatAgent about the grid state."""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    containers: list[dict] = Field(default_factory=list)
    active_container_id: str | None = None
    selected_node_ids: list[str] = Field(default_factory=list)
    user_action: str | None = None  # What user just did
    metadata: dict = Field(default_factory=dict)


class PilotCommand(BaseModel):
    """Command from Pilot to ChatAgent."""
    id: str
    command: str  # "observe", "create_node", "delete_node", "navigate", etc.
    args: dict = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 0  # 0=low, 1=normal, 2=high


class PilotResponse(BaseModel):
    """Response from Pilot after processing observation."""
    status: str  # "received", "processing", "analyzed"
    message: str
    analysis: dict | None = None
    commands: list[PilotCommand] = Field(default_factory=list)


class GodelReport(BaseModel):
    """Report from Pilot to Gödel."""
    session_id: str
    observation_count: int
    patterns: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


# --- Storage ---

def append_jsonl(path: Path, data: dict):
    """Append a record to a JSONL file."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


def read_jsonl(path: Path, limit: int = 100) -> list[dict]:
    """Read last N records from JSONL file."""
    if not path.exists():
        return []
    
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    lines = [l for l in lines if l]
    return [json.loads(l) for l in lines[-limit:]]


# --- In-memory state ---

command_queue: list[PilotCommand] = []
observations: list[GridObservation] = []


# --- Endpoints ---

@app.get("/")
async def root():
    """Health check."""
    return {
        "service": "Collider Pilot API",
        "status": "running",
        "observations": len(observations),
        "pending_commands": len(command_queue),
    }


@app.post("/observe", response_model=PilotResponse)
async def receive_observation(obs: GridObservation):
    """
    Receive an observation from ChatAgent.
    
    The Pilot will analyze this and may queue commands.
    """
    # Store observation
    observations.append(obs)
    append_jsonl(OBSERVATIONS_FILE, obs.model_dump())
    
    # Simple analysis (will be enhanced with Ollama later)
    analysis = {
        "node_count": len(obs.nodes),
        "edge_count": len(obs.edges),
        "container_count": len(obs.containers),
        "active": obs.active_container_id,
        "selected": obs.selected_node_ids,
    }
    
    # Generate response
    message = f"Received observation: {len(obs.nodes)} nodes, {len(obs.containers)} containers"
    
    # Check if any patterns to report
    commands = []
    if obs.user_action:
        message += f" | Action: {obs.user_action}"
    
    return PilotResponse(
        status="received",
        message=message,
        analysis=analysis,
        commands=commands,
    )


@app.get("/command")
async def get_pending_command():
    """
    Poll for pending commands from Pilot.
    
    ChatAgent calls this to get instructions.
    """
    if command_queue:
        cmd = command_queue.pop(0)
        append_jsonl(COMMANDS_FILE, cmd.model_dump())
        return {"has_command": True, "command": cmd}
    return {"has_command": False, "command": None}


@app.post("/command")
async def queue_command(cmd: PilotCommand):
    """
    Queue a command for ChatAgent.
    
    Used by Pilot or Gödel to send instructions.
    """
    command_queue.append(cmd)
    return {"queued": True, "queue_length": len(command_queue)}


@app.get("/observations")
async def list_observations(limit: int = 20):
    """Get recent observations."""
    return {
        "count": len(observations),
        "recent": [o.model_dump() for o in observations[-limit:]],
    }


@app.post("/report")
async def report_to_godel(report: GodelReport):
    """
    Send a report to Gödel for analysis.
    
    This is called by Pilot after accumulating patterns.
    """
    # For now, just log it
    report_path = DATA_DIR / "godel_reports.jsonl"
    append_jsonl(report_path, report.model_dump())
    
    return {
        "received": True,
        "message": f"Report for session {report.session_id} sent to Gödel",
        "patterns": len(report.patterns),
        "suggestions": len(report.suggestions),
    }


@app.delete("/reset")
async def reset_state():
    """Reset in-memory state (for testing)."""
    global observations, command_queue, chat_history
    observations = []
    command_queue = []
    chat_history = []
    return {"reset": True}


# --- Chat with Ollama ---

class ChatMessage(BaseModel):
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request."""
    message: str
    include_context: bool = True  # Include recent observations


chat_history: list[dict] = []

PILOT_SYSTEM_PROMPT = """You are the Collider Pilot, an AI assistant that helps manage the Tiny Data Collider.

You have access to:
- Grid observations (nodes, containers, edges from the frontend)
- Commands to send back to the ChatAgent

Your role:
1. Analyze the grid state when asked
2. Suggest improvements or patterns
3. Help the user understand their data
4. Report interesting findings to Gödel

Be concise and helpful. Reference specific nodes/containers by name when possible."""


@app.post("/chat")
async def chat_with_pilot(request: ChatRequest):
    """
    Chat with the Pilot using Ollama.
    """
    global chat_history
    
    # Build context from recent observations
    context = ""
    if request.include_context and observations:
        last_obs = observations[-1]
        context = f"\n\n[Current Grid State]\n"
        context += f"- Nodes: {len(last_obs.nodes)}\n"
        context += f"- Containers: {len(last_obs.containers)}\n"
        if last_obs.containers:
            container_names = [c.get("title", c.get("id", "?")) for c in last_obs.containers[:5]]
            context += f"- Recent containers: {', '.join(container_names)}\n"
    
    # Build messages
    messages = [{"role": "system", "content": PILOT_SYSTEM_PROMPT + context}]
    messages.extend(chat_history[-10:])  # Last 10 messages
    messages.append({"role": "user", "content": request.message})
    
    try:
        # Call Ollama
        response = ollama.chat(
            model="qwen3:14b",  # Use same model as Gödel
            messages=messages,
            options={"temperature": 0.7, "num_predict": 500},
        )
        
        assistant_message = response["message"]["content"]
        
        # Store in history
        chat_history.append({"role": "user", "content": request.message})
        chat_history.append({"role": "assistant", "content": assistant_message})
        
        # Log to file
        append_jsonl(CHAT_FILE, {
            "timestamp": datetime.now().isoformat(),
            "user": request.message,
            "assistant": assistant_message,
        })
        
        return {
            "response": assistant_message,
            "context_included": request.include_context,
            "history_length": len(chat_history),
        }
    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "context_included": False,
            "history_length": len(chat_history),
        }


@app.get("/chat/history")
async def get_chat_history(limit: int = 20):
    """Get chat history."""
    return {"messages": chat_history[-limit:]}


# --- Gödel Assessment ---

GODEL_SYSTEM_PROMPT = """You are Gödel, the architect of the Tiny Data Collider.

You are receiving assessment data from:
1. ChatAgent (frontend observer) - grid observations
2. Collider Pilot (local analyzer) - chat assessments
3. User notes

Your task:
1. Analyze the observations and assessments
2. Identify patterns, issues, and opportunities
3. Recommend changes to:
   - models/ (Pydantic schemas)
   - definitions/ (agent configurations)
   - runtimes/ (execution logic)

Focus on:
- Container building issues
- Composite definition mechanisms
- Graph topology correctness
- Field completeness in Pydantic models

Output structured recommendations in this format:

## Issues Found
- [issue description]

## Recommendations
### models/
- [file]: [change needed]

### definitions/
- [file]: [change needed]

### runtimes/
- [file]: [change needed]

Be specific and actionable."""


class AssessRequest(BaseModel):
    """Request for Gödel assessment."""
    user_notes: str = ""  # Additional notes from user
    include_observations: bool = True
    include_chat: bool = True
    observation_limit: int = 10
    chat_limit: int = 20


@app.post("/godel/assess")
async def godel_assess(request: AssessRequest):
    """
    Send all data to Gödel for architectural assessment.
    
    Reads observations, chat history, and user notes.
    Returns recommendations for models/definitions/runtimes.
    """
    # Build context from data files
    context_parts = []
    
    # Observations
    if request.include_observations:
        obs_data = read_jsonl(OBSERVATIONS_FILE, request.observation_limit)
        if obs_data:
            context_parts.append("## Grid Observations")
            for i, obs in enumerate(obs_data[-5:]):  # Last 5
                context_parts.append(f"\n### Observation {i+1}")
                context_parts.append(f"- Nodes: {len(obs.get('nodes', []))}")
                context_parts.append(f"- Containers: {len(obs.get('containers', []))}")
                context_parts.append(f"- Action: {obs.get('user_action', 'unknown')}")
                # Sample container data
                containers = obs.get('containers', [])[:3]
                for c in containers:
                    context_parts.append(f"  - {c.get('title', c.get('id', '?'))}")
    
    # Chat history
    if request.include_chat:
        chat_data = read_jsonl(CHAT_FILE, request.chat_limit)
        if chat_data:
            context_parts.append("\n## Pilot Chat History")
            for entry in chat_data[-10:]:  # Last 10 exchanges
                context_parts.append(f"\nUser: {entry.get('user', '')[:200]}")
                context_parts.append(f"Pilot: {entry.get('assistant', '')[:200]}")
    
    # User notes
    if request.user_notes:
        context_parts.append(f"\n## User Notes\n{request.user_notes}")
    
    if not context_parts:
        return {"error": "No data to assess. Collect observations first."}
    
    # Build prompt for Gödel
    context = "\n".join(context_parts)
    prompt = f"""Assess the following data and provide recommendations:

{context}

---

Provide your architectural recommendations:"""

    # Call Gödel via Ollama
    try:
        response = ollama.chat(
            model="qwen3:14b",
            messages=[
                {"role": "system", "content": GODEL_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.3, "num_predict": 1500},
        )
        
        assessment = response["message"]["content"]
        
        # Save assessment
        assessment_file = DATA_DIR / "godel_assessments.jsonl"
        append_jsonl(assessment_file, {
            "timestamp": datetime.now().isoformat(),
            "observations_count": len(obs_data) if request.include_observations else 0,
            "chat_count": len(chat_data) if request.include_chat else 0,
            "user_notes": request.user_notes,
            "assessment": assessment,
        })
        
        return {
            "status": "complete",
            "assessment": assessment,
            "data_summary": {
                "observations": len(obs_data) if request.include_observations else 0,
                "chat_entries": len(chat_data) if request.include_chat else 0,
                "has_user_notes": bool(request.user_notes),
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/godel/assessments")
async def list_assessments(limit: int = 10):
    """Get previous Gödel assessments."""
    assessment_file = DATA_DIR / "godel_assessments.jsonl"
    assessments = read_jsonl(assessment_file, limit)
    return {"count": len(assessments), "assessments": assessments}


# --- WebUI ---

@app.get("/ui")
async def serve_ui():
    """Serve the Pilot WebUI."""
    ui_path = STATIC_DIR / "index.html"
    if ui_path.exists():
        return FileResponse(ui_path)
    # Fallback: return simple HTML
    return FileResponse(STATIC_DIR / "index.html")


# --- Run ---

if __name__ == "__main__":
    import uvicorn
    # Create UI directory if needed
    STATIC_DIR.mkdir(exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8001)
