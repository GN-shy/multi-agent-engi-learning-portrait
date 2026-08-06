"""Deterministic, auditable grounding checks for external LLM content.

These checks are a release gate, not an empirical hallucination-rate estimate.
Competition claims still require independent human blind review.
"""

from __future__ import annotations

import re
from typing import Any


_NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?%?")
_TECH_TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9.+#_-]{1,}\b")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
_ALLOWED_KINDS = {"summary", "tip", "caution"}


def _normalized(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def _semantic_units(value: str) -> set[str]:
    text = str(value or "").lower()
    units = {item.lower() for item in _TECH_TOKEN_RE.findall(text)}
    for sequence in _CJK_RE.findall(text):
        if len(sequence) == 1:
            units.add(sequence)
        else:
            units.update(sequence[index : index + 2] for index in range(len(sequence) - 1))
    return units


def _evidence_text(item: dict[str, Any]) -> str:
    return " ".join(str(item.get(key) or "") for key in ("title", "content", "source_title"))


def verify_atomic_claims(
    payload: dict[str, Any], evidence: list[dict[str, Any]]
) -> dict[str, Any]:
    """Classify atomic claims as supported or rejected against cited evidence."""

    evidence_by_id = {
        str(item.get("chunk_id")): item for item in evidence if item.get("chunk_id")
    }
    raw_claims = payload.get("atomic_claims")
    claims = raw_claims if isinstance(raw_claims, list) else []
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for index, raw in enumerate(claims[:20]):
        issues: list[str] = []
        if not isinstance(raw, dict):
            rejected.append(
                {"index": index, "text": "", "status": "rejected", "issues": ["invalid_claim"]}
            )
            continue

        text = str(raw.get("text") or "").strip()[:1000]
        kind = str(raw.get("kind") or "tip").strip().lower()
        quote = str(raw.get("evidence_quote") or "").strip()[:1000]
        raw_ids = raw.get("citation_ids")
        citation_ids = (
            list(dict.fromkeys(str(item) for item in raw_ids if isinstance(item, str)))
            if isinstance(raw_ids, list)
            else []
        )
        cited = [evidence_by_id[item] for item in citation_ids if item in evidence_by_id]

        if not text:
            issues.append("empty_claim")
        if kind not in _ALLOWED_KINDS:
            issues.append("invalid_kind")
        if not citation_ids or len(cited) != len(citation_ids):
            issues.append("invalid_or_missing_citation")
        if len(_normalized(quote)) < 6:
            issues.append("evidence_quote_too_short")

        combined_evidence = " ".join(_evidence_text(item) for item in cited)
        if quote and _normalized(quote) not in _normalized(combined_evidence):
            issues.append("quote_not_found_in_cited_evidence")

        if set(_NUMBER_RE.findall(text)) - set(_NUMBER_RE.findall(combined_evidence)):
            issues.append("unsupported_number")

        claim_tech = {item.lower() for item in _TECH_TOKEN_RE.findall(text)}
        evidence_tech = {item.lower() for item in _TECH_TOKEN_RE.findall(combined_evidence)}
        if claim_tech - evidence_tech:
            issues.append("unsupported_named_technology")

        claim_units = _semantic_units(text)
        quote_units = _semantic_units(quote)
        overlap = len(claim_units & quote_units) / max(1, min(len(claim_units), len(quote_units)))
        if overlap < 0.18:
            issues.append("insufficient_semantic_overlap")

        claim = {
            "index": index,
            "kind": kind,
            "text": text,
            "citation_ids": citation_ids,
            "evidence_quote": quote,
            "support_score": round(overlap, 3),
            "status": "supported" if not issues else "rejected",
            "issues": issues,
        }
        (accepted if not issues else rejected).append(claim)

    total = len(accepted) + len(rejected)
    grounded_rate = len(accepted) / max(1, total)
    status = "passed" if total and not rejected else "partial" if accepted else "blocked"
    return {
        "detector_version": "claim-grounding-v1",
        "method": "atomic_claim_exact_quote_numeric_entity_overlap",
        "status": status,
        "total_claims": total,
        "supported_claims": len(accepted),
        "rejected_claims": len(rejected),
        "grounded_claim_rate": round(grounded_rate, 3),
        "unsupported_claim_rate": round(1 - grounded_rate, 3) if total else 1.0,
        "released_claims": len(accepted),
        "released_grounded_rate": 1.0 if accepted else 0.0,
        "requires_human_review": True,
        "metric_notice": "这是系统主张级证据检查结果，不等同于人工盲测得到的真实幻觉率。",
        "accepted": accepted,
        "rejected": rejected,
    }


def build_grounded_enhancement(
    payload: dict[str, Any], audit: dict[str, Any]
) -> dict[str, Any]:
    """Build user-visible fields exclusively from accepted claims."""

    accepted = audit.get("accepted", [])
    citation_ids = list(
        dict.fromkeys(
            citation_id
            for item in accepted
            for citation_id in item.get("citation_ids", [])
        )
    )
    return {
        "personalized_summary": "；".join(
            item["text"] for item in accepted if item.get("kind") == "summary"
        ),
        "project_tips": [item["text"] for item in accepted if item.get("kind") == "tip"],
        "caution": "；".join(
            item["text"] for item in accepted if item.get("kind") == "caution"
        ),
        "citation_ids": citation_ids,
        "atomic_claims": accepted,
        "claim_verification": {
            key: value for key, value in audit.items() if key not in {"accepted", "rejected"}
        },
    }
