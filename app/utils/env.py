"""Environment and path helpers for Streamlit startup."""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def _load_env_file(path: Path = ENV_FILE) -> None:
    """Load key/value pairs from an .env file into process environment."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def ensure_project_root(load_env: bool = True) -> Path:
    """Ensure project root is on ``sys.path`` and optionally load ``.env``."""
    root = PROJECT_ROOT
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    if load_env:
        _load_env_file()

    return root


__all__ = ["ensure_project_root", "PROJECT_ROOT", "ENV_FILE"]
