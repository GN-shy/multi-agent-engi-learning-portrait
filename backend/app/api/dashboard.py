"""由真实持久化数据聚合的首页、Agent 与消息 API。"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, success
from app.core.database import get_db
from app.core.models import (
    AgentEvent,
    AssessmentAttempt,
    LearningPlan,
    LearningResource,
    LearningSession,
    Notification,
    TrackSelection,
    User,
)
from app.domain.catalog import get_catalog

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = user.profile
    selected = db.scalar(
        select(TrackSelection)
        .where(TrackSelection.user_id == user.id, TrackSelection.selected.is_(True))
        .order_by(TrackSelection.created_at.desc())
    )
    active_plan = db.scalar(
        select(LearningPlan)
        .where(LearningPlan.user_id == user.id, LearningPlan.status == "active")
        .order_by(LearningPlan.updated_at.desc())
    )
    latest_session = db.scalar(
        select(LearningSession)
        .where(LearningSession.user_id == user.id)
        .order_by(LearningSession.created_at.desc())
    )
    resource_types = Counter(
        db.scalars(
            select(LearningResource.resource_type).where(LearningResource.user_id == user.id)
        ).all()
    )
    attempts = db.scalars(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.user_id == user.id)
        .order_by(AssessmentAttempt.created_at.desc())
        .limit(8)
    ).all()
    track = (
        get_catalog().track_summary(get_catalog().get_track(selected.track_code))
        if selected
        else None
    )
    return success(
        {
            "user": {"id": user.id, "username": user.username, "avatar": user.avatar},
            "onboarding": {
                "profile_ready": profile is not None,
                "track_selected": selected is not None,
                "first_session_ready": latest_session is not None,
            },
            "profile": {
                "version": profile.version if profile else 0,
                "score": (
                    round(sum(profile.dimension_scores.values()) / len(profile.dimension_scores), 1)
                    if profile and profile.dimension_scores
                    else 0
                ),
                "dimensions": profile.dimension_scores if profile else {},
                "blind_spots": profile.blind_spots[:3] if profile else [],
                "strengths": profile.strengths[:3] if profile else [],
                "weekly_hours": profile.weekly_hours if profile else 0,
            },
            "selected_track": track,
            "route_match": selected.rationale if selected else None,
            "plan": {
                "id": active_plan.id,
                "goal": active_plan.goal,
                "progress": active_plan.progress,
                "phases": active_plan.phases,
            }
            if active_plan
            else None,
            "resources": {
                "total": sum(resource_types.values()),
                "lecture": resource_types["lecture"],
                "practice": resource_types["practice"],
                "assessment": resource_types["assessment"],
                "plan": resource_types["plan"],
            },
            "assessment_trend": [
                {"score": row.score, "date": row.created_at.isoformat()}
                for row in reversed(attempts)
            ],
            "latest_session": {
                "id": latest_session.id,
                "status": latest_session.status,
                "track_code": latest_session.track_code,
                "goal": latest_session.goal,
                "quality_metrics": latest_session.quality_metrics,
            }
            if latest_session
            else None,
        }
    )


@router.get("/agents/status")
def agent_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.scalar(
        select(LearningSession)
        .where(LearningSession.user_id == user.id)
        .order_by(LearningSession.created_at.desc())
    )
    definitions = [
        ("lms", "学情建模 Agent"),
        ("krs", "知识检索 Agent"),
        ("dgs_a", "严谨生成 Agent"),
        ("dgs_b", "项目生成 Agent"),
        ("ars", "仲裁审核 Agent"),
        ("tis", "导学交互 Agent"),
    ]
    event_map = {event.agent_code: event for event in session.events} if session else {}
    items = []
    for code, name in definitions:
        event = event_map.get(code)
        items.append(
            {
                "code": code,
                "name": name,
                "status": event.status if event else "idle",
                "summary": event.summary if event else "等待学习任务",
                "duration_ms": event.duration_ms if event else 0,
                "evidence": event.evidence if event else {},
            }
        )
    return success(
        {
            "items": items,
            "session_id": session.id if session else None,
            "workflow_status": session.status if session else "idle",
        }
    )


@router.get("/agents/tasks")
def agent_tasks(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(AgentEvent)
        .join(LearningSession, AgentEvent.session_id == LearningSession.id)
        .where(LearningSession.user_id == user.id)
        .order_by(AgentEvent.created_at.desc())
        .limit(100)
    ).all()
    return success(
        {
            "items": [
                {
                    "id": row.id,
                    "session_id": row.session_id,
                    "agent_code": row.agent_code,
                    "event_type": row.event_type,
                    "status": row.status,
                    "summary": row.summary,
                    "duration_ms": row.duration_ms,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]
        }
    )


@router.get("/messages")
def messages(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(100)
    ).all()
    items = [
        {
            "id": row.id,
            "type": row.notification_type,
            "title": row.title,
            "content": row.content,
            "action_url": row.action_url,
            "related_id": row.related_id,
            "created_at": row.created_at.isoformat(),
            "read": row.is_read,
        }
        for row in rows
    ]
    if not user.profile:
        items.append(
            {
                "id": "onboarding:profile",
                "type": "onboarding",
                "title": "完成首次能力诊断",
                "content": "画像是路线匹配和个性化生成的必要输入。",
                "action_url": "/onboarding",
                "related_id": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "read": False,
            }
        )
    return success({"items": items})


@router.put("/messages/{message_id}/read")
def mark_message_read(
    message_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(Notification, message_id)
    if not row or row.user_id != user.id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="消息不存在")
    row.is_read = True
    db.commit()
    return success({"id": row.id, "read": True}, "已标记为已读")
