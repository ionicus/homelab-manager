# Homelab Management System

A comprehensive system for managing homelab infrastructure with inventory tracking, automated provisioning, and real-time monitoring capabilities.

## Features

- **Inventory Management**: Track all physical servers, VMs, containers, and network devices
- **Automated Provisioning**: Deploy and configure systems using Ansible playbooks
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

### Frontend
- **React.js** with Vite
- **React Router** for navigation
- **Axios** for API calls
- **TailwindCSS** for styling

### Infrastructure
- **Ansible** for automation
- **Docker** for containerization
- **PostgreSQL** for data persistence

## Prerequisites

- Python 3.14+
- Node.js 18+
- PostgreSQL 14+
- Docker & Docker Compose (optional)
- UV package manager

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
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

# Run the backend
python -m app.main
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
# From project root
cd docker
docker-compose up -d
```

## Project Structure

```
homelab-manager/
├── backend/              # Flask backend application
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   └── utils/       # Helper functions
│   ├── migrations/      # Alembic migrations
│   ├── tests/           # Backend tests
│   └── pyproject.toml   # Python dependencies
├── frontend/            # React frontend application
│   ├── src/
│   │   ├── components/  # Reusable components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API client
│   │   └── utils/       # Utilities
│   └── package.json     # Node dependencies
├── ansible/             # Ansible playbooks
│   ├── playbooks/       # Provisioning scripts
│   └── inventory/       # Inventory files
├── docker/              # Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── docs/                # Documentation
```

## API Documentation

The API documentation is available at `http://localhost:5000/api/docs` when running the backend.

### Key Endpoints

- `GET /api/devices` - List all devices
- `POST /api/devices` - Create new device
- `GET /api/devices/:id/metrics` - Get device metrics
- `POST /api/provision` - Trigger provisioning job

## Development

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

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/homelab
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
CORS_ORIGINS=http://localhost:5173
```

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:5000/api
```

## Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

## Roadmap

- [x] Phase 1: Foundation and basic CRUD
- [ ] Phase 2: Inventory Management
- [ ] Phase 3: Monitoring System
- [ ] Phase 4: Provisioning Integration
- [ ] Phase 5: Authentication and Deployment

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

Built with modern Python and JavaScript technologies for efficient homelab management.
