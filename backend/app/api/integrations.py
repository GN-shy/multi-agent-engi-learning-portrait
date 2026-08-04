"""用户自带密钥（BYOK）、连接测试、预算和用量 API。"""

from __future__ import annotations

from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, success
from app.core.database import get_db
from app.core.models import ExternalServiceConfig, ExternalUsageLog, User
from app.infrastructure.external_gateway import (
    GatewayError,
    OpenAICompatibleGateway,
    WebSearchGateway,
    validate_external_url,
)
from app.infrastructure.secrets import (
    SecretError,
    decrypt_secret,
    encrypt_secret,
    temporary_secrets,
)
from app.schemas import ExternalSearchInput, ExternalServiceInput, TemporaryKeyInput

router = APIRouter(prefix="/integrations", tags=["integrations"])


PROVIDER_DEFAULTS = {
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "service_type": "llm"},
    "openai": {"base_url": "https://api.openai.com/v1", "service_type": "llm"},
    "openai_compatible": {"base_url": "", "service_type": "llm"},
    "tavily": {"base_url": "https://api.tavily.com", "service_type": "search"},
    "serper": {"base_url": "https://google.serper.dev", "service_type": "search"},
    "custom": {"base_url": "", "service_type": "search"},
}


def config_view(row: ExternalServiceConfig) -> dict:
    return {
        "id": row.id,
        "service_type": row.service_type,
        "provider": row.provider,
        "label": row.label,
        "base_url": row.base_url,
        "model": row.model,
        "storage_mode": row.storage_mode,
        "masked_key": f"••••••••{row.key_last4}" if row.key_last4 else "",
        "key_available": bool(row.encrypted_api_key)
        if row.storage_mode == "encrypted"
        else temporary_secrets.exists(row.user_id, row.id),
        "max_tokens_per_request": row.max_tokens_per_request,
        "daily_budget": row.daily_budget,
        "timeout_seconds": row.timeout_seconds,
        "input_price_per_million": row.input_price_per_million,
        "output_price_per_million": row.output_price_per_million,
        "daily_request_limit": row.daily_request_limit,
        "enabled": row.enabled,
        "last_test_status": row.last_test_status,
        "last_test_message": row.last_test_message,
        "last_tested_at": row.last_tested_at.isoformat() if row.last_tested_at else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def config_runtime(row: ExternalServiceConfig) -> dict:
    return {
        "id": row.id,
        "service_type": row.service_type,
        "provider": row.provider,
        "base_url": row.base_url,
        "model": row.model,
        "max_tokens_per_request": row.max_tokens_per_request,
        "daily_budget": row.daily_budget,
        "timeout_seconds": row.timeout_seconds,
        "input_price_per_million": row.input_price_per_million,
        "output_price_per_million": row.output_price_per_million,
        "daily_request_limit": row.daily_request_limit,
    }


def get_owned_config(
    config_id: str, user: User, db: Session, service_type: str | None = None
) -> ExternalServiceConfig:
    row = db.get(ExternalServiceConfig, config_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="服务配置不存在")
    if service_type and row.service_type != service_type:
        raise HTTPException(status_code=409, detail=f"该配置不是 {service_type} 服务")
    return row


def resolve_api_key(row: ExternalServiceConfig) -> str:
    try:
        if row.storage_mode == "encrypted":
            if not row.encrypted_api_key:
                raise HTTPException(status_code=409, detail="加密密钥尚未设置")
            return decrypt_secret(row.encrypted_api_key)
        value = temporary_secrets.get(row.user_id, row.id)
        if not value:
            raise HTTPException(status_code=409, detail="临时密钥不存在或已过期，请重新输入")
        return value
    except SecretError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def usage_today(row: ExternalServiceConfig, db: Session) -> dict:
    start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)
    request_count, total_cost, prompt_tokens, completion_tokens = db.execute(
        select(
            func.count(ExternalUsageLog.id),
            func.coalesce(func.sum(ExternalUsageLog.estimated_cost), 0),
            func.coalesce(func.sum(ExternalUsageLog.prompt_tokens), 0),
            func.coalesce(func.sum(ExternalUsageLog.completion_tokens), 0),
        ).where(
            ExternalUsageLog.config_id == row.id,
            ExternalUsageLog.created_at >= start,
            ExternalUsageLog.status == "success",
        )
    ).one()
    return {
        "requests": int(request_count),
        "estimated_cost": round(float(total_cost), 8),
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "request_limit": row.daily_request_limit,
        "budget": row.daily_budget,
    }


