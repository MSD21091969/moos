---
description: Start the Factory pipeline with Frontend + Pilot + Gödel data collection
---

# Start Pipeline

Complete **ChatAgent → Gödel → Collider Pilot** pipeline for observation and architectural audit.

> **Purpose**: This self-contained pipeline enables visual Grid interaction, real-time observation streaming, and meta-agent assessment—without requiring the main Collider backend or FatRuntime server.

> **Use Case**: This dev tool runs locally in `dev-assistant` and `agent-factory` environments when working with code-assist in **Antigravity IDE**. The colored UX serves as a visual reference for pointing out architectural patterns during code review sessions.

## Prerequisites

- **Ollama**: Running with `qwen3:14b` and custom `godel` models
- **Node.js**: Installed (for legacy frontend)
- **Python**: With `uv` package manager

## Step 1: Start Pilot API (Port 8001)

// turbo

```powershell
cd D:\agent-factory
uv run python godel/pilot_api.py
```

**Provides:**

- **Pilot API**: `http://localhost:8001`
- **Web UI**: `http://localhost:8001/ui` (chat + observation viewer)
- **Gödel Assessment**: `POST /godel/assess` endpoint

**Model**: Uses `qwen3:14b` for chat and architectural reasoning.

**Verify Running:**

```powershell
curl http://localhost:8001/ui
```

---

## Step 2: Start Gödel CLI (Interactive Meta-Agent)

// turbo

```powershell
cd D:\agent-factory
uv run python cli.py spawn godel
```

**Provides:**

- Interactive terminal for definition evaluation
- Commands: `help`, `list defs`, `eval <file>`, `read self`, `quit`

**Non-interactive query mode:**

```powershell
uv run python cli.py spawn godel -q "What is your purpose?"
```

**Expected Output:**

```
🔮 Spawning Gödel - the meta-agent...
==================================================
Model: qwen3:14b
Tools: 9

Query: What is your purpose?
--------------------------------------------------

I am Gödel, the meta-agent of the Agent Factory...
```

**Model**: Uses the custom `godel` Ollama model (9.3 GB, embedded system prompt).

---

## Step 3: Start Legacy Frontend (Port 5173/5174)

// turbo

```powershell
cd C:\Users\hp\.gemini\antigravity\playground\legacy-collider\frontend
npm run dev:demo
```

**Provides:**

- **Frontend UI**: `http://localhost:5174` (or 5173, check terminal output)
- **ChatAgent Panel**: Visual grid + observation streaming
- **pilot-bridge.ts**: TypeScript client for sending observations to Pilot API

**Expected Output:**

```
VITE v5.4.21  ready in 1011 ms

➜  Local:   http://localhost:5174/
➜  Network: http://192.168.1.13:5174/
```

> **Note**: This frontend is for **dev visualization only**. It bypasses the main Collider backend and sends data directly to the Pilot API.

---

## Step 4a: Start Dev Assistant CLI (Interactive)

```powershell
cd D:\dev-assistant
uv run python -m src.cli
```

**Provides:**

- Interactive terminal for the Dev Assistant agent
- Commands: `/help`, `/context <dir>`, `/tools`, `exit`
- Natural language chat for coding tasks

**Example Usage:**

```
[dev-assistant]> tell me about the collider

THINK: The Collider is a distributed, peer-to-peer architecture...

[dev-assistant]> /context d:\my-tiny-data-collider

Context loaded: my-tiny-data-collider
```

**Model**: Uses `qwen3:14b` (configured in `.env`).

---

## Step 4b: (Optional) Start Dev Assistant Gradio UI

```powershell
cd D:\dev-assistant
uv run python -m src.web_ui
```

**Provides:**

- **Gradio Chat UI**: `http://localhost:7860`
- Interactive chat with the Dev Assistant agent
- Knowledge retrieval from `collider.md`, manifesto, and pilot behaviors

---

## Step 5: Verify Pipeline Connection

1. **Open Pilot Web UI**: `http://localhost:8001/ui`

   - Should show "Connected" status
   - Model: `qwen3:14b`
   - Observations counter starts at 0

2. **Open Legacy Frontend**: `http://localhost:5174`

   - Grid canvas displays with containers (colored nodes)
   - Factory Observer panel on the right
   - Status indicator shows green dot (connected)

3. **Trigger Observation**: Click "Observe" in Factory Observer panel

   - Observation count increments
   - Recent observations list populates (e.g., "30 nodes, 15 containers")

4. **Verify Data Flow**: Check Pilot WebUI observation count increases in sync

---

## Visual Reference

### Grid Visualization (Port 5174)

![Grid Overview](.agent/workflows/screenshots/grid_overview.png)

**Elements visible:**

- **Colored Containers**: Blue (Trip to Santorini), Red (Q4 Sales Analysis), Green (React App Build), Purple (AI Research Notes), Orange (Client Dashboard)
- **Factory Observer Panel**: Shows observation count, recent observations, and "Observe canvas" button
- **Status Indicator**: Green = connected to Pilot API

