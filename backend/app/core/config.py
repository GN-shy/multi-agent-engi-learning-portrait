"""应用配置。

开发环境默认使用本地 SQLite，生产环境通过 DATABASE_URL 切换到 PostgreSQL。
所有密钥只从环境变量读取。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "工学智链"
    app_version: str = "1.0.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    # 使用新版本文件名，避免旧原型 SQLite 表结构与当前 ORM 冲突。
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'gongxue_v1.db').as_posix()}"
    jwt_secret: str = "change-this-secret-before-production"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    cors_origins: str = "http://localhost:5173"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: int = 45
    llm_enabled: bool = False
    byok_master_key: str = ""
    temporary_key_ttl_minutes: int = 480
    allow_private_integration_hosts: bool = False

    # 治理账号只在部署者显式提供密码时初始化，不设置默认管理员口令。
    bootstrap_admin_email: str = ""
    bootstrap_admin_username: str = "治理管理员"
    bootstrap_admin_password: str = ""

    debate_max_rounds: int = 3
    normal_session_timeout_seconds: int = 30
    debate_session_timeout_seconds: int = 90

    @property
    def catalog_path(self) -> Path:
        return PROJECT_ROOT / "data" / "computer_domain" / "catalog.json"

    @property
    def evaluation_profiles_path(self) -> Path:
        return PROJECT_ROOT / "data" / "evaluation" / "learner_profiles.json"

    @property
    def evaluation_tasks_path(self) -> Path:
        return PROJECT_ROOT / "data" / "evaluation" / "evaluation_set.json"

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
