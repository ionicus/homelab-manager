"""Audit logging utility for tracking security-relevant actions."""

import logging
from collections.abc import Callable
from functools import wraps

from flask import request

from app.models import AuditLog, User
from app.utils.errors import DatabaseSession

logger = logging.getLogger(__name__)


def get_current_user_id() -> int | None:
    """Get the current user ID from JWT, if authenticated."""
    try:
        from flask_jwt_extended import get_jwt_identity

        return get_jwt_identity()
    except Exception:
        return None


def get_current_username(db) -> str | None:
    """Get the current username from the database."""
    user_id = get_current_user_id()
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        return user.username if user else None
    return None


def audit_log(
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    details: dict | None = None,
    status: str = "success",
) -> None:
    """
    Log an auditable action to the database.

    Args:
        action: The action performed (CREATE, UPDATE, DELETE, LOGIN, etc.)
        resource_type: The type of resource affected (Device, Service, User, etc.)
        resource_id: Optional ID of the affected resource
        details: Optional dictionary with additional context
        status: The outcome of the action (success, failure, denied)
    """
    try:
        with DatabaseSession() as db:
            user_id = get_current_user_id()
            username = get_current_username(db) if user_id else None

            log_entry = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get("User-Agent", "")[:500] if request else None,
                details=details,
                status=status,
            )

            db.add(log_entry)
            db.commit()

            logger.info(
                f"Audit: {action} {resource_type}"
                f"{f' #{resource_id}' if resource_id else ''}"
                f" by {username or 'anonymous'}"
                f" from {log_entry.ip_address}"
                f" [{status}]"
            )
    except Exception as e:
        # Don't let audit logging failures break the application
        logger.error(f"Failed to write audit log: {e}")


def audit_action(
    action: str,
    resource_type: str,
    get_resource_id: Callable | None = None,
    get_details: Callable | None = None,
):
    """
    Decorator to automatically audit an action.

    Args:
        action: The action being performed
        resource_type: The type of resource being affected
        get_resource_id: Optional function to extract resource ID from response
        get_details: Optional function to extract additional details

    Example:
        @audit_action("CREATE", "Device", get_resource_id=lambda r: r.get("id"))
        def create_device():
            ...
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                result = f(*args, **kwargs)

                # Extract resource ID if function provided
                resource_id = None
                if get_resource_id and result:
                    try:
                        # Handle Flask response tuples
                        response_data = result[0].get_json() if hasattr(result[0], "get_json") else result
                        resource_id = get_resource_id(response_data)
                    except Exception:
                        pass

                # Extract details if function provided
                details = None
                if get_details:
                    try:
                        details = get_details(request, result)
                    except Exception:
                        pass

                # Log successful action
                audit_log(action, resource_type, resource_id, details, "success")

                return result
            except Exception as e:
                # Log failed action
                audit_log(
                    action,
                    resource_type,
                    kwargs.get("device_id") or kwargs.get("service_id") or kwargs.get("user_id"),
                    {"error": str(e)},
                    "failure",
                )
                raise

        return wrapper

    return decorator


# Convenience functions for common audit actions
def log_login_success(user_id: int, username: str) -> None:
    """Log a successful login."""
    audit_log("LOGIN", "User", user_id, {"username": username}, "success")


def log_login_failure(username: str, reason: str = "invalid_credentials") -> None:
    """Log a failed login attempt."""
    audit_log("LOGIN", "User", None, {"username": username, "reason": reason}, "failure")


def log_logout(user_id: int, username: str) -> None:
    """Log a logout."""
    audit_log("LOGOUT", "User", user_id, {"username": username}, "success")


def log_access_denied(resource_type: str, resource_id: int | None = None) -> None:
    """Log an access denied event."""
    audit_log("ACCESS", resource_type, resource_id, None, "denied")
