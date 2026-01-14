"""Pagination utilities for list endpoints."""

from flask import request
from sqlalchemy.orm import Query


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def get_pagination_params() -> tuple[int, int]:
    """Get pagination parameters from request query string.

    Returns:
        Tuple of (page, per_page) with validated values
    """
    page = request.args.get("page", DEFAULT_PAGE, type=int)
    per_page = request.args.get("per_page", DEFAULT_PER_PAGE, type=int)

    # Ensure valid bounds
    page = max(1, page)
    per_page = max(1, min(per_page, MAX_PER_PAGE))

    return page, per_page


def paginate_query(query: Query, page: int, per_page: int) -> tuple[list, int]:
    """Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (items, total_count)
    """
    total = query.count()
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    return items, total


def paginated_response(items: list, total: int, page: int, per_page: int) -> dict:
    """Create a paginated response envelope.

    Args:
        items: List of items (already converted to dicts)
        total: Total count of items
        page: Current page number
        per_page: Items per page

    Returns:
        Dict with data, pagination metadata
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return {
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }
