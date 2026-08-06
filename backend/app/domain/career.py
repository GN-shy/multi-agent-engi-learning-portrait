"""岗位文本解析、能力差距分析与学习路线重排规则。"""

from __future__ import annotations

import copy
import math
import re
from typing import Any


TECH_RULES = [
    ("HTML", ["html", "html5"], "fe.web_platform", "web_frontend"),
    ("CSS", ["css", "scss", "less"], "fe.web_platform", "web_frontend"),
    ("JavaScript", ["javascript", "js"], "fe.web_platform", "web_frontend"),
    ("TypeScript", ["typescript", "ts"], "fe.typescript", "web_frontend"),
    ("Vue", ["vue", "vue3"], "fe.framework", "web_frontend"),
    ("React", ["react", "next.js", "nextjs"], "fe.framework", "web_frontend"),
    ("性能优化", ["性能优化", "web vitals"], "fe.quality", "web_frontend"),
    ("Java", ["java"], "core.programming", "backend"),
    ("Spring Boot", ["spring boot", "springboot", "spring cloud"], "be.api", "backend"),
    ("Python", ["python"], "core.programming", "backend"),
    ("FastAPI", ["fastapi", "django", "flask"], "be.api", "backend"),
    ("Go", ["golang", "go语言"], "be.concurrency", "backend"),
    ("Node.js", ["node.js", "nodejs", "nestjs", "express"], "be.api", "backend"),
    ("MySQL", ["mysql", "postgresql", "postgres", "sql server"], "core.database", "backend"),
    ("Redis", ["redis"], "be.persistence", "backend"),
    ("消息队列", ["kafka", "rabbitmq", "rocketmq", "消息队列"], "be.concurrency", "backend"),
    ("微服务", ["微服务", "microservice"], "be.observability", "backend"),
    ("Git", ["git", "github", "gitlab"], "core.git", "fullstack"),
    ("Linux", ["linux", "shell", "bash"], "core.linux", "devops"),
    ("Docker", ["docker", "dockerfile"], "ops.container", "devops"),
    ("Kubernetes", ["kubernetes", "k8s"], "ops.k8s", "devops"),
    ("CI/CD", ["ci/cd", "cicd", "jenkins", "github actions"], "ops.cicd", "devops"),
    ("自动化测试", ["pytest", "junit", "playwright", "selenium", "自动化测试"], "qa.automation", "quality_engineering"),
    ("数据结构与算法", ["数据结构", "算法", "leetcode"], "core.data_structures", "algorithms"),
    ("机器学习", ["机器学习", "scikit-learn", "sklearn"], "ml.modeling", "machine_learning"),
    ("深度学习", ["pytorch", "tensorflow", "深度学习"], "ml.deep_learning", "machine_learning"),
    ("LLM", ["llm", "大模型", "prompt", "提示词"], "llm.prompting", "llm_application"),
    ("RAG", ["rag", "向量数据库", "embedding"], "llm.rag", "llm_application"),
    ("Agent", ["agent", "智能体", "langgraph", "autogen"], "agent.workflow", "agent_engineering"),
    ("C/C++", ["c++", "c语言", "cpp"], "emb.c", "embedded_iot"),
    ("MCU", ["mcu", "stm32", "单片机"], "emb.mcu", "embedded_iot"),
    ("RTOS", ["rtos", "freertos"], "emb.rtos", "embedded_iot"),
    ("网络安全", ["渗透测试", "漏洞", "网络安全", "owasp"], "sec.app", "network_security"),
    ("数据仓库", ["数据仓库", "hive", "spark", "flink"], "de.pipeline", "data_engineering"),
    ("UI/UX", ["figma", "ui/ux", "交互设计", "用户研究"], "design.interaction", "uiux"),
]


def _contains(text: str, alias: str) -> bool:
    alias = alias.lower()
    if re.fullmatch(r"[a-z0-9+#./-]+", alias):
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text))
    return alias in text


