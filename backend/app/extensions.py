"""Flask extensions - initialized separately to avoid circular imports."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize rate limiter (attached to app in create_app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
