"""学习画像分析、证据更新与趋势 API。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, success
from app.core.database import get_db
from app.core.models import LearnerProfile, ProfileSnapshot, TrackSelection, User
from app.domain.profile import ProfileEngine
from app.domain.routing import extract_decision_context, visible_preferences
from app.schemas import ProfileInput

router = APIRouter(prefix="/profiles", tags=["profiles"])

DIMENSION_DEFAULTS = {
    "programming_and_algorithms": 0.0,
    "systems_foundation": 0.0,
    "software_engineering": 0.0,
    "architecture_and_security": 0.0,
    "engineering_delivery": 0.0,
    "route_specific": 0.0,
}


def _analysis_summary(profile: LearnerProfile, dimensions: dict, skills: dict) -> dict:
    ordered = sorted(dimensions.items(), key=lambda item: item[1], reverse=True)
    strongest = ordered[0] if ordered else ("", 0)
    weakest = ordered[-1] if ordered else ("", 0)
    evidence_count = sum(float(score or 0) > 0 for score in skills.values())
    confidence = "高" if evidence_count >= 20 else "中" if evidence_count >= 8 else "待补证据"
    next_actions = []
    if evidence_count < 8:
        next_actions.append("先完成通用能力诊断，避免路线推荐过度依赖主观自评。")
    if profile.blind_spots:
        names = "、".join(item.get("name", "待提升能力") for item in profile.blind_spots[:3])
        next_actions.append(f"优先补齐 {names}，并用代码、测试或项目结果证明掌握。")
    next_actions.append("选择 1–3 条目标岗位路线，生成去重后的阶段学习计划。")
    return {
        "overview": (
            f"当前画像版本为 V{profile.version or 1}，已有 {evidence_count} 项能力证据，"
            f"画像可信度为“{confidence}”。"
        ),
        "strongest_dimension": {"code": strongest[0], "score": strongest[1]},
        "weakest_dimension": {"code": weakest[0], "score": weakest[1]},
        "evidence_count": evidence_count,
        "confidence_level": confidence,
        "next_actions": next_actions,
    }


def serialize(profile: LearnerProfile) -> dict:
    dimensions = {**DIMENSION_DEFAULTS, **(profile.dimension_scores or {})}
    skills = profile.skill_scores or {}
    return {
        "id": profile.id,
        "version": profile.version,
        "background": profile.background or "",
        "learning_goals": list(profile.goals or []),
        "preferences": visible_preferences(profile.preferences),
        "decision_context": extract_decision_context(profile.preferences),
        "weekly_hours": int(profile.weekly_hours or 8),
        "learning_style": profile.learning_style or "balanced",
        "knowledge_breadth": float(profile.knowledge_breadth or 0),
        "knowledge_depth": float(profile.knowledge_depth or 0),
        "engineering_maturity": float(profile.engineering_maturity or 0),
        "cognitive_load": float(profile.cognitive_load or 0),
        "dimension_scores": dimensions,
        "skill_scores": skills,
        "blind_spots": list(profile.blind_spots or []),
        "strengths": list(profile.strengths or []),
        "comprehensive_score": (
            round(sum(dimensions.values()) / len(dimensions), 1)
            if dimensions
            else 0
        ),
        "analysis_summary": _analysis_summary(profile, dimensions, skills),
        "updated_at": (
            profile.updated_at.isoformat()
            if profile.updated_at
            else datetime.now(timezone.utc).isoformat()
        ),
    }


@router.get("/me")
def get_profile(user: User = Depends(get_current_user)):
    if not user.profile:
        raise HTTPException(status_code=404, detail="尚未建立学习画像")
    return success(serialize(user.profile))


@router.put("/me/analyze")
def analyze_profile(
    body: ProfileInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    selected = db.scalar(
        select(TrackSelection)
        .where(TrackSelection.user_id == user.id, TrackSelection.selected.is_(True))
        .order_by(TrackSelection.created_at.desc())
    )
    result = ProfileEngine().analyze(body.model_dump(), selected.track_code if selected else None)
    profile = user.profile
    if not profile:
        profile = LearnerProfile(user_id=user.id)
        db.add(profile)
    profile.background = result["background"]
    profile.goals = result["goals"]
    profile.preferences = result["preferences"]
    profile.weekly_hours = result["weekly_hours"]
    profile.learning_style = result["learning_style"]
    profile.knowledge_breadth = result["knowledge_breadth"]
    profile.knowledge_depth = result["knowledge_depth"]
    profile.engineering_maturity = result["engineering_maturity"]
    profile.cognitive_load = result["cognitive_load"]
    profile.dimension_scores = result["dimension_scores"]
    profile.skill_scores = result["skill_scores"]
    profile.blind_spots = result["blind_spots"]
    profile.strengths = result["strengths"]
    profile.version = (profile.version or 0) + 1
    profile.updated_at = datetime.now(timezone.utc)
    db.flush()
    db.add(
        ProfileSnapshot(
            user_id=user.id,
            version=profile.version,
            comprehensive_score=result["comprehensive_score"],
            dimension_scores=result["dimension_scores"],
            skill_scores=result["skill_scores"],
            reason="analysis",
        )
    )
    db.commit()
    db.refresh(profile)
    return success(serialize(profile), "画像分析完成")


@router.get("/me/trend")
def profile_trend(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(ProfileSnapshot)
        .where(ProfileSnapshot.user_id == user.id)
        .order_by(ProfileSnapshot.created_at.asc())
        .limit(30)
    ).all()
    if not rows and user.profile:
        current = serialize(user.profile)
        return success(
            {
                "items": [
                    {
                        "version": current["version"],
                        "score": current["comprehensive_score"],
                        "dimensions": current["dimension_scores"],
                        "reason": "current_profile_backfill",
                        "created_at": current["updated_at"],
                    }
                ],
                "backfilled": True,
                "notice": "历史版本缺少快照，已用当前画像建立趋势起点；后续分析、评测和反馈会持续追加。",
            }
        )
    return success(
        {
            "items": [
                {
                    "version": row.version,
                    "score": row.comprehensive_score,
                    "dimensions": row.dimension_scores,
                    "reason": row.reason,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]
        }
    )
