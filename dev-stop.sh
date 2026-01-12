#!/bin/bash

# Homelab Manager - Stop Development Servers
# This script stops any running backend and frontend development servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Homelab Manager development servers...${NC}\n"

# Stop backend (Flask on port 5000)
BACKEND_PIDS=$(lsof -ti:5000 2>/dev/null || true)
if [ ! -z "$BACKEND_PIDS" ]; then
    echo -e "Stopping backend processes: ${YELLOW}$BACKEND_PIDS${NC}"
    kill $BACKEND_PIDS 2>/dev/null || true
    sleep 1
    # Force kill if still running
    kill -9 $BACKEND_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Backend stopped${NC}"
else
    echo -e "${YELLOW}No backend processes found on port 5000${NC}"
fi

# Stop frontend (Vite on port 5173)
FRONTEND_PIDS=$(lsof -ti:5173 2>/dev/null || true)
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo -e "Stopping frontend processes: ${YELLOW}$FRONTEND_PIDS${NC}"
    kill $FRONTEND_PIDS 2>/dev/null || true
    sleep 1
    # Force kill if still running
    kill -9 $FRONTEND_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Frontend stopped${NC}"
else
    echo -e "${YELLOW}No frontend processes found on port 5173${NC}"
fi

# Stop any python app.main processes
PYTHON_PIDS=$(ps aux | grep "python.*app.main" | grep -v grep | awk '{print $2}' || true)
if [ ! -z "$PYTHON_PIDS" ]; then
    echo -e "Stopping Python backend processes: ${YELLOW}$PYTHON_PIDS${NC}"
    kill $PYTHON_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Python backend stopped${NC}"
fi

# Stop any npm dev processes
NPM_PIDS=$(ps aux | grep "npm run dev" | grep -v grep | awk '{print $2}' || true)
if [ ! -z "$NPM_PIDS" ]; then
    echo -e "Stopping npm dev processes: ${YELLOW}$NPM_PIDS${NC}"
    kill $NPM_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ npm dev stopped${NC}"
fi

# Stop any vite processes
VITE_PIDS=$(ps aux | grep "[v]ite --host" | awk '{print $2}' || true)
if [ ! -z "$VITE_PIDS" ]; then
    echo -e "Stopping Vite processes: ${YELLOW}$VITE_PIDS${NC}"
    kill $VITE_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Vite stopped${NC}"
fi

echo -e "\n${GREEN}All development servers stopped${NC}"
