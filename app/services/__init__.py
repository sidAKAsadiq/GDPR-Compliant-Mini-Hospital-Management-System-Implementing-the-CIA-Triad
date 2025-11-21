"""Service layer exports."""
from __future__ import annotations

from importlib import import_module
from types import ModuleType


def _import(name: str) -> ModuleType:
    try:
        return import_module(f".{name}", __name__)
    except ImportError:
        return import_module(name)


auth_service = _import("auth_service")
log_service = _import("log_service")
patient_service = _import("patient_service")

__all__ = ["auth_service", "log_service", "patient_service"]
