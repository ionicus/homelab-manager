"""
Centralized error handling utilities for the API.

Provides consistent error responses, custom exceptions, and helper functions
for common error scenarios.
"""

import logging
from typing import Any

from flask import jsonify

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        payload: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        result = {"error": self.message}
        if self.payload:
            result.update(self.payload)
        return result


class ValidationError(APIError):
    """Exception for validation errors (400)."""

    def __init__(self, message: str, field: str | None = None):
        payload = {"field": field} if field else {}
        super().__init__(message, status_code=400, payload=payload)


class NotFoundError(APIError):
    """Exception for resource not found errors (404)."""

    def __init__(self, resource: str, identifier: Any | None = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, status_code=404)


class ConflictError(APIError):
    """Exception for resource conflict errors (409)."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class DatabaseError(APIError):
    """Exception for database operation errors (500)."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)


def error_response(
    message: str, status_code: int = 400, **kwargs
) -> tuple[dict[str, Any], int]:
    """
    Create a standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code
        **kwargs: Additional fields to include in response

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {"error": message}
    if kwargs:
        response.update(kwargs)

    # Log error if it's a server error
    if status_code >= 500:
        logger.error(f"Error {status_code}: {message}", extra=kwargs)

    return jsonify(response), status_code


def success_response(
    data: Any = None, message: str | None = None, status_code: int = 200
) -> tuple[dict[str, Any], int]:
    """
    Create a standardized success response.

    All responses are wrapped in a consistent envelope:
    - {"data": ...} for data responses
    - {"message": ...} for message-only responses
    - {"data": ..., "message": ...} for both

    Args:
        data: Response data (dict, list, or None)
        message: Optional success message
        status_code: HTTP status code

    Returns:
        Tuple of (response_dict, status_code)
    """
    response: dict[str, Any] = {}

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    return jsonify(response), status_code


def validation_error(
    message: str, field: str | None = None
) -> tuple[dict[str, Any], int]:
    """
    Create a validation error response (400).

    Args:
        message: Validation error message
        field: Optional field name that failed validation

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {"error": message}
    if field:
        response["field"] = field
    return jsonify(response), 400


def not_found_error(
    resource: str, identifier: Any | None = None
) -> tuple[dict[str, Any], int]:
    """
    Create a resource not found error response (404).

    Args:
        resource: Resource type (e.g., "Device", "Service")
        identifier: Optional resource identifier

    Returns:
        Tuple of (response_dict, status_code)
    """
    message = f"{resource} not found"
    if identifier:
        message += f": {identifier}"
    return jsonify({"error": message}), 404


def conflict_error(message: str) -> tuple[dict[str, Any], int]:
    """
    Create a resource conflict error response (409).

    Args:
        message: Conflict description

    Returns:
        Tuple of (response_dict, status_code)
    """
    return jsonify({"error": message}), 409


def database_error(
    message: str = "Database operation failed", log_details: str | None = None
) -> tuple[dict[str, Any], int]:
    """
    Create a database error response (500).

    Args:
        message: User-facing error message
        log_details: Additional details to log (not sent to user)

    Returns:
        Tuple of (response_dict, status_code)
    """
    if log_details:
        logger.error(f"Database error: {log_details}")
    else:
        logger.error(f"Database error: {message}")

    return jsonify({"error": message}), 500


def handle_database_exception(e: Exception) -> tuple[dict[str, Any], int]:
    """
    Handle SQLAlchemy database exceptions.

    Args:
        e: Database exception

    Returns:
        Tuple of (response_dict, status_code)
    """
    from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

    if isinstance(e, IntegrityError):
        # Extract constraint violation details if possible
        error_msg = str(e.orig) if hasattr(e, "orig") else str(e)

        # Check for common constraint violations
        if "unique constraint" in error_msg.lower():
            logger.warning(f"Unique constraint violation: {error_msg}")
            return conflict_error("Resource already exists with this value")
        elif "foreign key constraint" in error_msg.lower():
            logger.warning(f"Foreign key constraint violation: {error_msg}")
            return validation_error("Referenced resource does not exist")
        elif "not null constraint" in error_msg.lower():
            logger.warning(f"Not null constraint violation: {error_msg}")
            return validation_error("Required field is missing")
        else:
            logger.error(f"Integrity error: {error_msg}")
            return database_error("Data integrity constraint violated")

    elif isinstance(e, OperationalError):
        logger.error(f"Database operational error: {str(e)}")
        return database_error("Database connection or operation failed")

    elif isinstance(e, SQLAlchemyError):
        logger.error(f"SQLAlchemy error: {str(e)}")
        return database_error("Database operation failed")

    else:
        # Generic database error
        logger.error(f"Unexpected database error: {str(e)}")
        return database_error()


class DatabaseSession:
    """
    Context manager for database sessions with automatic error handling.

    Usage:
        with DatabaseSession() as db:
            # perform database operations
            device = db.query(Device).first()
            return success_response(device.to_dict())
    """

    def __init__(self):
        from app.database import Session

        self.Session = Session
        self.db = None

    def __enter__(self):
        """Open database session."""
        self.db = self.Session()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close database session and handle exceptions."""
        if exc_type is not None:
            # Rollback on exception
            if self.db:
                self.db.rollback()
                logger.warning(f"Database transaction rolled back due to: {exc_val}")

        # Always close the session
        if self.db:
            self.db.close()

        # Don't suppress the exception, let it propagate
        return False
