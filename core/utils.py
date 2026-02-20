"""Shared utilities for Study Pal."""

from __future__ import annotations

from datetime import datetime


def current_timestamp() -> str:
    """Return an ISO8601 timestamp for logging."""
    return datetime.utcnow().isoformat()
