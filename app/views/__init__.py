"""View exports for Streamlit pages.

Views are imported lazily via __getattr__ to prevent:
  - Streamlit ScriptRunContext warnings on bare import
  - Cascade failures when a view-level dependency (joblib, shap) is missing
  - Unnecessary module loading on pages that don't need every view
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .auditor import render_auditor
    from .dashboard import (
        render_anomaly_page,
        render_dashboard,
        render_forecasting_page,
    )
    from .jira_sync import render_jira_sync_page
    from .login import render_login_view
    from .settings import render_settings
    from .what_if import render_what_if_page

__all__ = [
    "render_auditor",
    "render_anomaly_page",
    "render_dashboard",
    "render_forecasting_page",
    "render_jira_sync_page",
    "render_login_view",
    "render_settings",
    "render_what_if_page",
]

_LAZY_MAP: dict[str, str] = {
    "render_auditor": "app.views.auditor",
    "render_anomaly_page": "app.views.dashboard",
    "render_dashboard": "app.views.dashboard",
    "render_forecasting_page": "app.views.dashboard",
    "render_jira_sync_page": "app.views.jira_sync",
    "render_login_view": "app.views.login",
    "render_settings": "app.views.settings",
    "render_what_if_page": "app.views.what_if",
}


def __getattr__(name: str):
    if name in _LAZY_MAP:
        import importlib

        module = importlib.import_module(_LAZY_MAP[name])
        obj = getattr(module, name)
        globals()[name] = obj
        return obj
    raise AttributeError(f"module 'app.views' has no attribute {name!r}")


def __dir__() -> list[str]:
    return __all__
