"""Streamlit entry point for GDPR-aware hospital dashboard."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from .services import auth_service, log_service, patient_service  # type: ignore
except ImportError:
    from services import auth_service, log_service, patient_service


def ensure_session_defaults() -> None:
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None
    if "app_start_time" not in st.session_state:
        st.session_state["app_start_time"] = time.time()
    if "login_error" not in st.session_state:
        st.session_state["login_error"] = ""


def render_login() -> None:
    st.title("Hospital Privacy Dashboard — Login")
    st.caption("GDPR-aware Mini Hospital Management System")

    if st.session_state["login_error"]:
        st.error(st.session_state["login_error"])

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

        if submitted:
            user = auth_service.authenticate_user(username, password)
            if user:
                auth_service.set_session_user(st.session_state, user)
                st.session_state["login_error"] = ""
                st.rerun()
            else:
                st.session_state["login_error"] = "Invalid credentials. Please try again."
                st.rerun()


def sidebar_controls(current_user: Dict[str, str]) -> str:
    st.sidebar.success(f"Logged in as: {current_user['username']} ({current_user['role']})")

    role = current_user["role"]
    nav_options = {
        "admin": ["Admin Dashboard"],
        "doctor": ["Doctor View"],
        "receptionist": ["Receptionist Workspace"],
    }
    selection = st.sidebar.radio("Navigation", nav_options.get(role, []))

    if st.sidebar.button("Log out"):
        auth_service.logout_user(st.session_state)
        st.rerun()

    return selection


def _render_patient_table(title: str, data: List[Dict]) -> None:
    st.subheader(title)
    if not data:
        st.info("No records available.")
        return
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"Download {title} CSV",
        data=csv_bytes,
        file_name=f"{title.lower().replace(' ', '_')}.csv",
        mime="text/csv",
    )


def render_admin_panel(user: Dict[str, str]) -> None:
    if user["role"] != "admin":
        st.error("You do not have permission to view this page.")
        return

    st.header("Admin Dashboard")

    col1, col2 = st.columns(2)
    with col1:
        raw_patients = patient_service.list_patients(view="raw")
        _render_patient_table("Raw Patient Data", raw_patients)
    with col2:
        anonymized_patients = patient_service.list_patients(view="anonymized")
        _render_patient_table("Anonymized Patient Data", anonymized_patients)

    if st.button("Refresh Anonymized Fields"):
        patient_service.refresh_anonymized_fields(acted_by=user)
        st.success("Anonymized fields refreshed.")
        st.rerun()

    st.subheader("Audit Logs")
    logs = log_service.list_logs(limit=200)
    if logs:
        logs_df = pd.DataFrame(logs)
        st.dataframe(logs_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Logs CSV",
            logs_df.to_csv(index=False).encode("utf-8"),
            file_name="audit_logs.csv",
            mime="text/csv",
        )
    else:
        st.info("No logs recorded yet.")


def render_doctor_view(user: Dict[str, str]) -> None:
    if user["role"] not in {"doctor", "admin"}:
        st.error("You do not have permission to view this page.")
        return

    st.header("Doctor View")
    anonymized_patients = patient_service.list_patients(view="anonymized")
    search = st.text_input("Search anonymized name or diagnosis code")
    if search:
        search_lower = search.lower()
        anonymized_patients = [
            p
            for p in anonymized_patients
            if search_lower in p["anonymized_name"].lower()
            or search_lower in p["diagnosis_masked"].lower()
        ]

    _render_patient_table("Anonymized Patients", anonymized_patients)


def render_receptionist_workspace(user: Dict[str, str]) -> None:
    if user["role"] not in {"receptionist", "admin"}:
        st.error("You do not have permission to view this page.")
        return

    st.header("Receptionist Workspace")
    st.caption("Add or update patient records. Sensitive/masked data remains hidden.")

    with st.form("add_patient_form"):
        st.subheader("Add New Patient")
        name = st.text_input("Patient Name")
        contact = st.text_input("Contact Number")
        diagnosis = st.text_area("Diagnosis")
        add_submitted = st.form_submit_button("Add Patient")
        if add_submitted:
            if not (name and contact and diagnosis):
                st.error("All fields are required.")
            else:
                patient_id = patient_service.create_patient(
                    name=name, contact=contact, diagnosis=diagnosis, acted_by=user
                )
                st.success(f"Patient record created with ID {patient_id}.")
                st.rerun()

    st.markdown("---")
    st.subheader("Update Existing Patient")
    patients = patient_service.list_patients(view="raw")
    patient_ids = [p["patient_id"] for p in patients]
    if not patient_ids:
        st.info("No patients available to update.")
        return

    with st.form("edit_patient_form"):
        patient_choice = st.selectbox(
            "Select Patient ID to update",
            patient_ids,
            format_func=lambda pid: f"Patient #{pid}",
        )
        new_name = st.text_input("New Patient Name")
        new_contact = st.text_input("New Contact Number")
        new_diagnosis = st.text_area("New Diagnosis")
        update_submitted = st.form_submit_button("Update Patient")
        if update_submitted:
            if not (new_name and new_contact and new_diagnosis):
                st.error("All fields are required to update a patient.")
            else:
                patient_service.update_patient(
                    patient_id=patient_choice,
                    name=new_name,
                    contact=new_contact,
                    diagnosis=new_diagnosis,
                    acted_by=user,
                )
                st.success(f"Patient #{patient_choice} updated.")
                st.rerun()


def render_footer() -> None:
    uptime_seconds = int(time.time() - st.session_state["app_start_time"])
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    st.markdown("---")
    st.caption(f"System uptime: {hours}h {minutes}m {seconds}s")


def main() -> None:
    st.set_page_config(page_title="Hospital Privacy Dashboard", layout="wide")
    ensure_session_defaults()

    current_user = auth_service.get_session_user(st.session_state)
    if not current_user:
        render_login()
        render_footer()
        return

    selection = sidebar_controls(current_user)
    try:
        if selection == "Admin Dashboard":
            render_admin_panel(current_user)
        elif selection == "Doctor View":
            render_doctor_view(current_user)
        elif selection == "Receptionist Workspace":
            render_receptionist_workspace(current_user)
        else:
            st.warning("Unknown section selected.")
    except Exception as exc:  # pragma: no cover - UI safeguard
        st.error(f"An unexpected error occurred: {exc}")

    render_footer()


if __name__ == "__main__":
    main()

