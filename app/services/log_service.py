"""Log service for recording and retrieving audit events."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..db import get_connection


def log_action(user_id: int, role: str, action: str, details: Optional[str] = None) -> None:
    """Persist a log entry for a critical user action."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO logs (user_id, role, action, details)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, role, action, details),
        )


def list_logs(limit: int = 100, role: Optional[str] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return most recent logs, optionally filtered by role or user."""
    params = []
    clauses = []
    if role:
        clauses.append("role = ?")
        params.append(role)
    if user_id:
        clauses.append("user_id = ?")
        params.append(user_id)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT log_id, user_id, role, action, details, timestamp
        FROM logs
        {where}
        ORDER BY timestamp DESC
        LIMIT ?
    """
    params.append(limit)

    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

