"""Structured, evidence-aware assessment scoring.

The scorer deliberately separates demonstrated reasoning from verification
confidence.  A fluent answer can receive formative feedback, but it cannot
strongly update the learner profile without usable evidence.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlparse


FIELDS = {
    "action": {"label": "实施方案", "minimum": 45},
    "validation": {"label": "验收与验证", "minimum": 35},
    "boundary": {"label": "失败处理", "minimum": 35},
    "reasoning": {"label": "技术取舍", "minimum": 35},
}
EVIDENCE_WEIGHTS = {
    "repository": 0.72,
    "commit": 0.78,
    "test": 0.86,
    "deployment": 0.82,
    "screenshot_note": 0.58,
    "note": 0.38,
}


def _text(value: Any, limit: int = 3000) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def normalize_answer(value: Any) -> dict[str, Any]:
    """Accept the current structured format and keep old text submissions compatible."""

    if isinstance(value, dict):
        return {
            "action": _text(value.get("action")),
            "validation": _text(value.get("validation")),
            "boundary": _text(value.get("boundary")),
            "reasoning": _text(value.get("reasoning")),
            "evidence": value.get("evidence") if isinstance(value.get("evidence"), list) else [],
        }
    legacy = _text(value)
    return {
        "action": legacy,
        "validation": legacy,
        "boundary": legacy,
        "reasoning": legacy,
        "evidence": [],
    }


def _has_structure(value: str) -> bool:
    return bool(re.search(r"(?:^|\s)(?:\d+[.、)]|步骤[一二三四五六\d]|先.+再|输入.+输出)", value))


def _field_score(code: str, value: str) -> tuple[float, list[str]]:
    """Score observable answer structure, not raw keyword frequency."""

    issues: list[str] = []
    minimum = FIELDS[code]["minimum"]
    if not value:
        return 0.0, [f"未填写{FIELDS[code]['label']}"]

    length_ratio = min(1.0, len(value) / minimum)
    score = 0.7 * length_ratio
    if code == "action":
        if _has_structure(value):
            score += 0.65
        else:
            issues.append("实施方案需要体现顺序、输入输出或可执行步骤")
        if re.search(r"(?:接口|函数|模块|数据|配置|命令|页面|模型|算法|服务|仓库)", value):
            score += 0.65
        else:
            issues.append("实施方案缺少具体技术对象")
    elif code == "validation":
        if re.search(r"(?:预期|通过标准|断言|状态码|误差|耗时|覆盖率|输出为|应当|日志)", value):
            score += 0.65
        else:
            issues.append("需要写明可判定的预期结果或通过标准")
        if re.search(r"(?:测试|命令|请求|样例|指标|日志|检查|对照)", value):
            score += 0.65
        else:
            issues.append("需要说明用什么方法或工具验证")
    elif code == "boundary":
        if re.search(r"(?:失败|异常|错误|超时|空值|并发|权限|断网|越界|冲突)", value):
            score += 0.65
        else:
            issues.append("至少给出一个具体失败或边界场景")
        if re.search(r"(?:定位|排查|日志|回滚|重试|降级|恢复|修复|隔离)", value):
            score += 0.65
        else:
            issues.append("需要写明定位或恢复办法")
    else:
        if re.search(r"(?:选择|采用|不用|替代|相比|方案A|方案B|备选)", value, re.I):
            score += 0.65
        else:
            issues.append("需要明确主方案与备选方案")
        if re.search(r"(?:因为|代价|成本|复杂度|性能|维护|安全|适用|权衡|取舍)", value):
            score += 0.65
        else:
            issues.append("需要解释判断依据与代价")
    return round(min(2.0, score), 1), issues


def _valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _review_evidence(raw_items: list[Any]) -> tuple[list[dict[str, Any]], float]:
    results: list[dict[str, Any]] = []
    accepted_weights: list[float] = []
    for raw in raw_items[:6]:
        item = raw if isinstance(raw, dict) else {"type": "note", "value": raw}
        kind = _text(item.get("type"), 30) or "note"
        value = _text(item.get("value"), 1200)
        accepted = True
        reason = "格式有效；真实性仍需人工或外部系统复核"
        if kind not in EVIDENCE_WEIGHTS:
            accepted, reason = False, "不支持的成果证据类型"
        elif not value:
            accepted, reason = False, "成果证据为空"
        elif kind in {"repository", "deployment"} and not _valid_http_url(value):
            accepted, reason = False, "链接需要使用 http 或 https"
        elif kind == "commit" and not re.fullmatch(r"[0-9a-fA-F]{7,40}", value):
            accepted, reason = False, "提交哈希应为 7 至 40 位十六进制字符"
        elif kind == "test" and len(value) < 18:
            accepted, reason = False, "请写明测试命令、数量和关键结果"
        elif kind == "screenshot_note" and len(value) < 15:
            accepted, reason = False, "请说明截图内容对应哪个验收标准"
        elif kind == "note" and len(value) < 30:
            accepted, reason = False, "文字说明过短，不能作为可靠成果证据"
        results.append(
            {
                "type": kind,
                "value_preview": value[:120],
                "accepted": accepted,
                "reason": reason,
                "verification_scope": "仅完成格式与完整性检查，未声明外部真实性已验证",
            }
        )
        if accepted:
            accepted_weights.append(EVIDENCE_WEIGHTS[kind])
    confidence = max(accepted_weights, default=0.32)
    if len(accepted_weights) >= 2:
        confidence = min(0.92, confidence + 0.08)
    return results, round(confidence, 2)


def score_structured_answer(value: Any, max_score: float = 10) -> dict[str, Any]:
    answer = normalize_answer(value)
    rubric_scores: dict[str, float] = {}
    guidance: dict[str, list[str]] = {}
    for code in FIELDS:
        rubric_scores[code], guidance[code] = _field_score(code, answer[code])

    texts = [answer[code] for code in FIELDS if answer[code]]
    duplicated = any(
        SequenceMatcher(None, left, right).ratio() > 0.88
        for index, left in enumerate(texts)
        for right in texts[index + 1 :]
    )
    integrity_penalty = 1.5 if duplicated else 0.0
    evidence_review, confidence = _review_evidence(answer["evidence"])
    evidence_score = round(confidence * 2, 1) if any(item["accepted"] for item in evidence_review) else 0.0
    raw = max(0.0, sum(rubric_scores.values()) + evidence_score - integrity_penalty)
    score = round(min(max_score, raw / 10 * max_score), 1)
    verified_score = round(score * confidence, 1)
    missing = [code for code, value in rubric_scores.items() if value < 1.2]
    if not evidence_score:
        missing.append("evidence")
    if duplicated:
        guidance["integrity"] = ["四个栏目内容高度重复，需要分别回答，不要复制同一段文字"]

    evidence_level = (
        "strong" if confidence >= 0.8 else "moderate" if confidence >= 0.58 else "formative"
    )
    return {
        "score": score,
        "verified_score": verified_score,
        "rubric_scores": rubric_scores,
        "evidence_score": evidence_score,
        "evidence_confidence": confidence,
        "evidence_level": evidence_level,
        "missing_dimensions": list(dict.fromkeys(missing)),
        "guidance": guidance,
        "evidence_review": evidence_review,
        "integrity_flags": ["duplicated_sections"] if duplicated else [],
        "eligible_for_profile_update": confidence >= 0.58 and score >= 6,
    }


def profile_update_weight(confidence: float) -> float:
    if confidence >= 0.8:
        return 0.3
    if confidence >= 0.58:
        return 0.16
    return 0.0
