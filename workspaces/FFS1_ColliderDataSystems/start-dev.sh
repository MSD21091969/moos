#!/bin/bash
# Collider Development Environment Startup Script
# Runs: Backend API (8000), SQLite Viewer (8003), Frontend (4200)

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
BACKEND_DIR="$BASE_DIR/FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer"
FRONTEND_DIR="$BASE_DIR/FFS3_ColliderApplicationsFrontendServer"

# Check if directories exist
if [ ! -d "$BACKEND_DIR" ]; then
    echo "Error: Backend directory not found at $BACKEND_DIR"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Error: Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "${YELLOW}Shutting down services...${NC}"
    kill 0
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "${BLUE}[1/4] Installing backend dependencies...${NC}"
cd "$BACKEND_DIR"
uv sync

echo ""
echo "${BLUE}[2/4] Starting Backend API (port 8000)...${NC}"
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "${GREEN}✓ Backend API starting on http://localhost:8000${NC}"

echo ""
echo "${BLUE}[3/4] Starting SQLite Web Viewer (port 8003)...${NC}"
uv run sqlite_web "$BACKEND_DIR/collider.db" --host 0.0.0.0 --port 8003 &
SQLITE_PID=$!

echo "${GREEN}✓ SQLite Viewer starting on http://localhost:8003${NC}"

echo ""
echo "${BLUE}[4/4] Starting Frontend (port 4200)...${NC}"
cd "$FRONTEND_DIR"
pnpm nx serve ffs6 &
FRONTEND_PID=$!

echo "${GREEN}✓ Frontend starting on http://localhost:4200${NC}"

echo ""
echo "============================================"
echo "${GREEN}  All services running!${NC}"
echo "============================================"
echo ""
echo "  Backend API:       http://localhost:8000"
echo "  Database Viewer:   http://localhost:8003"
echo "  Frontend App:      http://localhost:4200"
echo ""
echo "  API Docs:          http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for all processes
wait
