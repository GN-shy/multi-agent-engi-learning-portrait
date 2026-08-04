"""HTTP 边界使用的 Pydantic 模型。"""

import unicodedata
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Envelope(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None
    request_id: str = ""


class RegisterInput(BaseModel):
    username: str = Field(min_length=2, max_length=40)
    email: str = Field(min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: Any) -> str:
        normalized = unicodedata.normalize("NFKC", str(value or "")).strip()
        if not normalized:
            raise ValueError("用户名不能为空")
        if any(unicodedata.category(char).startswith("C") for char in normalized):
            raise ValueError("用户名不能包含不可见或控制字符")
        if any(not (char.isalnum() or char in "_.-") for char in normalized):
            raise ValueError("用户名仅支持中文、字母、数字、下划线、点和短横线")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        categories = sum(
            [
                any(char.islower() for char in value),
                any(char.isupper() for char in value),
                any(char.isdigit() for char in value),
                any(not char.isalnum() for char in value),
            ]
        )
        if categories < 3:
            raise ValueError("密码至少包含大写字母、小写字母、数字、特殊字符中的三类")
        return value


class LoginInput(BaseModel):
    account: str
    password: str


class ProfileInput(BaseModel):
    background: str = Field(default="", max_length=2000)
    learning_goals: list[str] = Field(default_factory=list, max_length=10)
    preferences: list[str] = Field(default_factory=list, max_length=15)
    weekly_hours: int = Field(default=8, ge=1, le=80)
    learning_style: Literal["theory_first", "practice_first", "balanced"] = "balanced"
    self_assessment: dict[str, float] = Field(default_factory=dict)
    diagnostic_results: dict[str, float] = Field(default_factory=dict)

    @field_validator("self_assessment", "diagnostic_results")
    @classmethod
    def validate_scores(cls, value: dict[str, float]) -> dict[str, float]:
        if any(score < 0 or score > 100 for score in value.values()):
            raise ValueError("能力得分必须位于 0 到 100")
        return value


class RouteCompareInput(BaseModel):
    track_codes: list[str] = Field(default_factory=list, max_length=6)


class PathwayComposeInput(BaseModel):
    pathway_ids: list[str] = Field(min_length=1, max_length=6)
    weekly_hours: int = Field(default=8, ge=1, le=80)


class TrackSelectInput(BaseModel):
    track_code: str


class SessionCreateInput(BaseModel):
    track_code: str
    pathway_id: str | None = Field(default=None, max_length=120)
    pathway_ids: list[str] = Field(default_factory=list, max_length=6)
    goal: str = Field(min_length=2, max_length=1000)
    topic: str = Field(default="", max_length=200)
    source_mode: Literal[
        "knowledge_only", "knowledge_web", "knowledge_ai", "full"
    ] = "knowledge_only"
    llm_config_id: str | None = None
    search_config_id: str | None = None


class FeedbackInput(BaseModel):
    feedback_type: Literal[
        "too_hard", "too_easy", "helpful", "not_helpful", "answer", "question"
    ]
    rating: int | None = Field(default=None, ge=1, le=5)
    content: dict = Field(default_factory=dict)


class AssessmentSubmitInput(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)


class CheckinInput(BaseModel):
    completed_task_ids: list[str] = Field(default_factory=list)


class ExternalServiceInput(BaseModel):
    service_type: Literal["llm", "search"]
    provider: Literal[
        "deepseek", "openai", "openai_compatible", "tavily", "serper", "custom"
    ]
    label: str = Field(min_length=2, max_length=80)
    base_url: str = Field(min_length=8, max_length=500)
    model: str = Field(default="", max_length=160)
    api_key: str = Field(default="", max_length=1000)
    storage_mode: Literal["temporary", "encrypted"] = "temporary"
    max_tokens_per_request: int = Field(default=2048, ge=64, le=128000)
    daily_budget: float = Field(default=2.0, ge=0, le=100000)
    timeout_seconds: int = Field(default=45, ge=3, le=180)
    input_price_per_million: float = Field(default=0, ge=0, le=100000)
    output_price_per_million: float = Field(default=0, ge=0, le=100000)
    daily_request_limit: int = Field(default=100, ge=1, le=100000)
    enabled: bool = True


class TemporaryKeyInput(BaseModel):
    api_key: str = Field(min_length=6, max_length=1000)


class ExternalSearchInput(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    track_code: str | None = None
    config_id: str
    top_k: int = Field(default=8, ge=1, le=20)


class PasswordChangeInput(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        return RegisterInput.validate_password_strength(value)


class AccountDeleteInput(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    confirmation: Literal["DELETE"]


class KnowledgeContributionInput(BaseModel):
    track_code: str
    title: str = Field(min_length=2, max_length=300)
    content: str = Field(min_length=50, max_length=100000)
    source_url: str = Field(min_length=8, max_length=1000)
    license_type: str = Field(default="unknown", max_length=80)
    content_version: str = Field(default="unversioned", max_length=80)


class KnowledgeReviewInput(BaseModel):
    status: Literal["approved", "rejected"]
    review_notes: str = Field(default="", max_length=2000)
