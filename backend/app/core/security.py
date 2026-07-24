"""无额外依赖的密码哈希与 HS256 JWT 实现。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("密码至少需要 8 个字符")
    salt = os.urandom(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt$16384$8$1${_b64(salt)}${_b64(derived)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(),
            salt=_unb64(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=32,
        )
        return hmac.compare_digest(_b64(actual), expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str, role: str) -> str:
    return _create_token(
        {"sub": user_id, "role": role, "type": "access"},
        timedelta(minutes=settings.access_token_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "refresh", "nonce": secrets.token_urlsafe(12)},
        timedelta(days=settings.refresh_token_days),
    )


def _create_token(payload: dict, lifetime: timedelta) -> str:
    now = datetime.now(timezone.utc)
    body = {**payload, "iat": int(now.timestamp()), "exp": int((now + lifetime).timestamp())}
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        f"{_b64(json.dumps(header, separators=(',', ':')).encode())}."
        f"{_b64(json.dumps(body, separators=(',', ':')).encode())}"
    )
    signature = hmac.new(
        settings.jwt_secret.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_b64(signature)}"


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        header, payload, signature = token.split(".")
        expected = hmac.new(
            settings.jwt_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_unb64(signature), expected):
            raise ValueError("令牌签名无效")
        data = json.loads(_unb64(payload))
        if data.get("type") != expected_type:
            raise ValueError("令牌类型无效")
        if int(data.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("令牌已过期")
        return data
    except Exception as exc:
        raise ValueError("无效令牌") from exc


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
