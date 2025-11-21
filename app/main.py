"""Streamlit entry point for GDPR-aware hospital dashboard."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict

import streamlit as st

FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from .services import auth_service  # type: ignore
except ImportError:
    from services import auth_service


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

    nav_options = []
    role = current_user["role"]
    if role == "admin":
        nav_options = ["Admin Dashboard", "Doctor View", "Receptionist Workspace"]
    elif role == "doctor":
        nav_options = ["Doctor View"]
    elif role == "receptionist":
        nav_options = ["Receptionist Workspace"]

    selection = st.sidebar.radio("Navigation", nav_options)

    if st.sidebar.button("Log out"):
        auth_service.logout_user(st.session_state)
        st.rerun()

    return selection


def render_admin_placeholder() -> None:
    st.header("Admin Dashboard")
    st.info(
        "Upcoming: raw/anonymized patient tables, anonymization triggers, audit log access, CSV exports."
    )


def render_doctor_placeholder() -> None:
    st.header("Doctor View")
    st.info("Upcoming: anonymized patient list with masked diagnosis per PRD.")


def render_receptionist_placeholder() -> None:
    st.header("Receptionist Workspace")
    st.info("Upcoming: patient add/edit forms with validation, without revealing sensitive fields.")


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
            render_admin_placeholder()
        elif selection == "Doctor View":
            render_doctor_placeholder()
        elif selection == "Receptionist Workspace":
            render_receptionist_placeholder()
        else:
            st.warning("Unknown section selected.")
    except Exception as exc:  # pragma: no cover - UI safeguard
        st.error(f"An unexpected error occurred: {exc}")

    render_footer()


if __name__ == "__main__":
    main()

