# PRD — Hospital Privacy Dashboard (Assignment 4)

## 1. Overview

This product is a **GDPR-aware Mini Hospital Management Dashboard** built using **Streamlit, Python, and SQLite/MySQL**, demonstrating the **CIA Triad** (Confidentiality, Integrity, Availability) in handling patient data.

The system includes:

- Secure authentication  
- Role-Based Access Control (RBAC)  
- Data anonymization/masking/encryption  
- Logging & audit trails  
- Reliability features (error handling, backup/export, uptime)

---

## 2. Goals

- Protect patient privacy using GDPR-aligned methods  
- Ensure confidentiality, integrity, and availability of hospital records  
- Demonstrate real-world privacy & security concepts in a small working system

---

## 3. Functional Requirements

### 3.1 Confidentiality

#### 3.1.1 Data Protection

Encrypt or hash personal data using:

- `hashlib`, or  
- `Fernet` (optional bonus)

Sensitive fields must be masked:

- **name → ANON_xxxx**  
- **contact → XXX-XXX-####**  
- **diagnosis** masked for unauthorized roles  

#### 3.1.2 Role-Based Access Control

There are **3 user roles**:

| Role         | Permissions                                           |
|--------------|--------------------------------------------------------|
| **Admin**        | Full access to raw + anonymized data, logs           |
| **Doctor**       | View anonymized data only                            |
| **Receptionist** | Add/edit records; cannot view sensitive fields       |

#### 3.1.3 Authentication

- Login page verifies **username**, **password**, and assigns **role**.

---

### 3.2 Integrity

#### 3.2.1 Activity Logging

Create a **logs table** to store:

- user_id  
- role  
- action (login, view, update, anonymize, export)  
- timestamp  
- details  

All **critical user actions must be logged**.

#### 3.2.2 Validation / Constraints

- Unauthorized modifications must be blocked.  
- Database constraints or code-based checks must be applied.

#### 3.2.3 Audit Log Screen

- Admin-only page showing all logs in a table.

---

### 3.3 Availability

#### 3.3.1 Reliable System Operation

- Dashboard must remain responsive.  
- Implement `try/except` around DB operations and logins.

#### 3.3.2 Backup / Export

Provide **Download CSV** for:

- patient data  
- logs (admin only)

#### 3.3.3 Uptime Indicator

Footer showing:

- system uptime **OR**  
- last synchronization timestamp  

---

## 4. Database Schema

### 4.1 Users Table  
`user_id | username | password | role`

### 4.2 Patients Table  
`patient_id | name | contact | diagnosis | anonymized_name | anonymized_contact | date_added`

### 4.3 Logs Table  
`log_id | user_id | role | action | timestamp | details`

---

## 5. UI Requirements

### 5.1 Login Page

- Username + password  
- Invalid login error handling  

### 5.2 Main Dashboard

Depends on user role:

#### Admin

- View raw & anonymized patient data  
- Trigger anonymization/encryption  
- View audit logs  
- Export CSV  

#### Doctor

- View anonymized data only  

#### Receptionist

- Add/edit patient records  
- Cannot view masked data  

### 5.3 Footer

- Uptime or last synced time  

---

## 6. Workflow

1. User logs in  
2. Role determines which pages/actions are visible  
3. Admin may trigger anonymization  
4. Doctor views anonymized patient data  
5. Receptionist adds/edits data  
6. All actions stored in logs  
7. Admin may view/export logs  

---

## 7. Error Handling

- Invalid login → error message  
- Database failures → safe fallback + log entry  
- Missing fields → validation errors  

---

## 8. Bonus Features (Optional +2 Marks)

- Fernet reversible encryption  
- Real-time activity graphs  
- GDPR additions:  
  - Data retention timer  
  - User consent banner  
