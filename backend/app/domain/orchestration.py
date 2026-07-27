"""六 Agent 协作状态图。

这里只输出结构化执行轨迹、证据与裁定摘要，不保存或暴露模型隐藏思维链。
"""

from __future__ import annotations

from time import perf_counter
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.domain.content import ContentEngine
from app.domain.catalog import get_catalog
from app.domain.knowledge import get_knowledge_engine
from app.domain.profile import ProfileEngine
from app.domain.routing import RouteEngine


class WorkflowState(TypedDict, total=False):
    input_profile: dict[str, Any]
    track_code: str
    goal: str
    topic: str
    pathway_id: str
    pathway_ids: list[str]
    profile: dict[str, Any]
    route_match: dict[str, Any]
    evidence: list[dict[str, Any]]
    candidate_a: dict[str, Any]
    candidate_b: dict[str, Any]
    arbitration: dict[str, Any]
    tutoring: dict[str, Any]
    events: list[dict[str, Any]]
    extra_evidence: list[dict[str, Any]]


def _record(
    state: WorkflowState,
    agent: str,
    event_type: str,
    summary: str,
    evidence: dict[str, Any],
    started: float,
) -> list[dict[str, Any]]:
    return [
        *state.get("events", []),
        {
            "sequence": len(state.get("events", [])) + 1,
            "agent_code": agent,
            "event_type": event_type,
            "status": "completed",
            "summary": summary,
            "evidence": evidence,
            "duration_ms": max(1, round((perf_counter() - started) * 1000)),
        },
    ]


def lms_node(state: WorkflowState) -> dict[str, Any]:
    started = perf_counter()
    profile = ProfileEngine().analyze(state["input_profile"], state["track_code"])
    route_match = RouteEngine().compare(profile, [state["track_code"]])[0]
    return {
        "profile": profile,
        "route_match": route_match,
        "events": _record(
            state,
            "lms",
            "profile.updated",
            "融合背景、自评与诊断证据，生成五维状态和六维能力画像。",
            {
                "profile_score": profile["comprehensive_score"],
                "evidence_count": profile["evidence_count"],
                "top_gaps": route_match["skill_gaps"][:3],
            },
            started,
        ),
    }


