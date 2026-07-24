"""全局配置管理。所有配置项通过环境变量注入，严禁硬编码。"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    # 数据库
    postgres_url: str = "postgresql+asyncpg://user:pass@localhost:5432/gxlian"
    chroma_persist_dir: str = "./data/chroma"
    redis_url: str = "redis://localhost:6379/0"

    # 服务端口
    gw_port: int = 8000

    # 辩论配置
    debate_max_rounds: int = 3
    debate_single_round_timeout: int = 15

    # Agent LLM参数
    llm_timeout: int = 30

    # 学习监督
    supervision_cron_time: str = "09:00"
    email_smtp_host: str = ""
    email_smtp_port: int = 587

    # 日志
    log_level: str = "INFO"

    # 知识库
    similarity_threshold: float = 0.7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
# Demo模式：无真实API密钥时自动启用规则引擎
DEMO_MODE = (
    not settings.deepseek_api_key
    or settings.deepseek_api_key == "your_deepseek_key_here"
    or len(settings.deepseek_api_key) < 10
)
