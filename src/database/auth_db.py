"""SQLite-backed authentication store."""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from pathlib import Path
from typing import Optional


AUTH_DB_PATH = Path(os.getenv("AUTH_DB_PATH", "data/auth.db"))
HASH_ITERATIONS = 120_000


def initialize_db(db_path: Path = AUTH_DB_PATH) -> Path:
    """Ensure the auth database and schema exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "email" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)"
        )
        conn.commit()
    return db_path


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
    )
    return f"{HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        iterations_str, salt_hex, digest_hex = stored_hash.split("$", 2)
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False

    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(computed, expected)


def create_user(
    username: str,
    hashed_password: str,
    role: str,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
) -> bool:
    """Create a user record. Returns False when username exists."""
    initialize_db()
    normalized = username.strip()
    if not normalized:
        raise ValueError("Username cannot be empty")

    with sqlite3.connect(AUTH_DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (normalized,),
        )
        if cursor.fetchone():
            return False

        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, full_name, email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (normalized, hashed_password, role, full_name, email),
        )
        conn.commit()
    return True


def verify_user(username: str, password: str) -> Optional[dict]:
    """Verify a username/password pair. Returns user dict or None."""
    initialize_db()
    normalized = username.strip()
    if not normalized:
        return None

    with sqlite3.connect(AUTH_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT username, password_hash, role, full_name, email
            FROM users
            WHERE username = ?
            """,
            (normalized,),
        ).fetchone()

    if row is None:
        return None

    if not _verify_password(password, row["password_hash"]):
        return None

    return {
        "username": row["username"],
        "role": row["role"],
        "full_name": row["full_name"],
        "email": row["email"],
    }


def get_user(username: str) -> Optional[dict]:
    """Fetch a user record without validating password."""
    initialize_db()
    normalized = username.strip()
    if not normalized:
        return None

    with sqlite3.connect(AUTH_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, username, role, full_name, email
            FROM users
            WHERE username = ?
            """,
            (normalized,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "full_name": row["full_name"],
        "email": row["email"],
    }


def get_user_by_role(role: str) -> Optional[dict]:
    """Fetch the first user record for a given role."""
    initialize_db()
    normalized = role.strip()
    if not normalized:
        return None

    with sqlite3.connect(AUTH_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT username, role, full_name, email
            FROM users
            WHERE role = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (normalized,),
        ).fetchone()

    if row is None:
        return None

    return {
        "username": row["username"],
        "role": row["role"],
        "full_name": row["full_name"],
        "email": row["email"],
    }


def get_user_by_email(email: str) -> Optional[dict]:
    """Fetch a user record by email address."""
    initialize_db()
    normalized = email.strip()
    if not normalized:
        return None

    with sqlite3.connect(AUTH_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, username, email, role, full_name
            FROM users
            WHERE email = ?
            """,
            (normalized,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "role": row["role"],
        "full_name": row["full_name"],
    }


__all__ = [
    "AUTH_DB_PATH",
    "initialize_db",
    "create_user",
    "verify_user",
    "hash_password",
    "get_user",
    "get_user_by_role",
    "get_user_by_email",
]
