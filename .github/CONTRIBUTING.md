# Contributing to Homelab Manager

## Commit Standards

### Authorship
- All commits must be authored by human contributors only
- Do not include AI co-author tags in commit messages
- Use your real name and email in git config

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

## Before Committing

1. Run security check: Review all changes for sensitive data
2. Run tests: Ensure all tests pass
3. Update documentation: Keep docs in sync with code
4. Use conventional commits: Clear, descriptive messages

## Questions?

Open an issue or contact the maintainer.