def enforce_limits(row: ExternalServiceConfig, db: Session) -> dict:
    usage = usage_today(row, db)
    if usage["requests"] >= row.daily_request_limit:
        raise HTTPException(status_code=429, detail="今日外部服务请求次数已达上限")
    if row.daily_budget > 0 and usage["estimated_cost"] >= row.daily_budget:
        raise HTTPException(status_code=429, detail="今日模型预算已用尽")
    return usage


def record_usage(
    row: ExternalServiceConfig,
    db: Session,
    operation: str,
    *,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    estimated_cost: float = 0,
    status_value: str = "success",
    error_code: str = "",
    session_id: str | None = None,
    model: str | None = None,
) -> None:
    db.add(
        ExternalUsageLog(
            user_id=row.user_id,
            config_id=row.id,
            session_id=session_id,
            operation=operation,
            provider=row.provider,
            model=model or row.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost=estimated_cost,
            status=status_value,
            error_code=error_code,
        )
    )


@router.get("/providers/catalog")
def provider_catalog():
    return success(
        {
            "items": [
                {"provider": key, **value} for key, value in PROVIDER_DEFAULTS.items()
            ],
            "source_modes": [
                {
                    "code": "knowledge_only",
                    "name": "仅知识库",
                    "description": "只使用本地审核知识库，可靠性最高，不产生外部费用。",
                },
                {
                    "code": "knowledge_web",
                    "name": "知识库 + 全网检索",
                    "description": "补充最新框架和技术资料，不调用生成模型。",
                },
                {
                    "code": "knowledge_ai",
                    "name": "知识库 + AI 创作",
                    "description": "模型只能基于本地证据整合和个性化生成。",
                },
                {
                    "code": "full",
                    "name": "全能力模式",
                    "description": "本地知识、联网检索、双 Agent 生成、仲裁与引用校验。",
                },
            ],
        }
    )


@router.get("/providers")
def list_configs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(ExternalServiceConfig)
        .where(ExternalServiceConfig.user_id == user.id)
        .order_by(ExternalServiceConfig.created_at.asc())
    ).all()
    return success({"items": [config_view(row) for row in rows]})


