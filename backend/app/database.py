"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from app.config import Config

# Create engine
engine = create_engine(Config.DATABASE_URL, echo=Config.SQLALCHEMY_ECHO)

# Create session factory
# expire_on_commit=False prevents attributes from being expired after commit,
# which avoids "detached instance" errors when accessing attributes after commit
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
Session = scoped_session(session_factory)

# Create base class for models
Base = declarative_base()


def init_db():
    """Initialize the database."""
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
