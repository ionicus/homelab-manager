"""Application settings model for storing configurable settings."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class AppSetting(Base):
    """Store application-wide settings as key-value pairs.

    Settings can be updated by admin users through the API.
    Common settings include session timeout, rate limits, etc.
    """

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, nullable=True)  # User ID who last updated

    # Default values for settings (class-level constants)
    DEFAULTS = {
        "session_timeout_minutes": ("60", "Session timeout in minutes (default: 60)"),
        "max_login_attempts": ("5", "Maximum failed login attempts before lockout"),
        "lockout_duration_minutes": (
            "15",
            "Account lockout duration in minutes after max failed attempts",
        ),
    }

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_default(cls, key: str) -> str | None:
        """Get default value for a setting key."""
        if key in cls.DEFAULTS:
            return cls.DEFAULTS[key][0]
        return None

    def __repr__(self):
        """String representation."""
        return f"<AppSetting {self.key}={self.value}>"
