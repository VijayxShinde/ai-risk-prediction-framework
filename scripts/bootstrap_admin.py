"""Bootstrap a default admin user from environment variables."""

from __future__ import annotations

import os

from dotenv import load_dotenv

# Ensure the root project directory is in the Python path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.database.auth_db import create_user, hash_password, initialize_db


def main() -> None:
    load_dotenv()

    username = os.getenv("DEFAULT_ADMIN_USER", "").strip()
    password = os.getenv("DEFAULT_ADMIN_PASS", "").strip()
    role = os.getenv("DEFAULT_ADMIN_ROLE", "Administrator").strip() or "Administrator"
    full_name = os.getenv("DEFAULT_ADMIN_FULL_NAME", "Admin User").strip() or "Admin User"
    email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@riskai.io").strip() or "admin@riskai.io"

    if not username or not password:
        print(
            "[WARN] DEFAULT_ADMIN_USER or DEFAULT_ADMIN_PASS not set. "
            "Skipping admin bootstrap."
        )
        return

    initialize_db()
    created = create_user(
        username=username,
        hashed_password=hash_password(password),
        role=role,
        full_name=full_name,
        email=email,
    )
    if created:
        print(f"[OK] Admin user '{username}' created.")
    else:
        print(f"[INFO] Admin user '{username}' already exists.")


if __name__ == "__main__":
    main()
