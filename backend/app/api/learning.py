"""资源、实操、测试、计划、报告和学习记录 API。"""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, success
from app.core.database import get_db
from app.core.models import (
    AssessmentAttempt,
    Feedback,
    LearningPlan,
    LearningResource,
    LearningSession,
    ProfileSnapshot,
    TrackSelection,
    User,
)
from app.domain.catalog import get_catalog
from app.schemas import AssessmentSubmitInput, CheckinInput

router = APIRouter(tags=["learning"])


def _resource_view(item: LearningResource, detail: bool = False) -> dict[str, Any]:
    data = {
        "id": item.id,
        "session_id": item.session_id,
        "track_code": item.track_code,
        "resource_type": item.resource_type,
        "title": item.title,
        "version": item.version,
        "source_traces": item.source_traces,
        "created_at": item.created_at.isoformat(),
    }
    if detail:
        data["content"] = item.content
    return data


@router.get("/resources")
def list_resources(
    resource_type: str | None = None,
    track_code: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = select(LearningResource).where(LearningResource.user_id == user.id)
    if resource_type:
        statement = statement.where(LearningResource.resource_type == resource_type)
    if track_code:
        statement = statement.where(LearningResource.track_code == track_code)
    rows = db.scalars(statement.order_by(LearningResource.created_at.desc())).all()
    return success({"items": [_resource_view(row) for row in rows], "total": len(rows)})


@router.get("/resources/{resource_id}")
def resource_detail(
    resource_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(LearningResource, resource_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="学习资源不存在")
    return success(_resource_view(row, detail=True))


@router.post("/practice/{resource_id}/submit")
def submit_practice(
    resource_id: str,
    body: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resource = db.get(LearningResource, resource_id)
    if (
        not resource
        or resource.user_id != user.id
        or resource.resource_type != "practice"
    ):
        raise HTTPException(status_code=404, detail="实操任务不存在")
    evidence = body.get("evidence", [])
    completed_steps = body.get("completed_step_ids", [])
    total_steps = len(resource.content.get("steps", []))
    completion = len(set(completed_steps)) / max(1, total_steps)
    evidence_score = min(1.0, len(evidence) / max(1, total_steps))
    score = round((completion * 0.65 + evidence_score * 0.35) * 100, 1)
    feedback = {
        "score": score,
        "completion": round(completion, 3),
        "evidence_completeness": round(evidence_score, 3),
        "passed": score >= 70,
        "next_action": (
            "进入分阶测试并提交项目复盘"
            if score >= 70
            else "补齐未完成步骤及对应运行证据"
        ),
    }
    db.add(
        Feedback(
            user_id=user.id,
            session_id=resource.session_id,
            feedback_type="practice_submission",
            rating=None,
            payload=body,
            adjustment=feedback,
        )
    )
    db.commit()
    return success(feedback, "实操证据已评估")


@router.post("/assessments/{resource_id}/submit")
def submit_assessment(
    resource_id: str,
    body: AssessmentSubmitInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resource = db.get(LearningResource, resource_id)
    if (
        not resource
        or resource.user_id != user.id
        or resource.resource_type != "assessment"
    ):
        raise HTTPException(status_code=404, detail="测试不存在")
    questions = resource.content.get("questions", [])
    details = []
    skill_updates = {}
    for question in questions:
        answer = str(body.answers.get(question["id"], "")).strip()
        length_score = min(4.0, len(answer) / 35)
        evidence_terms = ["测试", "验证", "边界", "失败", "指标", "运行"]
        term_score = min(3.0, sum(term in answer for term in evidence_terms))
        structure_score = (
            3.0
            if any(mark in answer for mark in ["1.", "一、", "\n", "标准"])
            else 1.0
        )
        score = round(min(question["max_score"], length_score + term_score + structure_score), 1)
        details.append(
            {
                "question_id": question["id"],
                "skill_code": question["skill_code"],
                "score": score,
                "max_score": question["max_score"],
                "feedback": (
                    "证据与通过标准较完整"
                    if score >= 7
                    else "需要补充可执行步骤、边界条件和客观通过标准"
                ),
            }
        )
        skill_updates[question["skill_code"]] = score * 10

    total = sum(item["score"] for item in details)
    maximum = sum(item["max_score"] for item in details)
    score = round(total / max(1, maximum) * 100, 1)
    attempt = AssessmentAttempt(
        user_id=user.id,
        session_id=resource.session_id,
        track_code=resource.track_code,
        answers=body.answers,
        score=score,
        skill_updates=skill_updates,
        feedback={"details": details, "passed": score >= 70},
    )
    db.add(attempt)
    profile = user.profile
    if profile:
        updated = dict(profile.skill_scores)
        for skill_code, evidence_score in skill_updates.items():
            updated[skill_code] = round(updated.get(skill_code, 0) * 0.7 + evidence_score * 0.3, 1)
        profile.skill_scores = updated
        profile.version += 1
        profile.updated_at = datetime.now(timezone.utc)
        comprehensive = (
            sum(profile.dimension_scores.values()) / len(profile.dimension_scores)
            if profile.dimension_scores
            else 0
        )
        db.add(
            ProfileSnapshot(
                user_id=user.id,
                version=profile.version,
                comprehensive_score=round(comprehensive, 1),
                dimension_scores=profile.dimension_scores,
                skill_scores=updated,
                reason="assessment",
            )
        )
    db.commit()
    db.refresh(attempt)
    return success(
        {
            "attempt_id": attempt.id,
            "score": score,
            "passed": score >= 70,
            "details": details,
            "skill_updates": skill_updates,
        },
        "测试已评分并回写画像",
    )


@router.get("/plans/current")
def current_plan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(
        select(LearningPlan)
        .where(LearningPlan.user_id == user.id, LearningPlan.status == "active")
        .order_by(LearningPlan.updated_at.desc())
    )
    if not row:
        raise HTTPException(status_code=404, detail="尚未生成学习计划")
    return success(
        {
            "id": row.id,
            "track_code": row.track_code,
            "track_name": get_catalog().get_track(row.track_code)["name"],
            "goal": row.goal,
            "phases": row.phases,
            "progress": row.progress,
            "version": row.version,
            "checkins": row.checkins,
            "updated_at": row.updated_at.isoformat(),
        }
    )


@router.post("/plans/{plan_id}/checkin")
def checkin(
    plan_id: str,
    body: CheckinInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.get(LearningPlan, plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="学习计划不存在")
    valid_ids = {
        f"{phase['id']}:{skill}"
        for phase in plan.phases
        for skill in phase.get("skills", [])
    }
    accepted = sorted(set(body.completed_task_ids) & valid_ids)
    checkins = list(plan.checkins)
    checkins.append(
        {"date": datetime.now(timezone.utc).date().isoformat(), "completed_task_ids": accepted}
    )
    plan.checkins = checkins
    completed = set(item for record in checkins for item in record["completed_task_ids"])
    plan.progress = round(len(completed) / max(1, len(valid_ids)) * 100, 1)
    phases = []
    for phase in plan.phases:
        phase_copy = dict(phase)
        phase_tasks = {f"{phase['id']}:{skill}" for skill in phase.get("skills", [])}
        done = len(phase_tasks & completed)
        phase_copy["progress"] = round(done / max(1, len(phase_tasks)) * 100, 1)
        phase_copy["status"] = (
            "completed"
            if phase_copy["progress"] == 100
            else ("active" if done > 0 or phase["id"] == "phase-1" else "pending")
        )
        phases.append(phase_copy)
    plan.phases = phases
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    return success(
        {"progress": plan.progress, "phases": phases, "accepted_task_ids": accepted},
        "打卡已保存",
    )


def _report_data(user: User, db: Session) -> dict[str, Any]:
    profile = user.profile
    session = db.scalar(
        select(LearningSession)
        .where(LearningSession.user_id == user.id, LearningSession.status == "completed")
        .order_by(LearningSession.completed_at.desc())
    )
    attempts = db.scalars(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.user_id == user.id)
        .order_by(AssessmentAttempt.created_at.desc())
        .limit(10)
    ).all()
    selected = db.scalar(
        select(TrackSelection)
        .where(TrackSelection.user_id == user.id, TrackSelection.selected.is_(True))
        .order_by(TrackSelection.created_at.desc())
    )
    if not profile:
        raise HTTPException(status_code=409, detail="请先建立学习画像")
    route = selected.rationale if selected else (session.route_snapshot if session else {})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user": {"id": user.id, "username": user.username},
        "profile_version": profile.version,
        "comprehensive_score": (
            round(sum(profile.dimension_scores.values()) / len(profile.dimension_scores), 1)
            if profile.dimension_scores
            else 0
        ),
        "dimensions": profile.dimension_scores,
        "blind_spots": profile.blind_spots,
        "strengths": profile.strengths,
        "route": route,
        "assessment_trend": [
            {"score": item.score, "date": item.created_at.isoformat()}
            for item in reversed(attempts)
        ],
        "quality_metrics": session.quality_metrics if session else {},
        "next_actions": (
            session.final_output.get("plan", [])[:2] if session and session.final_output else []
        ),
    }


@router.get("/reports/latest")
def latest_report(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return success(_report_data(user, db))


@router.get("/reports/latest/print")
def printable_report(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _report_data(user, db)
    dimensions = "".join(
        f"<li>{escape(name)}：{score}</li>" for name, score in report["dimensions"].items()
    )
    blind_spots = "".join(
        f"<li>{escape(item['name'])}（{item['score']}）</li>"
        for item in report["blind_spots"]
    )
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <title>工学智链学习报告</title><style>
    body{{font-family:system-ui;max-width:900px;margin:40px auto;color:#17233d;line-height:1.7}}
    .card{{border:1px solid #dbe5f4;border-radius:16px;padding:22px;margin:16px 0}}
    h1,h2{{color:#2458d3}}@media print{{body{{margin:0}}.no-print{{display:none}}}}
    </style></head><body>
    <button class="no-print" onclick="window.print()">打印 / 另存为 PDF</button>
    <h1>工学智链 · {escape(user.username)} 的学习报告</h1>
    <p>生成时间：{escape(report['generated_at'])}</p>
    <div class="card"><h2>综合能力 {report['comprehensive_score']}</h2><ul>{dimensions}</ul></div>
    <div class="card"><h2>关键盲区</h2><ul>{blind_spots}</ul></div>
    <div class="card"><h2>路线依据</h2><pre>{escape(str(report['route']))}</pre></div>
    <div class="card"><h2>质量证据</h2><pre>{escape(str(report['quality_metrics']))}</pre></div>
    </body></html>"""
    return Response(content=html, media_type="text/html")


@router.get("/records")
def records(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resources = db.scalars(
        select(LearningResource)
        .where(LearningResource.user_id == user.id)
        .order_by(LearningResource.created_at.desc())
        .limit(limit)
    ).all()
    attempts = db.scalars(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.user_id == user.id)
        .order_by(AssessmentAttempt.created_at.desc())
        .limit(limit)
    ).all()
    items = [
        {
            "id": item.id,
            "type": f"resource:{item.resource_type}",
            "title": item.title,
            "track_code": item.track_code,
            "created_at": item.created_at.isoformat(),
        }
        for item in resources
    ] + [
        {
            "id": item.id,
            "type": "assessment",
            "title": f"{get_catalog().get_track(item.track_code)['name']} 测试 · {item.score} 分",
            "track_code": item.track_code,
            "created_at": item.created_at.isoformat(),
        }
        for item in attempts
    ]
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return success({"items": items[:limit]})
