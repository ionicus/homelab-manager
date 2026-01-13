# Contributing to Homelab Manager

Thank you for your interest in contributing! This guide will help you get started.

## Ways to Contribute

- **Report bugs** - Open an issue using the bug report template
- **Suggest features** - Open an issue using the feature request template
- **Submit code** - Fix bugs, add features, improve documentation
- **Improve docs** - Fix typos, clarify instructions, add examples

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (or SQLite for development)

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Configure your environment
flask run
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Submitting Changes

### Workflow

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch** for your changes: `git checkout -b feature/your-feature`
4. **Make changes** and commit with clear messages
5. **Push** to your fork: `git push origin feature/your-feature`
6. **Open a Pull Request** against the `main` branch

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes

## Code Style

### Python (Backend)

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes

### JavaScript/React (Frontend)

- Use functional components with hooks
- Follow existing patterns in the codebase
- Use Mantine components where applicable

## Commit Standards

### Authorship

- All commits must be authored by human contributors only
- Do not include AI co-author tags in commit messages
- Use your real name and email in git config

### Commit Messages

- Use clear, descriptive messages
- Start with a verb: "Add", "Fix", "Update", "Remove"
- Reference issues when applicable: "Fix #123"

### Testing

- All test data must be prefixed with `TEST_`
- Use `backend/scripts/manage_test_data.py` to manage test data
- Run tests before committing

### Security

- Never commit credentials or secrets
- All sensitive configuration in `.env` files (gitignored)
- Review changes for sensitive data before pushing

## Git Configuration

Set your identity:

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] No sensitive data in commits
- [ ] Documentation updated if needed
- [ ] Commit messages are clear and descriptive

## Questions?

Open an issue or contact the maintainer.
