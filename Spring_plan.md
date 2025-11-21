# Sprint Plan — GDPR-Aware Hospital Dashboard

## Phase 1: Environment & Dependencies

1. install-env — Install Python 3.11+, pip, Streamlit, sqlite3/MySQL connector, cryptography/hashlib libraries.
2. init-repo — Initialize repo structure (`app/`, `data/`, `docs/`), add `.env.example`, `.gitignore`.

## Phase 2: Database & Models

1. design-schema — Define SQL schema for `users`, `patients`, `logs`; include RBAC constraints.
2. migrate-db — Create migration/init script to build local SQLite DB with seed admin/doctor/receptionist users.

## Phase 3: Core Services

1. auth-service — Implement authentication + password hashing, role lookup, session storage helpers.
2. patient-service — CRUD helpers for patients plus masking/anonymization utilities (hashlib / Fernet).
3. log-service — Logging helper that records {user_id, role, action, timestamp, details} for critical events.

## Phase 4: Streamlit UI Skeleton

1. layout-base — Build login screen, role-aware sidebar, placeholder pages for Admin/Doctor/Receptionist.
2. footer-uptime — Add uptime/last-sync indicator and error handling wrappers (try/except) around DB calls.

## Phase 5: Role-Specific Features

1. admin-panel — Show raw + anonymized tables, anonymization trigger, CSV export for patients/logs, audit log table.
2. doctor-panel — Read-only anonymized patient view with masked diagnosis handling.
3. receptionist-panel — Form to add/edit patients with validation, without exposing masked fields.

## Phase 6: Integrity & Reliability Enhancements

1. validation-guards — Enforce RBAC checks in services/UI; handle unauthorized attempts gracefully and log them.
2. backup-export — Finalize CSV export logic, ensure log download is admin-only, add optional backup script.
3. availability-tests — Test error paths, confirm logging for failures, document recovery steps.

## Phase 7: QA & Documentation

1. qa-tests — Manual test checklist per role, verify logging/anonymization/export paths.
2. docs-update — Update `README`/`PRD` sections describing setup, roles, security controls, and usage.
3. handoff-package — Prepare final instructions (run commands, credentials, known limitations).