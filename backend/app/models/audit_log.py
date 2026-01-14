"""Audit log model for tracking user actions."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON

from app.database import Base


class AuditLog(Base):
    """Audit log model for tracking security-relevant actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Who performed the action
    user_id = Column(Integer, nullable=True, index=True)  # None for unauthenticated
    username = Column(String(80), nullable=True)  # Denormalized for query convenience

    # What action was performed
    action = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type = Column(String(50), nullable=False, index=True)  # Device, Service, User, etc.
    resource_id = Column(Integer, nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)

    # Additional details
    details = Column(JSON, nullable=True)  # Flexible storage for action-specific data
    status = Column(String(20), default="success")  # success, failure, denied

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "details": self.details,
            "status": self.status,
        }

    def __repr__(self):
        """String representation."""
        return f"<AuditLog {self.action} {self.resource_type} by {self.username or 'anonymous'}>"
