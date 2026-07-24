"""BYOK 密钥加密与临时密钥仓库。

密钥从不出现在响应、日志、Agent 事件或报告中。临时密钥仅驻留当前后端进程，
到期、退出或显式清除后立即失效。
"""

from __future__ import annotations

import base64
import hashlib
import threading
from datetime import datetime, timedelta, timezone

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # 允许无 BYOK 依赖时继续运行比赛核心闭环
    Fernet = None  # type: ignore[assignment,misc]
    InvalidToken = Exception  # type: ignore[assignment,misc]

from app.core.config import settings


class SecretError(RuntimeError):
    pass


def _fernet():
    if Fernet is None:
        raise SecretError("加密保存功能未安装 cryptography 依赖")
    material = settings.byok_master_key or settings.jwt_secret
    if settings.environment == "production" and not settings.byok_master_key:
        raise SecretError("生产环境必须配置独立的 BYOK_MASTER_KEY")
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    if not value:
        raise SecretError("密钥不能为空")
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise SecretError("密钥无法解密，请重新配置") from exc


class TemporarySecretStore:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str], tuple[str, datetime]] = {}
        self._lock = threading.Lock()

    def set(self, user_id: str, config_id: str, value: str) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.temporary_key_ttl_minutes
        )
        with self._lock:
            self._values[(user_id, config_id)] = (value, expires_at)

    def get(self, user_id: str, config_id: str) -> str | None:
        with self._lock:
            item = self._values.get((user_id, config_id))
            if not item:
                return None
            value, expires_at = item
            if expires_at <= datetime.now(timezone.utc):
                self._values.pop((user_id, config_id), None)
                return None
            return value

    def clear(self, user_id: str, config_id: str | None = None) -> None:
        with self._lock:
            keys = [
                key
                for key in self._values
                if key[0] == user_id and (config_id is None or key[1] == config_id)
            ]
            for key in keys:
                self._values.pop(key, None)

    def exists(self, user_id: str, config_id: str) -> bool:
        return self.get(user_id, config_id) is not None


temporary_secrets = TemporarySecretStore()
