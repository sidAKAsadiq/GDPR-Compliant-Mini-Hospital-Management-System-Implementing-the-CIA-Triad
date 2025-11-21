## Database Schema Overview

Derived from `PRD.md` requirements. Database defaults to SQLite (`data/hospital.db`), but SQL is portable to MySQL with minor syntax tweaks.

### users
| field      | type        | constraints                            | notes                            |
|------------|-------------|----------------------------------------|----------------------------------|
| user_id    | INTEGER     | PRIMARY KEY AUTOINCREMENT              |                                  |
| username   | TEXT        | UNIQUE NOT NULL                        | lowercased for comparisons       |
| password   | TEXT        | NOT NULL                               | stores hashed password (SHA-256) |
| role       | TEXT        | NOT NULL CHECK role IN ('admin','doctor','receptionist') | enforces RBAC roles |
| created_at | TIMESTAMP   | DEFAULT CURRENT_TIMESTAMP              | auditing support                 |

### patients
| field              | type      | constraints                      | notes                                    |
|--------------------|-----------|----------------------------------|------------------------------------------|
| patient_id         | INTEGER   | PRIMARY KEY AUTOINCREMENT        |                                          |
| name               | TEXT      | NOT NULL                         | raw name (confidential)                  |
| contact            | TEXT      | NOT NULL                         | raw contact                              |
| diagnosis          | TEXT      | NOT NULL                         | sensitive                                |
| anonymized_name    | TEXT      | NOT NULL                         | masked e.g., `ANON_xxxx`                 |
| anonymized_contact | TEXT      | NOT NULL                         | masked e.g., `XXX-XXX-####`              |
| diagnosis_masked   | TEXT      | NOT NULL                         | hashed/masked diagnosis for doctors      |
| date_added         | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP        |                                          |
| last_updated       | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP        | updated via trigger/app logic            |

### logs
| field     | type      | constraints                       | notes                               |
|-----------|-----------|-----------------------------------|-------------------------------------|
| log_id    | INTEGER   | PRIMARY KEY AUTOINCREMENT         |                                     |
| user_id   | INTEGER   | NOT NULL REFERENCES users(user_id)| cascades optional (RESTRICT deletes)|
| role      | TEXT      | NOT NULL                          | redundantly stored for quick audits |
| action    | TEXT      | NOT NULL                          | e.g., login/view/update/export      |
| details   | TEXT      |                                   | JSON or string payload              |
| timestamp | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP         | server time                         |

### indexes & constraints
- `users.username` unique for login.
- `patients.name` optional index if search needed.
- `logs.user_id` foreign key index for query speed.

### initialization workflow
1. Load env vars from `.env` (`DB_PATH`, default admin creds, optional Fernet key).
2. Run `python app/db.py` to create tables.
3. Script seeds default Admin/Doctor/Receptionist with hashed passwords.
4. Subsequent runs are idempotent (uses `INSERT OR IGNORE` / UPSERTs).

### viewing the SQLite database
After initialization:
```powershell
sqlite3 data/hospital.db ".tables"
sqlite3 data/hospital.db "SELECT * FROM users;"
```
If `sqlite3` CLI isn't installed, install from https://www.sqlite.org/download.html or use a GUI like DB Browser for SQLite.