### Container Detail View

![Container Detail](.agent/workflows/screenshots/container_detail.png)

**Elements visible:**

- **Trip Planner** (purple container) with "Planning" tag
- **Flight Search** (orange/yellow container) with "Travel" tag
- **Booking API** (green container) with "api" tag
- **Alice (Owner)** user object with ACL member info
- **Context Menu**: Create Session, Grouping, Add Agent, Add Tool, Add Source, Add Document, Circular Layout

---

## Step 6: Collect & Audit Data

### Observation Flow:

1. **Interact with Grid** in the legacy frontend (add nodes, containers, links)
2. **ChatAgent** auto-sends grid snapshots to Pilot API via `POST /observe`
3. **Chat with Pilot** in Web UI to analyze patterns
4. **Request Gödel Assessment** when ready for architectural recommendations

### CLI Commands (Gödel Terminal):

```powershell
# List all available agent definitions
uv run python cli.py list

# Output:
## Available Definitions
- 'base.py'
- 'godel.py'

# Evaluate a specific definition
uv run python cli.py eval definitions/godel.py

# Single-query mode for quick questions
uv run python cli.py spawn godel -q "How many observations have been received?"
```

---

## Data Files

All collected data is stored in **`D:\agent-factory\data\`**:

| File                      | Content                                   | Verified Count (This Session) |
| ------------------------- | ----------------------------------------- | ----------------------------- |
| `observations.jsonl`      | Grid snapshots (nodes, edges, containers) | 13+ lines                     |
| `pilot_chat.jsonl`        | Pilot conversations with timestamps       | Active                        |
| `commands.jsonl`          | Commands queued by Pilot                  | Active                        |
| `godel_assessments.jsonl` | Architectural recommendations with scores | On-demand                     |

**Check observation count:**

```powershell
cd D:\agent-factory
(Get-Content data\observations.jsonl | Measure-Object -Line).Lines
```

---

## Architecture Notes

**What is NOT used:**

- ❌ Collider backend (`my-tiny-data-collider`, port 8000)
- ❌ FatRuntime server
- ❌ SSE endpoints from main stack

**Data Flow:**

```
Legacy Frontend (5174)
    ↓ POST /observe
Pilot API (8001)
    ↓ Logs to data/*.jsonl
Gödel CLI (terminal) + Gödel Assessment Endpoint
```

**Model Alignment:**

- **Pilot API** (`pilot_api.py`): `qwen3:14b`
- **Gödel CLI** (`spawn godel`): `godel` (custom model, 9.3 GB)
- **Dev Assistant** (`dev-assistant`): `qwen3:14b`

**Verified Ollama Models:**

```
NAME                       ID              SIZE      MODIFIED
godel:latest               c1fcd67034ae    9.3 GB    33 hours ago
qwen3:14b                  bdbd181c33f2    9.3 GB    47 hours ago
nomic-embed-text:latest    0a109f422b47    274 MB    5 days ago
```

---

## Quick Health Check

Run this in PowerShell to verify all services are listening:

```powershell
netstat -ano | findstr ":8001 :5173 :5174 :7860"
```

**Expected ports:**

- **8001**: Pilot API (FastAPI) ✅
- **5174**: Legacy frontend (Vite) ✅
- **7860**: Dev Assistant Gradio UI (optional) ✅

**Active Terminals (Verified Running):**

- `uv run python godel/pilot_api.py` (in `d:\agent-factory`)
- `uv run python cli.py spawn godel` (in `d:\agent-factory`)
- `npm run dev:demo` (in `C:\Users\hp\.gemini\antigravity\playground\legacy-collider\frontend`)
- `uv run python -m src.web_ui` (in `d:\dev-assistant`, optional)
- `uv run python -m src.cli` (in `d:\dev-assistant`, optional)

---

## Antigravity IDE Integration

**Purpose in IDE Workflow:**

This pipeline is designed for **visual code review sessions** in Antigravity IDE:

- Developer makes changes to Container/Definition models
- Launches pipeline to visualize impact on the Grid
- Uses colored UX to point out architectural patterns during discussion
- Gödel provides meta-analysis of proposed changes

**Not for production use** — this is a local dev tool for the `dev-assistant` and `agent-factory` environments.

---

## Troubleshooting

### Gödel CLI Hangs in Interactive Mode

**Symptom:** Prompt appears but no response  
**Fix:** Use single-query mode instead:

```powershell
uv run python cli.py spawn godel -q "Your question here"
```

### Frontend Not Connecting to Pilot API

**Check:**

1. Pilot API is running on port 8001
2. Factory Observer shows green dot (connected)
3. Browser console for CORS errors

### Observation Count Not Incrementing

**Check:**

1. Click "Observe canvas" button after grid changes
2. Verify `data\observations.jsonl` file is being written
3. Check Pilot API terminal for `POST /observe` requests
