# Project Instructions for Claude

## Git Commit Preferences
- NEVER add "Co-Authored-By: Claude" lines to commit messages
- All commits should be authored solely by the human developer
- Keep commit messages professional and concise

## Testing Standards
- ALL test data must be prefixed with `TEST_`
- Use `backend/scripts/manage_test_data.py` to manage test data
- Never commit actual production data

## Security Requirements
- No credentials in committed files
- All secrets in `.env` (gitignored)
- Database URLs from environment variables only
- Review for sensitive data before every commit
