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
from app.schemas import ProfileInput

router = APIRouter(prefix="/profiles", tags=["profiles"])


def serialize(profile: LearnerProfile) -> dict:
    return {
        "id": profile.id,
        "version": profile.version,
        "background": profile.background,
        "learning_goals": profile.goals,
        "preferences": profile.preferences,
        "weekly_hours": profile.weekly_hours,
        "learning_style": profile.learning_style,
        "knowledge_breadth": profile.knowledge_breadth,
        "knowledge_depth": profile.knowledge_depth,
        "engineering_maturity": profile.engineering_maturity,
        "cognitive_load": profile.cognitive_load,
        "dimension_scores": profile.dimension_scores,
        "skill_scores": profile.skill_scores,
        "blind_spots": profile.blind_spots,
        "strengths": profile.strengths,
        "comprehensive_score": (
            round(sum(profile.dimension_scores.values()) / len(profile.dimension_scores), 1)
            if profile.dimension_scores
            else 0
        ),
        "updated_at": profile.updated_at.isoformat(),
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
