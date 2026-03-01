#!/bin/bash
# Collider Development Environment Startup Script
# Runs: DataServer (8000), AgentRunner (8004), NanoClawBridge (18789), Frontend (4200)

set -e

echo "============================================"
echo "  Collider Development Environment"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base paths
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FFS2_DIR="$BASE_DIR/FFS2_ColliderBackends_MultiAgentChromeExtension"
DATA_SERVER_DIR="$FFS2_DIR/ColliderDataServer"
AGENT_RUNNER_DIR="$FFS2_DIR/ColliderAgentRunner"
NANOCLAW_DIR="$FFS2_DIR/NanoClawBridge"
FRONTEND_DIR="$BASE_DIR/FFS3_ColliderApplicationsFrontendServer"

# Check if directories exist
for dir in "$DATA_SERVER_DIR" "$AGENT_RUNNER_DIR" "$NANOCLAW_DIR" "$FRONTEND_DIR"; do
    if [ ! -d "$dir" ]; then
        echo "Error: Directory not found at $dir"
        exit 1
    fi
done

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "${YELLOW}Shutting down services...${NC}"
    kill 0
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "${BLUE}[1/5] Starting Data Server (port 8000)...${NC}"
cd "$DATA_SERVER_DIR"
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 &

echo "${BLUE}[2/5] Starting Agent Runner (port 8004)...${NC}"
cd "$AGENT_RUNNER_DIR"
uv run uvicorn src.main:app --host 0.0.0.0 --port 8004 &

echo "${BLUE}[3/5] Starting NanoClaw Bridge (port 18789)...${NC}"
cd "$NANOCLAW_DIR"
pnpm run dev &

echo "${BLUE}[4/5] Starting SQLite Viewer (port 8003)...${NC}"
cd "$DATA_SERVER_DIR"
uv run sqlite_web collider.db --host 0.0.0.0 --port 8003 &

echo "${BLUE}[5/5] Starting Frontend (port 4200)...${NC}"
cd "$FRONTEND_DIR"
pnpm nx serve ffs6 &

echo ""
echo "============================================"
echo "${GREEN}  NanoClaw SDK + gRPC Stack Active!${NC}"
echo "============================================"
echo ""
echo "  Data Server:       http://localhost:8000"
echo "  Agent Runner:      http://localhost:8004"
echo "  NanoClaw Bridge:   http://localhost:18789"
echo "  Frontend App:      http://localhost:4200"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for all processes
wait