def krs_node(state: WorkflowState) -> dict[str, Any]:
    started = perf_counter()
    profile = state["profile"]
    target_difficulty = 1 + profile["knowledge_depth"] * 4
    gap_names = " ".join(item["name"] for item in state["route_match"]["skill_gaps"][:4])
    query = " ".join([state.get("topic", ""), state["goal"], gap_names])
    selected_pathways = [
        get_catalog().get_pathway(pathway_id)
        for pathway_id in state.get("pathway_ids", [])
    ]
    track_codes = list(
        dict.fromkeys(
            [state["track_code"]]
            + [pathway["track_code"] for pathway in selected_pathways]
        )
    )
    evidence = []
    per_track = max(4, 12 // max(1, len(track_codes)))
    for track_code in track_codes:
        evidence.extend(
            get_knowledge_engine().search(
                query=query,
                track_code=track_code,
                top_k=per_track,
                target_difficulty=target_difficulty,
            )
        )
    evidence = list({item["chunk_id"]: item for item in evidence}.values())
    known_ids = {item["chunk_id"] for item in evidence}
    evidence.extend(
        item
        for item in state.get("extra_evidence", [])
        if item["chunk_id"] not in known_ids
    )
    return {
        "evidence": evidence,
        "events": _record(
            state,
            "krs",
            "retrieval.completed",
            "按目标路线、技能缺口、难度与来源版本完成检索和重排。",
            {
                "query": query,
                "track_codes": track_codes,
                "retrieved": len(evidence),
                "source_ids": [item["chunk_id"] for item in evidence],
            },
            started,
        ),
    }


def dgs_a_node(state: WorkflowState) -> dict[str, Any]:
    started = perf_counter()
    candidate = ContentEngine().generate_rigorous(
        state["track_code"],
        state["goal"],
        state["profile"],
        state["route_match"],
        state["evidence"],
        state.get("pathway_id"),
        state.get("pathway_ids"),
    )
    return {
        "candidate_a": candidate,
        "events": _record(
            state,
            "dgs_a",
            "generation.candidate",
            "生成遵守前置关系、逐节带引用的严谨学习方案。",
            {
                "strategy": candidate["strategy"],
                "sections": len(candidate["lecture"]["sections"]),
            },
            started,
        ),
    }


def dgs_b_node(state: WorkflowState) -> dict[str, Any]:
    started = perf_counter()
    candidate = ContentEngine().generate_project_first(
        state["track_code"],
        state["goal"],
        state["profile"],
        state["route_match"],
        state["evidence"],
        state.get("pathway_id"),
        state.get("pathway_ids"),
    )
    return {
        "candidate_b": candidate,
        "events": _record(
            state,
            "dgs_b",
            "generation.candidate",
            "生成以代表项目为牵引、用失败证据回补原理的学习方案。",
            {
                "strategy": candidate["strategy"],
                "steps": len(candidate["practice"]["steps"]),
            },
            started,
        ),
    }


def ars_node(state: WorkflowState) -> dict[str, Any]:
    started = perf_counter()
    result = ContentEngine().arbitrate(
        state["candidate_a"], state["candidate_b"], state["evidence"], state["profile"]
    )
    return {
        "arbitration": result,
        "events": _record(
            state,
            "ars",
            "arbitration.completed",
            "按覆盖率、引用率、画像适配与前置依赖进行评分、辩论和融合。",
            {
                "winner": result["winner"],
                "debate_rounds": result["debate_rounds"],
                "quality_metrics": result["quality_metrics"],
            },
            started,
        ),
    }


def tis_node(state: WorkflowState) -> dict[str, Any]:
    started = perf_counter()
    profile = state["profile"]
    first_gap = state["route_match"]["skill_gaps"][0]
    tutoring = {
        "opening_question": (
            f"在开始“{first_gap['name']}”前，你能给出一个过去遇到的相关问题吗？"
        ),
        "difficulty_action": (
            "拆成更小步骤"
            if profile["cognitive_load"] > 0.55
            else "保持当前难度并要求提交运行证据"
        ),
        "next_action": state["arbitration"]["final_output"]["plan"][0],
        "feedback_options": ["too_hard", "too_easy", "helpful", "not_helpful"],
    }
    return {
        "tutoring": tutoring,
        "events": _record(
            state,
            "tis",
            "tutoring.ready",
            "根据认知负荷和首要技能缺口生成追问、难度动作与下一步任务。",
            {"next_skill": first_gap["skill_code"]},
            started,
        ),
    }


def build_graph():
    workflow = StateGraph(WorkflowState)
    workflow.add_node("lms", lms_node)
    workflow.add_node("krs", krs_node)
    workflow.add_node("dgs_a", dgs_a_node)
    workflow.add_node("dgs_b", dgs_b_node)
    workflow.add_node("ars", ars_node)
    workflow.add_node("tis", tis_node)
    workflow.set_entry_point("lms")
    workflow.add_edge("lms", "krs")
    workflow.add_edge("krs", "dgs_a")
    workflow.add_edge("dgs_a", "dgs_b")
    workflow.add_edge("dgs_b", "ars")
    workflow.add_edge("ars", "tis")
    workflow.add_edge("tis", END)
    return workflow.compile()


orchestration_graph = build_graph()


def run_workflow(
    profile_input: dict[str, Any],
    track_code: str,
    goal: str,
    topic: str = "",
    extra_evidence: list[dict[str, Any]] | None = None,
    pathway_id: str | None = None,
    pathway_ids: list[str] | None = None,
) -> WorkflowState:
    return orchestration_graph.invoke(
        {
            "input_profile": profile_input,
            "track_code": track_code,
            "goal": goal,
            "topic": topic,
            "pathway_id": pathway_id or "",
            "pathway_ids": pathway_ids or ([pathway_id] if pathway_id else []),
            "events": [],
            "extra_evidence": extra_evidence or [],
        }
    )
