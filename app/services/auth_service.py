"""Authentication helpers: hashing, lookup, and session utilities."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any, Dict, Optional

FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from ..db import get_connection  # type: ignore
except ImportError:
    from db import get_connection

try:
    from .log_service import log_action  # type: ignore
except ImportError:
    from log_service import log_action


def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def verify_password(raw_password: str, hashed_password: str) -> bool:
    return hash_password(raw_password) == hashed_password


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT user_id, username, password, role FROM users WHERE username = ?",
            (username.lower(),),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT user_id, username, role FROM users WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Validate credentials and log the login attempt."""
    user = get_user_by_username(username)
    if not user:
        return None

    if verify_password(password, user["password"]):
        log_action(user_id=user["user_id"], role=user["role"], action="login", details="Successful login")
        return {k: user[k] for k in ("user_id", "username", "role")}

    log_action(user_id=user["user_id"], role=user["role"], action="login_failed", details="Invalid password")
    return None


# Simple dict-based session helpers (Streamlit's st.session_state is dict-like)
def set_session_user(state: Dict[str, Any], user: Dict[str, Any]) -> None:
    state["current_user"] = user


def get_session_user(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return state.get("current_user")


def logout_user(state: Dict[str, Any]) -> None:
    user = state.pop("current_user", None)
    if user:
        log_action(user_id=user["user_id"], role=user["role"], action="logout", details="User logged out")

