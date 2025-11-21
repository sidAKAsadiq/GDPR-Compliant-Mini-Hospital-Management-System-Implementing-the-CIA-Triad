"""Patient data service: CRUD plus masking/anonymization utilities."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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

try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover - optional dependency
    Fernet = None

FERNET_KEY = os.getenv("FERNET_KEY")
FERNET = None
if FERNET_KEY and Fernet:
    try:
        FERNET = Fernet(FERNET_KEY)
    except ValueError:
        # Invalid key provided; fall back to plain-text storage
        FERNET = None


def mask_name(name: str) -> str:
    suffix = abs(hash(name)) % 10000
    return f"ANON_{suffix:04d}"


def mask_contact(contact: str) -> str:
    digits = [c for c in contact if c.isdigit()]
    last_four = "".join(digits[-4:]) or "0000"
    return f"XXX-XXX-{last_four}"


def mask_diagnosis(diagnosis: str) -> str:
    return f"MASKED_{abs(hash(diagnosis)) % 1_000_000:06d}"


def encrypt_sensitive(value: str) -> str:
    if FERNET:
        return FERNET.encrypt(value.encode("utf-8")).decode("utf-8")
    return value


def decrypt_sensitive(value: str) -> str:
    if FERNET:
        return FERNET.decrypt(value.encode("utf-8")).decode("utf-8")
    return value


def _format_patient_row(row) -> Dict[str, Any]:
    record = dict(row)
    record["diagnosis"] = decrypt_sensitive(record["diagnosis"])
    return record


def list_patients(view: str = "raw") -> List[Dict[str, Any]]:
    sql = """
        SELECT patient_id, name, contact, diagnosis,
               anonymized_name, anonymized_contact, diagnosis_masked,
               date_added, last_updated
        FROM patients
        ORDER BY date_added DESC
    """
    with get_connection() as conn:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()

    records = [_format_patient_row(row) for row in rows]
    if view == "anonymized":
        return [
            {
                "patient_id": r["patient_id"],
                "anonymized_name": r["anonymized_name"],
                "anonymized_contact": r["anonymized_contact"],
                "diagnosis_masked": r["diagnosis_masked"],
                "date_added": r["date_added"],
            }
            for r in records
        ]
    return records


def get_patient(patient_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
        )
        row = cursor.fetchone()
        return _format_patient_row(row) if row else None


def _anonymized_fields(name: str, contact: str, diagnosis: str) -> Dict[str, str]:
    return {
        "anonymized_name": mask_name(name),
        "anonymized_contact": mask_contact(contact),
        "diagnosis_masked": mask_diagnosis(diagnosis),
    }


def create_patient(
    *, name: str, contact: str, diagnosis: str, acted_by: Dict[str, Any]
) -> int:
    fields = _anonymized_fields(name, contact, diagnosis)
    encrypted_diagnosis = encrypt_sensitive(diagnosis)
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO patients (name, contact, diagnosis,
                                  anonymized_name, anonymized_contact, diagnosis_masked)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                contact,
                encrypted_diagnosis,
                fields["anonymized_name"],
                fields["anonymized_contact"],
                fields["diagnosis_masked"],
            ),
        )
        patient_id = cursor.lastrowid

    log_action(
        user_id=acted_by["user_id"],
        role=acted_by["role"],
        action="create_patient",
        details=f"patient_id={patient_id}",
    )
    return patient_id


def update_patient(
    patient_id: int, *, name: str, contact: str, diagnosis: str, acted_by: Dict[str, Any]
) -> None:
    fields = _anonymized_fields(name, contact, diagnosis)
    encrypted_diagnosis = encrypt_sensitive(diagnosis)
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE patients
            SET name = ?, contact = ?, diagnosis = ?,
                anonymized_name = ?, anonymized_contact = ?, diagnosis_masked = ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE patient_id = ?
            """,
            (
                name,
                contact,
                encrypted_diagnosis,
                fields["anonymized_name"],
                fields["anonymized_contact"],
                fields["diagnosis_masked"],
                patient_id,
            ),
        )

    log_action(
        user_id=acted_by["user_id"],
        role=acted_by["role"],
        action="update_patient",
        details=f"patient_id={patient_id}",
    )


def delete_patient(patient_id: int, *, acted_by: Dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))

    log_action(
        user_id=acted_by["user_id"],
        role=acted_by["role"],
        action="delete_patient",
        details=f"patient_id={patient_id}",
    )

