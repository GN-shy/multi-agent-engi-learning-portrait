"""注册、登录、刷新和当前用户 API。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, success
from app.core.config import settings
from app.core.database import get_db
from app.core.models import (
    AgentEvent,
    AssessmentAttempt,
    ExternalServiceConfig,
    ExternalUsageLog,
    Feedback,
    KnowledgeContribution,
    LearnerProfile,
    LearningPlan,
    LearningResource,
    LearningSession,
    Notification,
    ProfileSnapshot,
    RefreshToken,
    TrackSelection,
    User,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    token_digest,
    verify_password,
)
from app.infrastructure.secrets import temporary_secrets
from app.schemas import AccountDeleteInput, LoginInput, PasswordChangeInput, RegisterInput

router = APIRouter(prefix="/auth", tags=["auth"])


def user_view(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "role": user.role,
        "created_at": user.created_at.isoformat(),
    }


def issue_tokens(user: User, response: Response, db: Session) -> dict:
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_digest(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path=f"{settings.api_prefix}/auth",
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
        "user": user_view(user),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterInput, response: Response, db: Session = Depends(get_db)):
    exists = db.scalar(
        select(User).where(or_(User.username == body.username, User.email == body.email.lower()))
    )
    if exists:
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在")
    user = User(
        username=body.username.strip(),
        email=body.email.lower().strip(),
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success(issue_tokens(user, response, db), "注册成功")


@router.post("/login")
def login(body: LoginInput, response: Response, db: Session = Depends(get_db)):
    account = body.account.strip()
    user = db.scalar(
        select(User).where(or_(User.username == account, User.email == account.lower()))
    )
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    if not user.active:
        raise HTTPException(status_code=403, detail="账号已停用")
    return success(issue_tokens(user, response, db), "登录成功")


@router.post("/refresh")
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="缺少刷新令牌")
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_digest(refresh_token))
    )
    now = datetime.now(timezone.utc).timestamp()
    expiry = record.expires_at.replace(tzinfo=timezone.utc).timestamp() if record else 0
    if not record or record.revoked or expiry < now:
        raise HTTPException(status_code=401, detail="刷新令牌已失效")
    record.revoked = True
    user = db.get(User, payload["sub"])
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="用户不存在或已停用")
    db.commit()
    return success(issue_tokens(user, response, db))


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token:
        record = db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_digest(refresh_token))
        )
        if record:
            temporary_secrets.clear(record.user_id)
            record.revoked = True
            db.commit()
    response.delete_cookie("refresh_token", path=f"{settings.api_prefix}/auth")
    return success(message="已退出登录")


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return success(user_view(user))


@router.patch("/me")
def update_me(
    body: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if "username" in body:
        username = str(body["username"]).strip()
        if len(username) < 2 or len(username) > 40:
            raise HTTPException(status_code=422, detail="用户名长度应为 2 到 40 个字符")
        duplicate = db.scalar(select(User).where(User.username == username, User.id != user.id))
        if duplicate:
            raise HTTPException(status_code=409, detail="用户名已被使用")
        user.username = username
    if "avatar" in body:
        user.avatar = str(body["avatar"])[:500]
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return success(user_view(user), "资料已更新")


@router.put("/password")
def change_password(
    body: PasswordChangeInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=422, detail="新密码不能与当前密码相同")
    user.password_hash = hash_password(body.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.execute(
        RefreshToken.__table__.update()
        .where(RefreshToken.user_id == user.id)
        .values(revoked=True)
    )
    db.commit()
    return success(message="密码已修改，其他登录会话已失效")


@router.get("/data-export")
def export_personal_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = db.scalars(
        select(LearningSession).where(LearningSession.user_id == user.id)
    ).all()
    resources = db.scalars(
        select(LearningResource).where(LearningResource.user_id == user.id)
    ).all()
    attempts = db.scalars(
        select(AssessmentAttempt).where(AssessmentAttempt.user_id == user.id)
    ).all()
    feedback = db.scalars(select(Feedback).where(Feedback.user_id == user.id)).all()
    plans = db.scalars(select(LearningPlan).where(LearningPlan.user_id == user.id)).all()
    selections = db.scalars(
        select(TrackSelection).where(TrackSelection.user_id == user.id)
    ).all()
    snapshots = db.scalars(
        select(ProfileSnapshot).where(ProfileSnapshot.user_id == user.id)
    ).all()
    contributions = db.scalars(
        select(KnowledgeContribution).where(KnowledgeContribution.user_id == user.id)
    ).all()
    notifications = db.scalars(
        select(Notification).where(Notification.user_id == user.id)
    ).all()
    service_configs = db.scalars(
        select(ExternalServiceConfig).where(ExternalServiceConfig.user_id == user.id)
    ).all()
    usage_logs = db.scalars(
        select(ExternalUsageLog).where(ExternalUsageLog.user_id == user.id)
    ).all()
    profile = user.profile
    return success(
        {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user": user_view(user),
            "profile": {
                "version": profile.version,
                "background": profile.background,
                "goals": profile.goals,
                "preferences": profile.preferences,
                "dimension_scores": profile.dimension_scores,
                "skill_scores": profile.skill_scores,
            }
            if profile
            else None,
            "route_selections": [
                {
                    "track_code": row.track_code,
                    "score": row.score,
                    "selected": row.selected,
                    "created_at": row.created_at.isoformat(),
                }
                for row in selections
            ],
            "sessions": [
                {
                    "id": row.id,
                    "track_code": row.track_code,
                    "goal": row.goal,
                    "status": row.status,
                    "source_mode": row.source_mode,
                    "source_audit": row.source_audit,
                    "quality_metrics": row.quality_metrics,
                    "created_at": row.created_at.isoformat(),
                }
                for row in sessions
            ],
            "resources": [
                {
                    "id": row.id,
                    "session_id": row.session_id,
                    "type": row.resource_type,
                    "title": row.title,
                    "created_at": row.created_at.isoformat(),
                }
                for row in resources
            ],
            "assessment_attempts": [
                {
                    "id": row.id,
                    "track_code": row.track_code,
                    "score": row.score,
                    "created_at": row.created_at.isoformat(),
                }
                for row in attempts
            ],
            "feedback": [
                {
                    "id": row.id,
                    "type": row.feedback_type,
                    "adjustment": row.adjustment,
                    "created_at": row.created_at.isoformat(),
                }
                for row in feedback
            ],
            "plans": [
                {
                    "id": row.id,
                    "track_code": row.track_code,
                    "goal": row.goal,
                    "progress": row.progress,
                    "version": row.version,
                }
                for row in plans
            ],
            "profile_snapshots": [
                {
                    "version": row.version,
                    "comprehensive_score": row.comprehensive_score,
                    "dimension_scores": row.dimension_scores,
                    "reason": row.reason,
                    "created_at": row.created_at.isoformat(),
                }
                for row in snapshots
            ],
            "knowledge_contributions": [
                {
                    "id": row.id,
                    "track_code": row.track_code,
                    "title": row.title,
                    "source_url": row.source_url,
                    "license_type": row.license_type,
                    "content_version": row.content_version,
                    "status": row.status,
                    "review_notes": row.review_notes,
                    "created_at": row.created_at.isoformat(),
                }
                for row in contributions
            ],
            "notifications": [
                {
                    "id": row.id,
                    "type": row.notification_type,
                    "title": row.title,
                    "content": row.content,
                    "action_url": row.action_url,
                    "read": row.is_read,
                    "created_at": row.created_at.isoformat(),
                }
                for row in notifications
            ],
            "external_services": [
                {
                    "id": row.id,
                    "service_type": row.service_type,
                    "provider": row.provider,
                    "label": row.label,
                    "base_url": row.base_url,
                    "model": row.model,
                    "storage_mode": row.storage_mode,
                    "key_mask": f"****{row.key_last4}" if row.key_last4 else "",
                    "enabled": row.enabled,
                }
                for row in service_configs
            ],
            "external_usage": [
                {
                    "operation": row.operation,
                    "provider": row.provider,
                    "model": row.model,
                    "prompt_tokens": row.prompt_tokens,
                    "completion_tokens": row.completion_tokens,
                    "estimated_cost": row.estimated_cost,
                    "status": row.status,
                    "created_at": row.created_at.isoformat(),
                }
                for row in usage_logs
            ],
        }
    )


@router.delete("/me")
def delete_account(
    body: AccountDeleteInput,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除账号及其业务数据；审核人引用先匿名化，避免破坏他人知识记录。"""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")

    session_ids = select(LearningSession.id).where(LearningSession.user_id == user.id)
    temporary_secrets.clear(user.id)
    db.execute(
        update(KnowledgeContribution)
        .where(KnowledgeContribution.reviewed_by == user.id)
        .values(reviewed_by=None)
    )
    db.execute(delete(ExternalUsageLog).where(ExternalUsageLog.user_id == user.id))
    db.execute(delete(ExternalServiceConfig).where(ExternalServiceConfig.user_id == user.id))
    db.execute(delete(Notification).where(Notification.user_id == user.id))
    db.execute(delete(KnowledgeContribution).where(KnowledgeContribution.user_id == user.id))
    db.execute(delete(AgentEvent).where(AgentEvent.session_id.in_(session_ids)))
    db.execute(delete(LearningResource).where(LearningResource.user_id == user.id))
    db.execute(delete(AssessmentAttempt).where(AssessmentAttempt.user_id == user.id))
    db.execute(delete(Feedback).where(Feedback.user_id == user.id))
    db.execute(delete(LearningPlan).where(LearningPlan.user_id == user.id))
    db.execute(delete(LearningSession).where(LearningSession.user_id == user.id))
    db.execute(delete(ProfileSnapshot).where(ProfileSnapshot.user_id == user.id))
    db.execute(delete(TrackSelection).where(TrackSelection.user_id == user.id))
    db.execute(delete(LearnerProfile).where(LearnerProfile.user_id == user.id))
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    db.execute(delete(User).where(User.id == user.id))
    db.commit()
    response.delete_cookie("refresh_token", path=f"{settings.api_prefix}/auth")
    return success({"deleted": True}, "账号与关联学习数据已删除")