def parse_job_description(raw_text: str, source_url: str = "") -> dict[str, Any]:
    text = raw_text.strip()
    lower = text.lower()
    lines = [re.sub(r"^[\s•·*\-—\d.、()（）]+", "", line).strip() for line in text.splitlines() if line.strip()]
    skills = []
    for name, aliases, skill_code, track_code in TECH_RULES:
        hits = [alias for alias in aliases if _contains(lower, alias)]
        if hits:
            skills.append({
                "name": name, "skill_code": skill_code, "track_code": track_code,
                "evidence": hits[:3], "required": True,
            })
    education = next((value for value in ("博士", "硕士", "本科", "大专", "专科") if value in text), "未明确")
    experience_match = re.search(r"(\d+\s*[-—~至]\s*\d+\s*年|\d+\s*年以上|应届生|在校生|不限经验)", text)
    salary_match = re.search(r"(\d+(?:\.\d+)?\s*[kKＫ]\s*[-—~至]\s*\d+(?:\.\d+)?\s*[kKＫ](?:\s*[·x×]\s*\d+薪)?|\d+\s*[-—~至]\s*\d+\s*万/年)", text)
    city_match = re.search(r"(?:工作地点|地点|城市|坐标)\s*[：:]?\s*([\u4e00-\u9fff]{2,8})", text)
    title = next((line for line in lines[:4] if 2 <= len(line) <= 45 and any(word in line.lower() for word in ("工程师", "开发", "算法", "测试", "运维", "设计", "实习", "java", "前端", "后端"))), lines[0][:80] if lines else "目标岗位")
    responsibilities = [line for line in lines if any(word in line for word in ("负责", "参与", "设计", "开发", "维护", "建设", "优化", "实现"))][:12]
    track_counts: dict[str, int] = {}
    for item in skills:
        track_counts[item["track_code"]] = track_counts.get(item["track_code"], 0) + 1
    tracks = sorted(track_counts.items(), key=lambda item: item[1], reverse=True)
    extracted_fields = 1 + bool(skills) + (education != "未明确") + bool(experience_match) + bool(salary_match) + bool(city_match)
    return {
        "title": title,
        "company": "",
        "city": city_match.group(1) if city_match else "",
        "education": education,
        "experience": experience_match.group(1).replace(" ", "") if experience_match else "未明确",
        "salary": salary_match.group(1).replace(" ", "") if salary_match else "未明确",
        "source_url": source_url,
        "required_skills": skills,
        "responsibilities": responsibilities,
        "suggested_tracks": [{"track_code": code, "evidence_count": count} for code, count in tracks[:4]],
        "confidence": round(min(0.96, 0.38 + extracted_fields * 0.09 + min(0.22, len(skills) * 0.02)), 2),
        "limitations": [
            "结果来自可审计规则匹配，不会补写招聘文本中没有的信息。",
            "薪资、城市和学历未明确时必须由用户确认，不使用虚构默认值。",
            "确认目标岗位后才会影响学习路线。",
        ],
    }


def job_gap_analysis(required_skills: list[dict[str, Any]], skill_scores: dict[str, float]) -> dict[str, Any]:
    rows = []
    for item in required_skills:
        current = float(skill_scores.get(item.get("skill_code", ""), 0) or 0)
        target = 75.0
        rows.append({**item, "current": round(current, 1), "target": target, "gap": round(max(0, target - current), 1), "status": "已具备" if current >= target else "待补齐"})
    rows.sort(key=lambda item: item["gap"], reverse=True)
    coverage = sum(item["current"] >= item["target"] for item in rows) / max(1, len(rows))
    missing = [item for item in rows if item["gap"] > 0]
    return {
        "items": rows,
        "coverage": round(coverage, 3),
        "missing_count": len(missing),
        "priority_skills": missing[:8],
    }


