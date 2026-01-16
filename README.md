# Homelab Management System

A comprehensive system for managing homelab infrastructure with inventory tracking, automated provisioning, and real-time monitoring capabilities.

## Features

- **Inventory Management**: Track all physical servers, VMs, containers, and network devices
- **Network Interface Management**: Multi-homed device support with multiple NICs, MAC addresses, VLANs, and IP addresses
- **Automation**: Deploy and configure systems using Ansible playbooks
  - Multi-device execution for parallel deployments
  - Extra variables support with JSON Schema validation
  - Real-time log streaming via Server-Sent Events
  - Progress tracking and job cancellation
- **Workflow Orchestration**: Define multi-step automation sequences
  - Step dependencies and execution ordering
  - Automatic rollback on failure
  - Reusable workflow templates
- **Vault Secrets**: Secure storage for sensitive data (encrypted at rest with Fernet)
- **Real-time Monitoring**: Monitor CPU, memory, disk usage, and network traffic
- **Service Management**: Track and control running services across your infrastructure
- **Alert System**: Get notified when systems exceed defined thresholds
- **RESTful API**: Complete API for programmatic access
- **Web Dashboard**: Intuitive React-based web interface

## Technology Stack

### Backend
- **Python 3.14** with UV package manager
- **Flask** for RESTful API
- **SQLAlchemy** ORM
- **PostgreSQL** database
- **Alembic** for migrations
- **Celery** for background task processing
- **Redis** for task queue and caching
- **Pillow** for image processing

### Frontend
- **React.js** with Vite
- **React Router** for navigation
- **TanStack Query** for data fetching and caching
- **Axios** for API calls
- **Mantine UI** for components and theming

### Infrastructure
- **Ansible** for automation
- **Docker** for containerization
- **PostgreSQL** for data persistence
- **Redis** for task queue

## Prerequisites

- Python 3.14+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+ (for background tasks)
- Docker & Docker Compose (optional)
- UV package manager

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/ionicus/homelab-manager.git
cd homelab-manager
```

### 2. Backend Setup

```bash
cd backend

# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic upgrade head

# Create initial admin user
flask create-admin

# Start Redis (required for background tasks)
# Option 1: Using Docker
docker run -d -p 6379:6379 --name redis redis:alpine
# Option 2: System package (e.g., sudo apt install redis-server)

# Run the backend API server
python -m app.main

# In a separate terminal, start the Celery worker for background tasks
celery -A worker.celery_app worker --loglevel=info
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your backend API URL

# Run the development server
npm run dev
```

### 4. Using Docker (Alternative)

```bash
# Set up Docker environment variables
cd docker
cp .env.example .env
# Edit .env with your configuration (especially passwords!)

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Project Structure

```
homelab-manager/
├── backend/              # Flask backend application
│   ├── app/
│   │   ├── models/      # SQLAlchemy models (Device, NetworkInterface, Service, etc.)
│   │   ├── routes/      # API endpoints (devices, interfaces, services, metrics)
│   │   ├── services/    # Business logic
│   │   ├── tasks/       # Celery background tasks
│   │   ├── utils/       # Helper functions (validators, etc.)
│   │   ├── main.py      # Application entry point
│   │   ├── celery_app.py # Celery configuration
│   │   ├── config.py    # Configuration
│   │   └── database.py  # Database connection
│   ├── migrations/      # Alembic migrations
│   ├── automation/      # Automation resources
│   │   └── ansible/     # Ansible playbooks and config
│   ├── worker.py        # Celery worker entry point
│   ├── tests/           # Backend tests
│   └── pyproject.toml   # Python dependencies
├── frontend/            # React frontend application
│   ├── src/
│   │   ├── pages/       # Page components (Dashboard, DeviceDetail, Settings, etc.)
│   │   ├── components/  # Reusable components (StatusBadge, ServiceList, etc.)
│   │   ├── contexts/    # React contexts (ThemeContext)
│   │   ├── theme/       # Mantine theme configuration
│   │   ├── services/    # API client (api.js)
│   │   ├── utils/       # Utility functions (formatting, validation)
│   │   ├── App.jsx      # Main app component
│   │   ├── App.css      # Global styles
│   │   └── main.jsx     # Entry point
│   └── package.json     # Node dependencies
├── docker/              # Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── docs/                # Documentation
```

## API Documentation

📖 **[Complete API Documentation](docs/API.md)**

Comprehensive documentation covering all API endpoints, request/response formats, error handling, and examples.

###  Quick Reference

**Base URL**: `http://localhost:5000/api`

**Swagger UI**: `http://localhost:5000/apidocs/`

**Key Endpoints**:

