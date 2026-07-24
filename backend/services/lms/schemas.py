"""学情建模服务 Schemas"""

from pydantic import BaseModel, Field


class LMSConfig(BaseModel):
    model: str = "deepseek-chat"
    temperature: float = 0.1
    max_tokens: int = 2000
    timeout: int = 30