def build_revision(
    phases: list[dict[str, Any]],
    trigger: str,
    *,
    note: str = "",
    weekly_hours: int | None = None,
    target_skills: list[dict[str, Any]] | None = None,
    validated_skills: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    new_phases = copy.deepcopy(phases)
    changes: list[dict[str, Any]] = []
    validated_skills = validated_skills or set()
    target_skills = target_skills or []

    if trigger == "job_target" and target_skills:
        active = next((phase for phase in new_phases if phase.get("status") != "completed"), new_phases[0] if new_phases else None)
        if active:
            prioritized = []
            for item in target_skills:
                code = item.get("skill_code", "")
                if not code:
                    continue
                existing_task = None
                for phase in new_phases:
                    if phase.get("status") == "completed":
                        continue
                    kept = []
                    for task in phase.get("tasks", []):
                        if task.get("skill_code") == code and existing_task is None:
                            existing_task = dict(task)
                        else:
                            kept.append(task)
                    phase["tasks"] = kept
                prioritized.append({
                    **(existing_task or {}),
                        "id": f"job-gap:{code}", "title": f"岗位差距：{item.get('name', code)}",
                        "skill_code": code, "priority": "job_required",
                        "learning_action": f"完成 {item.get('name', code)} 的最小可运行任务，并对照目标 JD 说明使用场景。",
                        "evidence_required": "代码/测试/部署证据至少一项 + 与 JD 要求的对应说明",
                        "acceptance": "可独立完成典型任务，解释关键取舍，并提交可复核证据。",
                    })
            active["tasks"] = prioritized + list(active.get("tasks", []))
            changes.append({"type": "job_alignment", "label": f"将 {len(prioritized)} 个岗位差距任务前置并标记为高优先级"})

    if trigger in {"too_hard", "blocked"} and new_phases:
        active = next((phase for phase in new_phases if phase.get("status") != "completed"), new_phases[0])
        skill = next(iter(active.get("skills", [])), "core.programming")
        support = {
            "id": f"support:{trigger}:{skill}", "title": "回补前置与最小练习",
            "skill_code": skill, "priority": "remediation",
            "learning_action": "把当前难点拆成原理说明、最小示例、异常路径和复盘四步完成。",
            "evidence_required": "最小可运行示例 + 失败原因与修正记录",
            "acceptance": "不照抄教程完成最小任务，并能说明失败边界。",
        }
        active["tasks"] = [support] + list(active.get("tasks", []))
        changes.append({"type": "remediation", "label": "在当前阶段前加入回补前置任务"})

    if validated_skills:
        removed = 0
        for phase in new_phases:
            if phase.get("status") == "completed":
                continue
            tasks = list(phase.get("tasks", []))
            kept = [task for task in tasks if task.get("skill_code") not in validated_skills]
            if tasks and not kept:
                kept = tasks[-1:]
            removed += len(tasks) - len(kept)
            phase["tasks"] = kept
        changes.append({"type": "evidence_credit", "label": f"依据已验证成果免除 {removed} 个重复训练任务"})

    factor = 1.0
    if trigger in {"too_hard", "blocked"}:
        factor = 1.3
    elif trigger == "too_easy" or validated_skills:
        factor = .82
    if weekly_hours:
        original_hours = max([int(phase.get("hours_per_week", weekly_hours) or weekly_hours) for phase in new_phases] or [weekly_hours])
        factor *= original_hours / max(1, weekly_hours)
        for phase in new_phases:
            phase["hours_per_week"] = weekly_hours
        changes.append({"type": "availability", "label": f"每周投入调整为 {weekly_hours} 小时"})

    cursor = 1
    old_total = max([int(phase.get("week_end", 0)) for phase in phases] or [0])
    for phase in new_phases:
        duration = max(1, int(phase.get("week_end", cursor)) - int(phase.get("week_start", cursor)) + 1)
        if phase.get("status") != "completed":
            duration = max(1, math.ceil(duration * factor))
        phase["week_start"] = cursor
        phase["week_end"] = cursor + duration - 1
        cursor += duration
    new_total = cursor - 1
    if new_total != old_total:
        changes.append({"type": "duration", "label": f"总周期由 {old_total} 周调整为 {new_total} 周"})
    reason_map = {
        "job_target": "目标岗位发生变化，按真实 JD 能力要求调整任务优先级",
        "too_hard": "用户反馈当前内容过难，增加前置回补并降低推进速度",
        "too_easy": "用户反馈内容过易，压缩重复训练并提高推进速度",
        "no_time": "可投入时间变化，重新计算每阶段周期",
        "blocked": "任务连续受阻，拆分难点并加入最小可运行练习",
        "evidence": "新成果通过证据校验，免除已经证明的重复学习",
        "manual": "用户主动请求重新校准学习路线",
    }
    reason = reason_map.get(trigger, "学习状态变化触发路线校准") + (f"；补充说明：{note}" if note else "")
    return new_phases, changes, reason
