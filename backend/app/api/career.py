"""目标岗位、任务证据与动态路线版本 API。"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from statistics import mean
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, success
from app.core.database import get_db
from app.core.models import (
    CareerTarget,
    EvidenceArtifact,
    LearningPlan,
    ProfileSnapshot,
    RouteRevision,
    User,
)
from app.domain.career import build_revision, job_gap_analysis, parse_job_description
from app.domain.profile import DIMENSION_SKILLS
from app.schemas import (
    CareerTargetInput,
    JobParseInput,
    RecalibrationInput,
    RevisionDecisionInput,
    TaskEvidenceInput,
)

router = APIRouter(tags=["career-loop"])


def _target_view(row: CareerTarget) -> dict[str, Any]:
    return {
        "id": row.id, "title": row.title, "company": row.company, "city": row.city,
        "education": row.education, "experience": row.experience, "salary": row.salary,
        "source_url": row.source_url, "raw_text": row.raw_text,
        "required_skills": row.required_skills, "responsibilities": row.responsibilities,
        "analysis": row.analysis, "active": row.active,
        "created_at": row.created_at.isoformat(), "updated_at": row.updated_at.isoformat(),
    }


def _revision_view(row: RouteRevision) -> dict[str, Any]:
    return {
        "id": row.id, "plan_id": row.plan_id, "from_version": row.from_version,
        "to_version": row.to_version, "trigger": row.trigger, "reason": row.reason,
        "status": row.status, "changes": row.changes,
        "old_phases": row.old_phases, "new_phases": row.new_phases,
        "created_at": row.created_at.isoformat(),
        "decided_at": row.decided_at.isoformat() if row.decided_at else None,
    }


def _artifact_view(row: EvidenceArtifact) -> dict[str, Any]:
    return {
        "id": row.id, "plan_id": row.plan_id, "task_id": row.task_id,
        "evidence_type": row.evidence_type, "value": row.value,
        "description": row.description, "status": row.status, "score": row.score,
        "verification": row.verification, "skill_updates": row.skill_updates,
        "created_at": row.created_at.isoformat(),
    }


def _active_plan(user_id: str, db: Session) -> LearningPlan | None:
    return db.scalar(
        select(LearningPlan)
        .where(LearningPlan.user_id == user_id, LearningPlan.status == "active")
        .order_by(LearningPlan.updated_at.desc())
    )


def _task(plan: LearningPlan, task_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for phase in plan.phases:
        for task in phase.get("tasks", []):
            if str(task.get("id")) == task_id or f"{phase.get('id')}:{task.get('id')}" == task_id:
                return phase, task
        if task_id in {f"{phase.get('id')}:{skill}" for skill in phase.get("skills", [])}:
            skill = task_id.split(":", 1)[1]
            return phase, {"id": skill, "title": skill, "skill_code": skill}
    raise HTTPException(status_code=404, detail="学习任务不存在")


def _create_revision(
    db: Session,
    user_id: str,
    plan: LearningPlan,
    trigger: str,
    *,
    note: str = "",
    weekly_hours: int | None = None,
    target_skills: list[dict[str, Any]] | None = None,
    validated_skills: set[str] | None = None,
) -> RouteRevision:
    db.execute(
        update(RouteRevision)
        .where(RouteRevision.plan_id == plan.id, RouteRevision.status == "pending")
        .values(status="superseded", decided_at=datetime.now(timezone.utc))
    )
    new_phases, changes, reason = build_revision(
        plan.phases, trigger, note=note, weekly_hours=weekly_hours,
        target_skills=target_skills, validated_skills=validated_skills,
    )
    row = RouteRevision(
        user_id=user_id, plan_id=plan.id, from_version=plan.version,
        to_version=plan.version + 1, trigger=trigger, reason=reason,
        old_phases=plan.phases, new_phases=new_phases, changes=changes,
    )
    db.add(row)
    db.flush()
    return row


@router.post("/career/jobs/parse")
def parse_job(
    body: JobParseInput,
    user: User = Depends(get_current_user),
):
    result = parse_job_description(body.raw_text, body.source_url)
    result["gap_analysis"] = job_gap_analysis(
        result["required_skills"], user.profile.skill_scores if user.profile else {}
    )
    return success(result, "岗位要求已解析，请确认后再影响路线")


@router.post("/career/targets")
def confirm_target(
    body: CareerTargetInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not body.required_skills:
        raise HTTPException(status_code=422, detail="目标岗位至少需要一个明确技术要求")
    db.execute(update(CareerTarget).where(CareerTarget.user_id == user.id, CareerTarget.active.is_(True)).values(active=False))
    gap = job_gap_analysis(body.required_skills, user.profile.skill_scores if user.profile else {})
    parsed = parse_job_description(body.raw_text, body.source_url)
    row = CareerTarget(
        user_id=user.id, title=body.title.strip(), company=body.company.strip(),
        city=body.city.strip(), education=body.education.strip(), experience=body.experience.strip(),
        salary=body.salary.strip(), source_url=body.source_url.strip(), raw_text=body.raw_text.strip(),
        required_skills=body.required_skills, responsibilities=body.responsibilities,
        analysis={"gap_analysis": gap, "confidence": parsed["confidence"], "suggested_tracks": parsed["suggested_tracks"]},
    )
    db.add(row)
    plan = _active_plan(user.id, db)
    revision = _create_revision(db, user.id, plan, "job_target", target_skills=gap["priority_skills"]) if plan else None
    db.commit()
    db.refresh(row)
    return success({"target": _target_view(row), "gap_analysis": gap, "revision": _revision_view(revision) if revision else None}, "目标岗位已确认")


@router.get("/career/targets/current")
def current_target(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(select(CareerTarget).where(CareerTarget.user_id == user.id, CareerTarget.active.is_(True)).order_by(CareerTarget.updated_at.desc()))
    return success(_target_view(row) if row else None)


@router.get("/career/targets")
def target_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(CareerTarget).where(CareerTarget.user_id == user.id).order_by(CareerTarget.created_at.desc()).limit(30)).all()
    return success({"items": [_target_view(row) for row in rows]})


def _validate_evidence(kind: str, value: str, description: str) -> tuple[float, dict[str, Any]]:
    value = value.strip()
    checks = {"non_empty": bool(value), "format_valid": False, "description_present": len(description.strip()) >= 8}
    score = 25.0 if checks["description_present"] else 10.0
    note = ""
    if kind in {"repository", "deployment", "document"}:
        parsed = urlparse(value)
        checks["format_valid"] = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        score += 60 if checks["format_valid"] else 0
        note = "只验证 URL 格式，未冒充外部仓库或部署可访问性检查"
    elif kind == "commit":
        checks["format_valid"] = bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", value))
        score += 65 if checks["format_valid"] else 0
        note = "只验证提交哈希格式，需结合仓库链接复核归属"
    elif kind == "test":
        checks["format_valid"] = len(value) >= 16 and any(word in value.lower() for word in ("通过", "pass", "passed", "测试", "test"))
        checks["has_result_detail"] = bool(re.search(r"\d+", value))
        score += 45 if checks["format_valid"] else 0
        score += 20 if checks["has_result_detail"] else 0
        note = "校验测试结果描述完整性，未在沙箱中执行用户代码"
    else:
        checks["format_valid"] = len(value) >= 12
        score += 45 if checks["format_valid"] else 0
        note = "文字或截图说明只能作为辅助证据，不能单独证明代码能力"
    return min(100.0, score), {"checks": checks, "scope": note, "verified_at": datetime.now(timezone.utc).isoformat()}


def _refresh_plan_progress(plan: LearningPlan, completed_task_id: str) -> None:
    checkins = list(plan.checkins or [])
    checkins.append({"date": datetime.now(timezone.utc).date().isoformat(), "completed_task_ids": [completed_task_id], "source": "evidence"})
    plan.checkins = checkins
    completed = {item for record in checkins for item in record.get("completed_task_ids", [])}
    all_ids = []
    phases = []
    for phase in plan.phases:
        copy_phase = dict(phase)
        task_ids = [f"{phase['id']}:{task.get('id')}" for task in phase.get("tasks", [])] or [f"{phase['id']}:{skill}" for skill in phase.get("skills", [])]
        all_ids.extend(task_ids)
        done = len(set(task_ids) & completed)
        copy_phase["progress"] = round(done / max(1, len(task_ids)) * 100, 1)
        copy_phase["status"] = "completed" if copy_phase["progress"] == 100 else ("active" if done or phase.get("status") == "active" else "pending")
        phases.append(copy_phase)
    plan.phases = phases
    plan.progress = round(len(set(all_ids) & completed) / max(1, len(all_ids)) * 100, 1)


@router.post("/plans/{plan_id}/tasks/{task_id:path}/evidence")
def submit_task_evidence(
    plan_id: str,
    task_id: str,
    body: TaskEvidenceInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.get(LearningPlan, plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="学习计划不存在")
    phase, task = _task(plan, task_id)
    canonical_task_id = f"{phase['id']}:{task.get('id')}"
    scores = []
    artifacts = []
    strong = False
    for item in body.evidence:
        score, verification = _validate_evidence(item.evidence_type, item.value, item.description)
        strong = strong or (score >= 70 and item.evidence_type in {"repository", "commit", "test", "deployment", "document"})
        artifact = EvidenceArtifact(
            user_id=user.id, plan_id=plan.id, task_id=canonical_task_id,
            evidence_type=item.evidence_type, value=item.value.strip(), description=item.description.strip(),
            status="accepted" if score >= 60 else "needs_revision", score=score,
            verification=verification, skill_updates={},
        )
        db.add(artifact)
        artifacts.append(artifact)
        scores.append(score)
    total = round(mean(scores), 1)
    passed = total >= 70 and strong
    skill_code = str(task.get("skill_code", ""))
    profile_update = None
    revision = None
    if passed and user.profile and skill_code:
        updated = dict(user.profile.skill_scores or {})
        old_score = float(updated.get(skill_code, 0) or 0)
        new_score = round(old_score * .7 + total * .3, 1)
        updated[skill_code] = new_score
        user.profile.skill_scores = updated
        dimensions = dict(user.profile.dimension_scores or {})
        matched_dimension = next((name for name, codes in DIMENSION_SKILLS.items() if skill_code in codes), "route_specific")
        related = [float(updated.get(code, 0) or 0) for code in DIMENSION_SKILLS.get(matched_dimension, [skill_code]) if float(updated.get(code, 0) or 0) > 0]
        dimensions[matched_dimension] = round(mean(related), 1) if related else new_score
        if matched_dimension == "route_specific":
            dimensions["route_specific"] = new_score
        user.profile.dimension_scores = dimensions
        user.profile.version += 1
        user.profile.updated_at = datetime.now(timezone.utc)
        comprehensive = mean(dimensions.values()) if dimensions else 0
        db.add(ProfileSnapshot(user_id=user.id, version=user.profile.version, comprehensive_score=round(comprehensive, 1), dimension_scores=dimensions, skill_scores=updated, reason="verified_evidence"))
        for artifact in artifacts:
            artifact.skill_updates = {skill_code: {"before": old_score, "after": new_score}}
        _refresh_plan_progress(plan, canonical_task_id)
        plan.updated_at = datetime.now(timezone.utc)
        profile_update = {"skill_code": skill_code, "before": old_score, "after": new_score, "profile_version": user.profile.version}
        if new_score >= 75:
            revision = _create_revision(db, user.id, plan, "evidence", validated_skills={skill_code})
    db.commit()
    for artifact in artifacts:
        db.refresh(artifact)
    return success({
        "passed": passed, "score": total, "task_id": canonical_task_id,
        "artifacts": [_artifact_view(item) for item in artifacts],
        "profile_update": profile_update,
        "revision": _revision_view(revision) if revision else None,
        "next_action": "证据已写入画像；如有路线优化建议，请确认后应用。" if passed else "请补充代码、测试、提交或部署等强证据，并写清它与验收标准的对应关系。",
        "verification_notice": "系统不会仅凭 URL 或文字声称项目真实可运行；外部内容仍需沙箱执行或人工复核。",
    }, "任务证据已评估")


@router.get("/plans/{plan_id}/workspace")
def plan_workspace(
    plan_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.get(LearningPlan, plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="学习计划不存在")
    target = db.scalar(select(CareerTarget).where(CareerTarget.user_id == user.id, CareerTarget.active.is_(True)).order_by(CareerTarget.updated_at.desc()))
    artifacts = db.scalars(select(EvidenceArtifact).where(EvidenceArtifact.plan_id == plan.id).order_by(EvidenceArtifact.created_at.desc()).limit(100)).all()
    revisions = db.scalars(select(RouteRevision).where(RouteRevision.plan_id == plan.id).order_by(RouteRevision.created_at.desc()).limit(30)).all()
    return success({"target": _target_view(target) if target else None, "evidence": [_artifact_view(row) for row in artifacts], "revisions": [_revision_view(row) for row in revisions]})


@router.post("/plans/{plan_id}/recalibrate")
def recalibrate(
    plan_id: str,
    body: RecalibrationInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.get(LearningPlan, plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="学习计划不存在")
    target = db.scalar(select(CareerTarget).where(CareerTarget.user_id == user.id, CareerTarget.active.is_(True)).order_by(CareerTarget.updated_at.desc()))
    skills = target.analysis.get("gap_analysis", {}).get("priority_skills", []) if target and body.trigger == "job_target" else None
    revision = _create_revision(db, user.id, plan, body.trigger, note=body.note, weekly_hours=body.weekly_hours, target_skills=skills)
    db.commit()
    db.refresh(revision)
    return success(_revision_view(revision), "已生成路线调整建议，确认前不会改变当前路线")


@router.post("/plans/{plan_id}/revisions/{revision_id}/decision")
def decide_revision(
    plan_id: str,
    revision_id: str,
    body: RevisionDecisionInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.get(LearningPlan, plan_id)
    revision = db.get(RouteRevision, revision_id)
    if not plan or plan.user_id != user.id or not revision or revision.user_id != user.id or revision.plan_id != plan.id:
        raise HTTPException(status_code=404, detail="路线版本不存在")
    now = datetime.now(timezone.utc)
    if body.action in {"accept", "reject"}:
        if revision.status != "pending":
            raise HTTPException(status_code=409, detail="该调整建议已经处理")
        if body.action == "accept":
            plan.phases = revision.new_phases
            plan.version = max(plan.version + 1, revision.to_version)
            plan.updated_at = now
            revision.status = "accepted"
        else:
            revision.status = "rejected"
        revision.decided_at = now
    else:
        if revision.status != "accepted":
            raise HTTPException(status_code=409, detail="只有已接受的路线版本可以撤销")
        later = db.scalar(select(RouteRevision).where(RouteRevision.plan_id == plan.id, RouteRevision.status == "accepted", RouteRevision.decided_at > revision.decided_at))
        if later:
            raise HTTPException(status_code=409, detail="存在更新的已接受版本，请先处理最新版本")
        plan.phases = revision.old_phases
        plan.version += 1
        plan.updated_at = now
        revision.status = "reverted"
        revision.decided_at = now
    db.commit()
    return success({"revision": _revision_view(revision), "plan_version": plan.version, "phases": plan.phases}, "路线版本状态已更新")
