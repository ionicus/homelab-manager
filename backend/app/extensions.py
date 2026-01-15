"""Flask extensions - initialized separately to avoid circular imports."""

import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Use Redis for rate limiting storage (shared across workers, persists across restarts)
# Falls back to memory:// in development if Redis unavailable
RATE_LIMIT_STORAGE = os.getenv("RATE_LIMIT_STORAGE_URL") or os.getenv(
    "CELERY_BROKER_URL", "redis://localhost:6379/0"
)

# Initialize rate limiter (attached to app in create_app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=RATE_LIMIT_STORAGE,
)
