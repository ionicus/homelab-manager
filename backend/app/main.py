"""Main application entry point."""

from app import create_app
from app.config import config
from app.database import init_db
import os

# Get configuration from environment
config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config[config_name])

if __name__ == "__main__":
    # Initialize database tables
    init_db()

    # Run the application
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config.get("DEBUG", False),
    )
