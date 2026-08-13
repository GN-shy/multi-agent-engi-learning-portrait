"""资源、实操、测试、计划、报告和学习记录 API。"""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape
import re
from typing import Any
from urllib.parse import urlparse

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
from app.domain.assessment import FIELDS, profile_update_weight, score_structured_answer
from app.schemas import AssessmentSubmitInput, CheckinInput

router = APIRouter(tags=["learning"])


EVIDENCE_LABELS = {
    "repository": "代码仓库地址",
    "commit": "提交哈希",
    "test": "测试结果",
    "deployment": "部署地址",
    "screenshot_note": "截图说明",
    "note": "文字说明",
}


def _valid_http_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _review_practice_evidence(
    raw_evidence: list[Any],
    valid_step_ids: set[str],
    completed_step_ids: set[str],
) -> tuple[list[dict[str, Any]], float, float]:
    """Review evidence shape and strength without pretending external URLs were verified."""
    rows: list[dict[str, Any]] = []
    quality_by_step: dict[str, float] = {}
    type_weights = {
        "repository": 0.8,
        "commit": 0.85,
        "test": 1.0,
        "deployment": 0.9,
        "screenshot_note": 0.55,
        "note": 0.35,
    }
    for raw in raw_evidence:
        if isinstance(raw, str):
            item = {"step_id": "", "type": "note", "value": raw}
        elif isinstance(raw, dict):
            item = raw
        else:
            continue
        evidence_type = str(item.get("type", "note")).strip()
        step_id = str(item.get("step_id", "")).strip()
        value = str(item.get("value", "")).strip()
        accepted = True
        reason = "格式有效，已纳入证据质量计算"

        if not value:
            accepted, reason = False, "证据内容为空"
        elif step_id and step_id not in valid_step_ids:
            accepted, reason = False, "关联步骤不存在"
        elif step_id and step_id not in completed_step_ids:
            accepted, reason = False, "该步骤尚未标记完成"
        elif evidence_type in {"repository", "deployment"} and not _valid_http_url(value):
            accepted, reason = False, "链接格式无效，需要 http 或 https 地址"
        elif evidence_type == "commit" and not re.fullmatch(r"[0-9a-fA-F]{7,40}", value):
            accepted, reason = False, "提交哈希应为 7 至 40 位十六进制字符"
        elif evidence_type == "test" and len(value) < 12:
            accepted, reason = False, "测试证据过短，请写明测试数量、结果或关键输出"
        elif evidence_type == "screenshot_note" and len(value) < 10:
            accepted, reason = False, "截图说明过短，请说明画面与验收条件的对应关系"
        elif evidence_type not in type_weights:
            accepted, reason = False, "暂不支持该证据类型"

        rows.append(
            {
                "step_id": step_id or None,
                "type": evidence_type,
                "label": EVIDENCE_LABELS.get(evidence_type, "其他证据"),
                "accepted": accepted,
                "reason": reason,
                "verification_scope": "仅校验格式与描述完整性，未访问外部链接",
            }
        )
        if accepted and step_id:
            quality_by_step[step_id] = max(
                quality_by_step.get(step_id, 0),
                type_weights[evidence_type],
            )
    evidence_coverage = len(quality_by_step) / max(1, len(completed_step_ids))
    evidence_quality = (
        sum(quality_by_step.values()) / max(1, len(completed_step_ids))
        if completed_step_ids
        else 0
    )
    return rows, min(1.0, evidence_coverage), min(1.0, evidence_quality)


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
    steps = resource.content.get("steps", [])
    valid_step_ids = {str(step["id"]) for step in steps}
    completed_steps = {
        str(step_id)
        for step_id in body.get("completed_step_ids", [])
        if str(step_id) in valid_step_ids
    }
    completion = len(completed_steps) / max(1, len(valid_step_ids))
    evidence_review, evidence_coverage, evidence_quality = _review_practice_evidence(
        evidence,
        valid_step_ids,
        completed_steps,
    )
    score = round(
        (completion * 0.5 + evidence_coverage * 0.25 + evidence_quality * 0.25) * 100,
        1,
    )
    has_verifiable_evidence = any(
        row["accepted"] and row["type"] in {"repository", "commit", "test", "deployment"}
        for row in evidence_review
    )
    passed = score >= 70 and has_verifiable_evidence
    feedback = {
        "score": score,
        "completion": round(completion, 3),
        "evidence_completeness": round(evidence_coverage, 3),
        "passed": passed,
        "score_breakdown": {
            "step_completion": round(completion, 3),
            "evidence_coverage": round(evidence_coverage, 3),
            "evidence_quality": round(evidence_quality, 3),
        },
        "evidence_review": evidence_review,
        "verification_notice": "平台已检查证据格式、步骤关联和描述完整性；外部仓库与链接仍需评审者复核。",
        "next_action": (
            "进入分阶段测评，并在项目复盘中说明关键取舍。"
            if passed
            else (
                "请至少补充一条代码、提交、测试或部署证据。"
                if not has_verifiable_evidence
                else "补齐未完成步骤，并让每个已完成步骤都有对应证据。"
            )
        ),
    }
    db.add(
        Feedback(
            user_id=user.id,
            session_id=resource.session_id,
            feedback_type="practice_submission",
            rating=None,
            payload={
                **body,
                "resource_id": resource.id,
                "resource_title": resource.title,
            },
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
    formative_skill_scores = {}
    for question in questions:
        scoring = score_structured_answer(
            body.answers.get(question["id"], {}), float(question["max_score"])
        )
        score = scoring["score"]
        missing_dimensions = scoring["missing_dimensions"]
        skill = get_catalog().get_skill(question["skill_code"])
        missing_labels = [
            FIELDS.get(code, {"label": "成果证据"})["label"] for code in missing_dimensions
        ]
        details.append(
            {
                "question_id": question["id"],
                "skill_code": question["skill_code"],
                "skill_name": skill["name"],
                "score": score,
                "max_score": question["max_score"],
                "verified_score": scoring["verified_score"],
                "rubric_scores": scoring["rubric_scores"],
                "evidence_score": scoring["evidence_score"],
                "evidence_confidence": scoring["evidence_confidence"],
                "evidence_level": scoring["evidence_level"],
                "missing_dimensions": missing_dimensions,
                "guidance": scoring["guidance"],
                "evidence_review": scoring["evidence_review"],
                "integrity_flags": scoring["integrity_flags"],
                "eligible_for_profile_update": scoring["eligible_for_profile_update"],
                "feedback": (
                    "方案完整且成果证据达到画像回写门槛。"
                    if scoring["eligible_for_profile_update"] and score >= 7
                    else "方案回答已形成测评反馈，但需要补充可靠成果证据后再确认能力。"
                    if not scoring["eligible_for_profile_update"]
                    else f"需要补充：{'、'.join(missing_labels) or '更具体的技术细节'}。"
                ),
            }
        )
        formative_skill_scores[question["skill_code"]] = score * 10
        if scoring["eligible_for_profile_update"]:
            skill_updates[question["skill_code"]] = scoring["verified_score"] * 10

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
        feedback={
            "details": details,
            "passed": score >= 70 and bool(skill_updates),
            "formative_score": score,
            "verified_skill_count": len(skill_updates),
        },
    )
    db.add(attempt)
    profile = user.profile
    if profile and skill_updates:
        updated = dict(profile.skill_scores)
        for skill_code, evidence_score in skill_updates.items():
            detail = next(item for item in details if item["skill_code"] == skill_code)
            weight = profile_update_weight(detail["evidence_confidence"])
            updated[skill_code] = round(
                updated.get(skill_code, 0) * (1 - weight) + evidence_score * weight, 1
            )
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
            "passed": score >= 70 and bool(skill_updates),
            "result_type": "verified" if skill_updates else "formative",
            "result_notice": (
                "本次有成果证据的能力项已按证据可信度回写画像。"
                if skill_updates
                else "本次仅提供形成性反馈；未检测到达到门槛的成果证据，能力画像未被抬高。"
            ),
            "details": details,
            "skill_updates": skill_updates,
            "formative_skill_scores": formative_skill_scores,
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
    def phase_task_ids(phase: dict[str, Any]) -> set[str]:
        if phase.get("tasks"):
            return {
                f"{phase['id']}:{task['id']}"
                for task in phase["tasks"]
            }
        return {
            f"{phase['id']}:{skill}"
            for skill in phase.get("skills", [])
        }

    valid_ids = set().union(*(phase_task_ids(phase) for phase in plan.phases))
    accepted = sorted(set(body.completed_task_ids) & valid_ids)
    checkins = list(plan.checkins)
    checkins.append(
        {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "completed_task_ids": accepted,
            "feedback_type": body.feedback_type,
            "hours_spent": body.hours_spent,
            "note": body.note,
        }
    )
    plan.checkins = checkins
    completed = set(item for record in checkins for item in record["completed_task_ids"])
    plan.progress = round(len(completed) / max(1, len(valid_ids)) * 100, 1)
    phases = []
    for phase in plan.phases:
        phase_copy = dict(phase)
        phase_tasks = phase_task_ids(phase)
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
        {
            "progress": plan.progress,
            "phases": phases,
            "accepted_task_ids": accepted,
            "feedback_saved": body.feedback_type,
            "recalibration_recommended": body.feedback_type != "normal",
        },
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
    practice_submissions = db.scalars(
        select(Feedback)
        .where(
            Feedback.user_id == user.id,
            Feedback.feedback_type == "practice_submission",
        )
        .order_by(Feedback.created_at.desc())
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
    labels = {
        "programming_and_algorithms": "编程与算法",
        "systems_foundation": "系统基础",
        "software_engineering": "软件工程",
        "architecture_and_security": "架构与安全",
        "engineering_delivery": "工程交付",
        "route_specific": "方向专项",
        "chosen_track": "推荐方向",
        "track_code": "方向",
        "reasons": "推荐理由",
        "skill_gaps": "能力差距",
        "score": "匹配分",
        "total": "质量总分",
        "knowledge_coverage": "知识覆盖率",
        "citation_coverage": "引用覆盖率",
        "citation_integrity": "引用完整性",
        "profile_fit": "画像适配度",
        "prerequisite_violations": "前置冲突",
        "hallucination_risk": "未引用风险估计",
    }

    def render_value(value: Any, key: str = "") -> str:
        if isinstance(value, dict):
            rows = "".join(
                f"<div class='evidence-row'><b>{escape(labels.get(str(child_key), str(child_key)))}</b>"
                f"<span>{render_value(child_value, str(child_key))}</span></div>"
                for child_key, child_value in value.items()
            )
            return f"<div class='evidence-grid'>{rows}</div>"
        if isinstance(value, list):
            if not value:
                return "<span class='muted'>暂无</span>"
            return "<ul>" + "".join(f"<li>{render_value(item)}</li>" for item in value) + "</ul>"
        if isinstance(value, float) and key in {
            "knowledge_coverage",
            "citation_coverage",
            "citation_integrity",
            "profile_fit",
            "hallucination_risk",
        }:
            return f"{round(value * 100, 1)}%"
        return escape(str(value if value not in {None, ""} else "暂无"))

    dimensions = "".join(
        f"<li><span>{escape(labels.get(name, name))}</span><b>{score}</b></li>"
        for name, score in report["dimensions"].items()
    )
    blind_spots = "".join(
        f"<li>{escape(item['name'])}（{item['score']}）</li>"
        for item in report["blind_spots"]
    )
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <title>工学智链学习报告</title><style>
    body{{font-family:system-ui;max-width:900px;margin:40px auto;color:#17233d;line-height:1.7;background:#f5f8fd}}
    .card{{border:1px solid #dbe5f4;border-radius:16px;padding:22px;margin:16px 0;background:white}}
    .hero{{padding:28px;border-radius:20px;color:white;background:linear-gradient(135deg,#2458d3,#6b4bd9)}}
    .hero h1{{color:white;margin:0}}.hero p{{margin:7px 0 0;opacity:.84}}
    .score{{font-size:42px;color:#2458d3}}.dimensions{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;padding:0;list-style:none}}
    .dimensions li,.evidence-row{{display:flex;justify-content:space-between;gap:16px;padding:10px 12px;border-radius:10px;background:#f6f9ff}}
    .evidence-grid{{display:grid;gap:8px}}.evidence-row>span{{text-align:right;max-width:70%}}ul{{padding-left:22px}}.muted{{color:#78849a}}
    h1,h2{{color:#2458d3}}.no-print{{border:0;border-radius:10px;padding:10px 16px;background:#2458d3;color:white;cursor:pointer;margin-bottom:14px}}
    @media print{{body{{margin:0;background:white}}.no-print{{display:none}}.card{{break-inside:avoid}}}}
    </style></head><body>
    <button class="no-print" onclick="window.print()">打印 / 另存为 PDF</button>
    <section class="hero"><h1>工学智链 · {escape(user.username)} 的学习报告</h1>
    <p>生成时间：{escape(report['generated_at'])} · 画像版本 V{report['profile_version']}</p></section>
    <div class="card"><h2>综合能力 <span class="score">{report['comprehensive_score']}</span></h2><ul class="dimensions">{dimensions}</ul></div>
    <div class="card"><h2>关键盲区</h2><ul>{blind_spots}</ul></div>
    <div class="card"><h2>路线依据</h2>{render_value(report['route'])}</div>
    <div class="card"><h2>内容质量证据</h2>
      <p class="muted">“未引用风险估计”仅由引用覆盖推算，不代表独立事实核验结果。</p>
      {render_value(report['quality_metrics'])}
    </div>
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
    practice_submissions = db.scalars(
        select(Feedback)
        .where(
            Feedback.user_id == user.id,
            Feedback.feedback_type == "practice_submission",
        )
        .order_by(Feedback.created_at.desc())
        .limit(limit)
    ).all()
    session_ids = {item.session_id for item in practice_submissions if item.session_id}
    sessions_by_id = {
        row.id: row
        for row in (
            db.scalars(
                select(LearningSession).where(LearningSession.id.in_(session_ids))
            ).all()
            if session_ids
            else []
        )
    }
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
            "score": item.score,
            "passed": item.score >= 70,
            "created_at": item.created_at.isoformat(),
        }
        for item in attempts
    ] + [
        {
            "id": item.id,
            "type": "practice_submission",
            "title": item.payload.get("resource_title", "项目实操证据提交"),
            "track_code": sessions_by_id.get(item.session_id).track_code
            if sessions_by_id.get(item.session_id)
            else "",
            "score": (item.adjustment or {}).get("score"),
            "passed": (item.adjustment or {}).get("passed", False),
            "created_at": item.created_at.isoformat(),
        }
        for item in practice_submissions
    ]
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return success({"items": items[:limit]})