- **Auth**: `POST /api/auth/login` - Authentication and JWT tokens
- **Devices**: `GET/POST/PUT/DELETE /api/devices` - Device management
- **Network Interfaces**: `/api/devices/{id}/interfaces` - Multi-homed network support
- **Services**: `/api/services` - Service tracking and monitoring
- **Metrics**: `/api/metrics` - Performance metrics collection
- **Automation**: `/api/automation` - Ansible job triggering (single/multi-device)
- **Vault Secrets**: `/api/automation/vault/secrets` - Encrypted secret storage
- **Workflows**: `/api/workflows` - Multi-step automation orchestration

**Error Handling**: All errors return JSON with proper HTTP status codes (400, 401, 403, 404, 409, 429, 500)

## Authentication

All API endpoints (except `/health` and `/api/auth/login`) require JWT authentication.

### Initial Setup

Create the first admin user using the CLI:

```bash
cd backend
source .venv/bin/activate
flask create-admin
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `flask create-admin` | Create an admin user (interactive prompts for username, email, password) |
| `flask list-users` | Display all users in the system |
| `flask reset-password` | Reset a user's password from the command line |

### Using the API

1. Login to get a JWT token:
   ```bash
   curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "your-password"}'
   ```

2. Include the token in subsequent requests:
   ```bash
   curl http://localhost:5000/api/devices \
     -H "Authorization: Bearer <your-token>"
   ```

## Development

### Developer Environment Setup

This project uses specific tools and paths that may vary by environment:

**Node.js Setup (nvm)**:
- Node.js is managed via nvm (Node Version Manager)
- Before running npm commands, load nvm: `source ~/.nvm/nvm.sh`
- Current version: Node v22.21.1, npm 10.9.4
- Vite binary location: `frontend/node_modules/.bin/vite`

**Backend Entry Point**:
- Main application: `backend/app/main.py`
- Start backend: `cd backend && source .venv/bin/activate && python -m app.main`
- Backend runs on: http://localhost:5000

**Frontend Entry Point**:
- Start frontend: `cd frontend && source ~/.nvm/nvm.sh && npm run dev`
- Frontend runs on: http://localhost:5173
- Vite dev server binds to 0.0.0.0 for network access

**Database**:
- PostgreSQL connection configured in `backend/.env` (DATABASE_URL)
- Migrations: `cd backend && source .venv/bin/activate && alembic upgrade head`
- See `backend/.env.example` for configuration template

### Quick Start Commands

**Using convenience scripts** (recommended):
```bash
# Start both backend and frontend
./dev.sh

# Stop all development servers
./dev-stop.sh
```

**Manual start** (if needed):
```bash
# Start Redis (if not running)
docker run -d -p 6379:6379 --name redis redis:alpine

# Start backend API
cd backend && source .venv/bin/activate && python -m app.main

# Start Celery worker (in new terminal)
cd backend && source .venv/bin/activate && celery -A worker.celery_app worker --loglevel=info

# Start frontend (in new terminal)
cd frontend && source ~/.nvm/nvm.sh && npm run dev

# Run database migration
cd backend && source .venv/bin/activate && alembic upgrade head
```

**Logs**:
- Backend logs: `/tmp/homelab-backend.log`
- Frontend logs: `/tmp/homelab-frontend.log`

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Configuration

All sensitive configuration (database credentials, API keys, host addresses) is managed through `.env` files that are **excluded from git** via `.gitignore`.

### Backend Environment Variables

Copy the example file and customize for your environment:

```bash
cd backend
cp .env.example .env
# Edit .env with your actual configuration
```

Key variables in `backend/.env`:
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
HOST=0.0.0.0
PORT=5000
CORS_ORIGINS=http://localhost:5173

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Frontend Environment Variables

Copy the example file and customize:

```bash
cd frontend
cp .env.example .env
# Edit .env with your backend API URL
```

Key variables in `frontend/.env`:
```env
VITE_API_URL=http://localhost:5000/api
```

**Important**: Never commit `.env` files to git. They contain environment-specific and sensitive information.

### Docker Environment Variables

For Docker Compose deployments, copy the example file:

```bash
cd docker
cp .env.example .env
# Edit .env with your configuration
```

Key variables in `docker/.env`:
```env
# PostgreSQL
POSTGRES_USER=homelab
POSTGRES_PASSWORD=secure-password-here
POSTGRES_DB=homelab_db
POSTGRES_PORT=5432

# Backend
FLASK_ENV=production
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-min-32-chars
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Security Note**: Always change default passwords in production!

## Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

## Roadmap

- [x] Phase 1: Foundation and basic CRUD
- [ ] Phase 2: Inventory Management
- [ ] Phase 3: Monitoring System
- [x] Phase 4: Automation Integration
  - [x] Extra variables and JSON Schema support
  - [x] Real-time log streaming and progress tracking
  - [x] Multi-device execution
  - [x] Vault secrets (encrypted at rest)
  - [x] Workflow orchestration with dependencies and rollback
- [x] Phase 5: Authentication and Deployment

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

Built with modern Python and JavaScript technologies for efficient homelab management.
