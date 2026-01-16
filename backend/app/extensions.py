"""Flask extensions - initialized separately to avoid circular imports."""

import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Use Redis for rate limiting storage (shared across workers, persists across restarts)
# Falls back to memory:// in development if Redis unavailable
RATE_LIMIT_STORAGE = os.getenv("RATE_LIMIT_STORAGE_URL") or os.getenv(
    "CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"
)

# Use higher limits in development
IS_DEVELOPMENT = os.getenv("FLASK_ENV") == "development"
DEFAULT_LIMITS = ["10000 per day", "5000 per hour"] if IS_DEVELOPMENT else ["200 per day", "50 per hour"]

# Initialize rate limiter (attached to app in create_app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=DEFAULT_LIMITS,
    storage_uri=RATE_LIMIT_STORAGE,
)
