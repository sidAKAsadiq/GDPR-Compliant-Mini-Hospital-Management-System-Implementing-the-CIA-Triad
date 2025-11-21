"""Database utilities: connection helpers, schema creation, seed data."""
from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Tuple

try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    # dotenv optional; ignore if not installed
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "hospital.db"
DB_PATH = Path(os.getenv("DB_PATH", DEFAULT_DB_PATH))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)


@contextmanager
def get_connection():
    """Context manager yielding sqlite3 connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_tables() -> None:
    """Create users, patients, logs tables if they do not exist."""
    users_sql = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'doctor', 'receptionist')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    patients_sql = """
    CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT NOT NULL,
        diagnosis TEXT NOT NULL,
        anonymized_name TEXT NOT NULL,
        anonymized_contact TEXT NOT NULL,
        diagnosis_masked TEXT NOT NULL,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    logs_sql = """
    CREATE TABLE IF NOT EXISTS logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT
    );
    """

    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name);",
        "CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);",
    ]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(users_sql)
        cursor.execute(patients_sql)
        cursor.execute(logs_sql)
        for stmt in indexes_sql:
            cursor.execute(stmt)


def _hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def seed_users() -> None:
    """Insert default Admin/Doctor/Receptionist accounts."""
    default_users: Iterable[Tuple[str, str, str]] = [
        (
            os.getenv("DEFAULT_ADMIN_USERNAME", "admin"),
            os.getenv("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!"),
            "admin",
        ),
        ("doctor", os.getenv("DEFAULT_DOCTOR_PASSWORD", "DoctorPass123!"), "doctor"),
        (
            "reception",
            os.getenv("DEFAULT_RECEPTION_PASSWORD", "ReceptionPass123!"),
            "receptionist",
        ),
    ]

    with get_connection() as conn:
        cursor = conn.cursor()
        for username, password, role in default_users:
            cursor.execute(
                """
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET role=excluded.role
                """,
                (username.lower(), _hash_password(password), role),
            )


def initialize_database() -> None:
    create_tables()
    seed_users()


def get_db_path() -> Path:
    return DB_PATH


def read_database_bytes() -> bytes:
    return DB_PATH.read_bytes()


def health_check() -> bool:
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as exc:  # pragma: no cover - diagnostic helper
        logger.exception("Database health check failed: %s", exc)
        return False


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at {DB_PATH}")

