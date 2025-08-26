"""Pagination utilities for handling page and size parameters."""

from typing import Tuple


def clamp_pagination(page: int, size: int, max_size: int = 100) -> Tuple[int, int]:
    """Clamp page and size parameters to valid ranges.

    Args:
        page: Page number (1-based)
        size: Items per page
        max_size: Maximum allowed items per page

    Returns:
        Tuple of (clamped_page, clamped_size)
    """
    # Ensure page is at least 1
    clamped_page = max(1, page)

    # Ensure size is between 1 and max_size
    clamped_size = max(1, min(size, max_size))

    return clamped_page, clamped_size


def get_offset(page: int, size: int) -> int:
    """Calculate the offset for pagination.

    Args:
        page: Page number (1-based)
        size: Items per page

    Returns:
        Offset for SQL LIMIT/OFFSET
    """
    return (page - 1) * size
