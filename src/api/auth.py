import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parents[2]
AUTH_FILE = BASE_DIR / "config" / "auth" / "users.json"

AUTH_HEADER_PREFIX = "Bearer "


def _ensure_auth_file() -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not AUTH_FILE.exists():
        AUTH_FILE.write_text(json.dumps({"users": {}}, indent=2))


def _load_users() -> dict:
    _ensure_auth_file()
    return json.loads(AUTH_FILE.read_text())


def _save_users(data: dict) -> None:
    _ensure_auth_file()
    AUTH_FILE.write_text(json.dumps(data, indent=2))


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


def create_user(email: str, password: str) -> None:
    data = _load_users()
    users = data.setdefault("users", {})
    if email in users:
        raise ValueError("A user with this email already exists.")

    salt = secrets.token_hex(16)
    users[email] = {
        "salt": salt,
        "password_hash": _hash_password(password, salt),
    }
    _save_users(data)


def authenticate_user(email: str, password: str) -> bool:
    data = _load_users()
    users = data.get("users", {})
    user = users.get(email)
    if not user:
        return False
    expected_hash = user.get("password_hash", "")
    provided_hash = _hash_password(password, user.get("salt", ""))
    return hmac.compare_digest(expected_hash, provided_hash)


_active_tokens: dict[str, str] = {}


def create_access_token(email: str) -> str:
    token = secrets.token_urlsafe(32)
    _active_tokens[token] = email
    return token


def get_email_from_token(token: str) -> Optional[str]:
    return _active_tokens.get(token)


def invalidate_token(token: str) -> None:
    _active_tokens.pop(token, None)