@router.post("/providers", status_code=status.HTTP_201_CREATED)
def create_config(
    body: ExternalServiceInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expected = PROVIDER_DEFAULTS[body.provider]["service_type"]
    if body.provider not in {"openai_compatible", "custom"} and body.service_type != expected:
        raise HTTPException(status_code=422, detail="服务类型与厂商不匹配")
    try:
        base_url = validate_external_url(body.base_url, resolve_dns=False)
    except GatewayError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if body.service_type == "llm" and not body.model.strip():
        raise HTTPException(status_code=422, detail="LLM 配置必须填写模型名称")
    if not body.api_key:
        raise HTTPException(status_code=422, detail="创建配置时必须输入 API Key")
    encrypted = ""
    if body.storage_mode == "encrypted":
        try:
            encrypted = encrypt_secret(body.api_key)
        except SecretError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    row = ExternalServiceConfig(
        user_id=user.id,
        service_type=body.service_type,
        provider=body.provider,
        label=body.label.strip(),
        base_url=base_url,
        model=body.model.strip(),
        encrypted_api_key=encrypted,
        key_last4=body.api_key[-4:],
        storage_mode=body.storage_mode,
        max_tokens_per_request=body.max_tokens_per_request,
        daily_budget=body.daily_budget,
        timeout_seconds=body.timeout_seconds,
        input_price_per_million=body.input_price_per_million,
        output_price_per_million=body.output_price_per_million,
        daily_request_limit=body.daily_request_limit,
        enabled=body.enabled,
    )
    db.add(row)
    db.flush()
    if body.storage_mode == "temporary":
        temporary_secrets.set(user.id, row.id, body.api_key)
    db.commit()
    db.refresh(row)
    return success(config_view(row), "服务配置已创建")


@router.put("/providers/{config_id}")
def update_config(
    config_id: str,
    body: ExternalServiceInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_owned_config(config_id, user, db)
    previous_storage_mode = row.storage_mode
    expected = PROVIDER_DEFAULTS[body.provider]["service_type"]
    if body.provider not in {"openai_compatible", "custom"} and body.service_type != expected:
        raise HTTPException(status_code=422, detail="服务类型与厂商不匹配")
    if body.service_type == "llm" and not body.model.strip():
        raise HTTPException(status_code=422, detail="LLM 配置必须填写模型名称")
    try:
        row.base_url = validate_external_url(body.base_url, resolve_dns=False)
    except GatewayError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    row.service_type = body.service_type
    row.provider = body.provider
    row.label = body.label.strip()
    row.model = body.model.strip()
    row.max_tokens_per_request = body.max_tokens_per_request
    row.daily_budget = body.daily_budget
    row.timeout_seconds = body.timeout_seconds
    row.input_price_per_million = body.input_price_per_million
    row.output_price_per_million = body.output_price_per_million
    row.daily_request_limit = body.daily_request_limit
    row.enabled = body.enabled
    row.updated_at = datetime.now(timezone.utc)
    if body.api_key:
        row.key_last4 = body.api_key[-4:]
        if body.storage_mode == "encrypted":
            try:
                row.encrypted_api_key = encrypt_secret(body.api_key)
            except SecretError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            temporary_secrets.clear(user.id, row.id)
        else:
            row.encrypted_api_key = ""
            temporary_secrets.set(user.id, row.id, body.api_key)
    elif previous_storage_mode != body.storage_mode:
        raise HTTPException(status_code=422, detail="切换密钥保存方式时必须重新输入 API Key")
    row.storage_mode = body.storage_mode
    db.commit()
    db.refresh(row)
    return success(config_view(row), "服务配置已更新")


@router.post("/providers/{config_id}/temporary-key")
def set_temporary_key(
    config_id: str,
    body: TemporaryKeyInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_owned_config(config_id, user, db)
    if row.storage_mode != "temporary":
        raise HTTPException(status_code=409, detail="该配置不是临时密钥模式")
    temporary_secrets.set(user.id, row.id, body.api_key)
    row.key_last4 = body.api_key[-4:]
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    return success(config_view(row), "临时密钥已装载")


@router.delete("/providers/{config_id}/temporary-key")
def clear_temporary_key(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_owned_config(config_id, user, db)
    temporary_secrets.clear(user.id, row.id)
    return success(config_view(row), "临时密钥已清除")


@router.delete("/providers/{config_id}")
def delete_config(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_owned_config(config_id, user, db)
    temporary_secrets.clear(user.id, row.id)
    db.execute(delete(ExternalUsageLog).where(ExternalUsageLog.config_id == row.id))
    db.delete(row)
    db.commit()
    return success(message="服务配置已删除")


@router.post("/providers/{config_id}/test")
def test_config(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_owned_config(config_id, user, db)
    if not row.enabled:
        raise HTTPException(status_code=409, detail="服务配置已停用")
    enforce_limits(row, db)
    api_key = resolve_api_key(row)
    try:
        if row.service_type == "llm":
            result = OpenAICompatibleGateway(config_runtime(row), api_key).test_connection()
            record_usage(
                row,
                db,
                "connection_test",
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                estimated_cost=result.estimated_cost,
                model=result.model,
            )
            message = f"连接成功，模型返回 {result.content[:40]}"
        else:
            items = WebSearchGateway(config_runtime(row), api_key).test_connection()
            record_usage(row, db, "connection_test")
            message = f"连接成功，返回 {len(items)} 条标准化结果"
        row.last_test_status = "success"
        row.last_test_message = message
        row.last_tested_at = datetime.now(timezone.utc)
        db.commit()
        return success({"status": "success", "message": message}, "连接测试成功")
    except GatewayError as exc:
        record_usage(row, db, "connection_test", status_value="failed", error_code=exc.code)
        row.last_test_status = "failed"
        row.last_test_message = str(exc)
        row.last_tested_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/usage")
def usage(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(ExternalServiceConfig).where(ExternalServiceConfig.user_id == user.id)
    ).all()
    return success(
        {
            "items": [
                {"config": config_view(row), "today": usage_today(row, db)} for row in rows
            ]
        }
    )


@router.post("/search")
def external_search(
    body: ExternalSearchInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_owned_config(body.config_id, user, db, "search")
    enforce_limits(row, db)
    try:
        items = WebSearchGateway(config_runtime(row), resolve_api_key(row)).search(
            body.query, body.top_k
        )
        record_usage(row, db, "web_search")
        db.commit()
        return success(
            {
                "items": items,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "provider": row.provider,
                "masked_key": config_view(row)["masked_key"],
            }
        )
    except GatewayError as exc:
        record_usage(row, db, "web_search", status_value="failed", error_code=exc.code)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
