"""密码哈希（argon2）与 JWT 签发/校验。"""
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

logger = logging.getLogger(__name__)

password_hasher = PasswordHash.recommended()  # argon2


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(
    *, user_id: str, secret: str, expires_minutes: int, algorithm: str = "HS256"
) -> str:
    if not secret:
        raise ValueError("JWT_SECRET is not configured")
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(
    *, token: str, secret: str, algorithm: str = "HS256"
) -> dict[str, Any]:
    if not secret:
        raise ValueError("JWT_SECRET is not configured")
    return jwt.decode(token, secret, algorithms=[algorithm])
