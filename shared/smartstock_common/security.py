from __future__ import annotations

import base64
import hashlib

from .schemas import Role

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore[assignment]
    InvalidToken = Exception  # type: ignore[assignment]


PERMISSIONS: dict[Role, set[str]] = {
    Role.WAREHOUSE: {
        "inventory:read",
        "inventory:write",
        "placement:read",
        "placement:write",
    },
    Role.LOGISTICIAN: {
        "inventory:read",
        "forecast:read",
        "optimization:read",
        "integration:read",
    },
    Role.ANALYST: {
        "inventory:read",
        "forecast:read",
        "forecast:write",
        "analytics:read",
    },
    Role.ADMIN: {
        "inventory:read",
        "inventory:write",
        "forecast:read",
        "forecast:write",
        "optimization:read",
        "optimization:write",
        "placement:read",
        "placement:write",
        "analytics:read",
        "integration:read",
        "integration:write",
        "audit:read",
        "audit:write",
    },
}


def has_permission(role: Role | str, action: str) -> bool:
    normalized = Role(role) if isinstance(role, str) else role
    return action in PERMISSIONS.get(normalized, set())


def _derive_key(raw_key: str) -> bytes:
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_sensitive(value: str, raw_key: str) -> str:
    if not value:
        return value
    if Fernet is None:
        return "dev::" + base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii")
    key = _derive_key(raw_key)
    cipher = Fernet(key)
    token = cipher.encrypt(value.encode("utf-8")).decode("utf-8")
    return token


def decrypt_sensitive(token: str, raw_key: str) -> str:
    if not token:
        return token
    if token.startswith("dev::"):
        encoded = token.split("dev::", maxsplit=1)[1]
        return base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")
    if Fernet is None:
        return token
    key = _derive_key(raw_key)
    cipher = Fernet(key)
    try:
        return cipher.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return token
