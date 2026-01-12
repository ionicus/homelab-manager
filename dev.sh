#!/bin/bash

# Homelab Manager Development Server Startup Script
# This script starts both the backend (Flask) and frontend (Vite) development servers

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Homelab Manager - Development Server${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down development servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}Cleanup complete${NC}"
    exit 0
}

# Trap Ctrl+C and other termination signals
trap cleanup SIGINT SIGTERM

# Check for nvm
if [ ! -f "$HOME/.nvm/nvm.sh" ]; then
    echo -e "${RED}Error: nvm not found at $HOME/.nvm/nvm.sh${NC}"
    echo "Please install nvm or update the path in this script"
    exit 1
fi

# Load nvm
echo -e "${YELLOW}Loading nvm...${NC}"
source "$HOME/.nvm/nvm.sh"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js not found${NC}"
    echo "Please install Node.js using: nvm install 22"
    exit 1
fi

echo -e "${GREEN}✓ Node.js $(node --version) | npm $(npm --version)${NC}\n"

# Check Python virtual environment
if [ ! -d "$SCRIPT_DIR/backend/.venv" ]; then
    echo -e "${RED}Error: Python virtual environment not found${NC}"
    echo "Please run: cd backend && uv venv && uv pip install -e ."
    exit 1
fi

# Start Backend
echo -e "${YELLOW}Starting Flask backend...${NC}"
cd "$SCRIPT_DIR/backend"
source .venv/bin/activate

# Start backend in background
python -m app.main > /tmp/homelab-backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Backend failed to start${NC}"
    echo "Check logs at: /tmp/homelab-backend.log"
    tail -20 /tmp/homelab-backend.log
    exit 1
fi

# Check if backend is responding
if ! curl -s http://localhost:5000/api/devices > /dev/null 2>&1; then
    echo -e "${RED}Warning: Backend started but not responding yet${NC}"
    echo "Check logs at: /tmp/homelab-backend.log"
else
    echo -e "${GREEN}✓ Backend running at http://localhost:5000${NC}"
fi

# Start Frontend
echo -e "\n${YELLOW}Starting Vite frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

# Start frontend in background
npm run dev > /tmp/homelab-frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Frontend failed to start${NC}"
    echo "Check logs at: /tmp/homelab-frontend.log"
    tail -20 /tmp/homelab-frontend.log
    cleanup
    exit 1
fi

echo -e "${GREEN}✓ Frontend running at http://localhost:5173${NC}"

# Display startup summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Development servers are running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Backend:  ${GREEN}http://localhost:5000${NC}"
echo -e "Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "\nBackend logs:  ${YELLOW}/tmp/homelab-backend.log${NC}"
echo -e "Frontend logs: ${YELLOW}/tmp/homelab-frontend.log${NC}"
echo -e "\nPress ${RED}Ctrl+C${NC} to stop both servers\n"

# Keep script running and tail frontend logs
tail -f /tmp/homelab-frontend.log
