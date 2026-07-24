"""路线探索、技能图谱和反事实比较 API。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, success
from app.core.database import get_db
from app.core.models import LearnerProfile, TrackSelection, User
from app.domain.catalog import CatalogError, get_catalog
from app.domain.profile import ProfileEngine
from app.domain.routing import RouteEngine
from app.schemas import RouteCompareInput, TrackSelectInput

router = APIRouter(prefix="/tracks", tags=["tracks"])


def profile_view(profile: LearnerProfile | None) -> dict:
    if not profile:
        return ProfileEngine().analyze({"weekly_hours": 8})
    return {
        "background": profile.background,
        "goals": profile.goals,
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
    }


@router.get("/tree")
def tree():
    catalog = get_catalog()
    return success({"version": catalog.version, "clusters": catalog.track_tree()})


@router.get("")
def list_tracks():
    catalog = get_catalog()
    return success({"items": [catalog.track_summary(item) for item in catalog.tracks]})


@router.post("/compare")
def compare_tracks(
    body: RouteCompareInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        results = RouteEngine().compare(profile_view(user.profile), body.track_codes or None)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    for result in results:
        db.add(
            TrackSelection(
                user_id=user.id,
                track_code=result["track_code"],
                score=result["score"],
                rationale=result,
                selected=False,
            )
        )
    db.commit()
    return success({"items": results, "recommended": results[0] if results else None})


@router.post("/select")
def select_track(
    body: TrackSelectInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        track = get_catalog().get_track(body.track_code)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.execute(
        delete(TrackSelection).where(
            TrackSelection.user_id == user.id,
            TrackSelection.selected.is_(True),
        )
    )
    match = RouteEngine().compare(profile_view(user.profile), [body.track_code])[0]
    db.add(
        TrackSelection(
            user_id=user.id,
            track_code=body.track_code,
            score=match["score"],
            rationale=match,
            selected=True,
        )
    )
    db.commit()
    return success({"track": get_catalog().track_summary(track), "match": match}, "路线已选择")


@router.get("/history")
def history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(TrackSelection)
        .where(TrackSelection.user_id == user.id)
        .order_by(TrackSelection.created_at.desc())
        .limit(50)
    ).all()
    return success(
        {
            "items": [
                {
                    "id": row.id,
                    "track_code": row.track_code,
                    "score": row.score,
                    "selected": row.selected,
                    "rationale": row.rationale,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]
        }
    )


@router.get("/{track_code}/skill-graph")
def skill_graph(track_code: str):
    try:
        return success(get_catalog().skill_graph(track_code))
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{track_code}/diagnostic")
def diagnostic(track_code: str):
    try:
        return success({"items": get_catalog().diagnostic(track_code)})
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{track_code}")
def detail(track_code: str):
    try:
        catalog = get_catalog()
        track = catalog.get_track(track_code)
        return success(
            {
                **track,
                "graph": catalog.skill_graph(track_code),
                "diagnostic": catalog.diagnostic(track_code),
            }
        )
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
