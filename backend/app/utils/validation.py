"""Request validation utilities using Pydantic schemas."""

import logging
from functools import wraps
from typing import Any, Callable, Type

from flask import request
from pydantic import BaseModel, ValidationError

from app.utils.errors import APIError, error_response

logger = logging.getLogger(__name__)


def validate_request(schema: Type[BaseModel]):
    """
    Decorator to validate request JSON against a Pydantic schema.

    Usage:
        @validate_request(DeviceCreate)
        def create_device():
            # request.validated_data contains validated Pydantic model
            data = request.validated_data
            ...

    Args:
        schema: Pydantic schema class to validate against

    Returns:
        Decorated function that validates request data
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get JSON data from request
            json_data = request.get_json()

            if json_data is None:
                return error_response("Missing JSON request body", 400)

            try:
                # Validate using Pydantic schema
                validated_data = schema(**json_data)

                # Store validated data in request context
                request.validated_data = validated_data

                # Call the original function
                return f(*args, **kwargs)

            except ValidationError as e:
                # Format validation errors for user-friendly response
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    message = error["msg"]
                    errors.append({"field": field, "message": message})

                return error_response("Validation failed", 400, details=errors)

            except APIError:
                # Let our custom API errors propagate to Flask's error handler
                raise

            except Exception:
                # Log full exception for debugging, return generic message to client
                logger.exception("Unexpected error during request validation")
                return error_response("Invalid request data", 400)

        return wrapper

    return decorator


def validate_data(schema: Type[BaseModel], data: dict) -> tuple[Any, dict | None]:
    """
    Validate data against a Pydantic schema.

    Args:
        schema: Pydantic schema class
        data: Dictionary to validate

    Returns:
        Tuple of (validated_data, error_dict)
        If validation succeeds: (validated_model, None)
        If validation fails: (None, error_dict)
    """
    try:
        validated = schema(**data)
        return validated, None
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            errors.append({"field": field, "message": message})

        return None, {"error": "Validation failed", "details": errors}
    except Exception:
        # Log full exception for debugging, return generic message
        logger.exception("Unexpected error during data validation")
        return None, {"error": "Invalid request data"}
