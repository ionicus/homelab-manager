# Homelab Manager - Quick Start Guide

This guide will help you get the Homelab Manager up and running quickly.

## Prerequisites

- Python 3.14+
- Node.js 18+
- PostgreSQL 14+
- UV package manager
- Git

## Option 1: Local Development Setup

### Step 1: Clone and Setup Backend

```bash
cd backend

# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Set up environment
cp .env.example .env
# Edit .env and update DATABASE_URL and SECRET_KEY
```

### Step 2: Setup Database

```bash
# Create PostgreSQL database
createdb homelab_db

# Or using psql
psql -U postgres
CREATE DATABASE homelab_db;
CREATE USER homelab WITH PASSWORD 'homelab';
GRANT ALL PRIVILEGES ON DATABASE homelab_db TO homelab;
\q

# Initialize database with Alembic
alembic upgrade head
```

### Step 3: Start Backend

```bash
# From backend directory
python -m app.main

# Backend will be available at http://localhost:5000
```

### Step 4: Setup Frontend

```bash
# Open a new terminal
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env if needed (default should work)

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

## Option 2: Docker Setup

### Quick Start with Docker

```bash
# From project root
cd docker

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- PostgreSQL: localhost:5432

### Docker Commands

```bash
# Rebuild containers
docker-compose up -d --build

# View backend logs
docker-compose logs -f backend

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U homelab homelab_db

# Stop and remove all data
docker-compose down -v
```

## Testing the Installation

### Test Backend API

```bash
# Health check
curl http://localhost:5000/health

# Get devices (should return empty array initially)
curl http://localhost:5000/api/devices

# Create a test device
curl -X POST http://localhost:5000/api/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-server",
    "type": "server",
    "status": "active",
    "ip_address": "192.168.1.100"
  }'
```

### Test Frontend

1. Open http://localhost:5173 in your browser
2. You should see the Dashboard
3. Click "Devices" to view the device list
4. Try adding a device through the UI

## Next Steps

1. **Configure Environment Variables**: Update `.env` files with your settings
2. **Add Devices**: Start adding your homelab devices
3. **Setup Ansible**: Configure Ansible playbooks for automation
4. **Configure Monitoring**: Set up metrics collection agents
5. **Customize UI**: Modify the frontend to match your preferences

## Common Issues

### Database Connection Error
- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env`
- Verify database credentials

### Frontend Can't Connect to Backend
- Ensure backend is running on port 5000
- Check CORS_ORIGINS in backend `.env`
- Verify VITE_API_URL in frontend `.env`

### UV Installation Issues
```bash
# Alternative UV installation
pip install uv
```

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000  # Unix/Mac
netstat -ano | findstr :5000  # Windows

# Kill the process or change port in config
```

## Development Workflow

1. Make changes to backend code
2. Backend auto-reloads (Flask debug mode)
3. Make changes to frontend code
4. Vite hot-reloads automatically
5. Test changes
6. Commit and push

## Production Deployment

For production deployment, refer to `docs/DEPLOYMENT.md` (to be created).

## Getting Help

- Check the main README.md for detailed information
- Review the project documentation in `docs/`
- Open an issue on GitHub for bugs or questions

Happy homelabbing! 🚀
