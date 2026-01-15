#!/usr/bin/env python3
"""Celery worker entry point.

Usage:
    # Start worker with default settings
    celery -A worker.celery_app worker --loglevel=info

    # Start worker with concurrency (number of worker processes)
    celery -A worker.celery_app worker --loglevel=info --concurrency=4

    # Start worker with beat scheduler (for periodic tasks)
    celery -A worker.celery_app worker --loglevel=info --beat

    # Or run this script directly for development
    python worker.py
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

# Import tasks to register them
import app.tasks.automation  # noqa: E402, F401
from app.celery_app import celery_app  # noqa: E402

if __name__ == "__main__":
    # Run worker directly for development
    celery_app.start(argv=["celery", "worker", "--loglevel=info"])
