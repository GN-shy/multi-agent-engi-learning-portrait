"""
LangGraph StateGraph 编排器 - 六Agent协同的核心调度引擎。
Agent间通信严格遵守"只能通过State传递数据"的铁律。
"""

import logging
from typing import Optional
from langgraph.graph import StateGraph, END

from shared.schemas import SessionState, LearnerProfile, LearnerProfileInput
from shared.config import settings

logger = logging.getLogger(__name__)

# 辩论回合上限（硬编码）
MAX_DEBATE_ROUNDS = settings.debate_max_rounds
SINGLE_ROUND_TIMEOUT = settings.debate_single_round_timeout


async def node_lms(state: SessionState) -> dict:
    """节点1: 学情建模"""
    from services.lms.agent import learner_modeling_agent

    logger.info("[Orchestrator] → LMS: 开始学情建模")
    input_data = LearnerProfileInput(
        background=state.interaction_log[-1].get("background", "") if state.interaction_log else "",
    )
    profile = await learner_modeling_agent.analyze(input_data)
    logger.info("[Orchestrator] ✓ LMS: 学情画像构建完成, 学习风格=%s", profile.learning_style)
    return {"learner_profile": profile, "status": "lms_done"}


async def node_krs(state: SessionState) -> dict:
    """节点2: 知识检索"""
    from services.krs.agent import knowledge_retrieval_agent
    from shared.schemas import RetrievalRequest

    logger.info("[Orchestrator] → KRS: 开始知识检索")
    req = RetrievalRequest(
        query=_build_search_query(state.learner_profile),
        learner_profile=state.learner_profile,
        top_k=15,
    )
    result = await knowledge_retrieval_agent.retrieve(req)
    logger.info("[Orchestrator] ✓ KRS: 检索到%d个知识片段", len(result.chunks))
    return {"retrieved_chunks": result.chunks, "status": "krs_done"}


async def node_dgs_gen_a(state: SessionState) -> dict:
    """节点3a: 生成Agent A（严谨策略，低温）"""
    from services.dgs.agent import generation_agent_a

    logger.info("[Orchestrator] → DGS-A: 开始生成(严谨策略)")
    output = await generation_agent_a.generate(state.learner_profile, state.retrieved_chunks)
    logger.info("[Orchestrator] ✓ DGS-A: 生成完成，覆盖%d个知识点", len(output.knowledge_points_covered))
    return {"gen_a_output": output, "status": "dgs_a_done"}


async def node_dgs_gen_b(state: SessionState) -> dict:
    """节点3b: 生成Agent B（创意策略，高温）"""
    from services.dgs.agent import generation_agent_b

    logger.info("[Orchestrator] → DGS-B: 开始生成(创意策略)")
    output = await generation_agent_b.generate(state.learner_profile, state.retrieved_chunks)
    logger.info("[Orchestrator] ✓ DGS-B: 生成完成，覆盖%d个知识点", len(output.knowledge_points_covered))
    return {"gen_b_output": output, "status": "dgs_b_done"}


async def node_ars_arbitrate(state: SessionState) -> dict:
    """节点4: 仲裁审核"""
    from services.ars.agent import arbitration_agent

    logger.info("[Orchestrator] → ARS: 开始仲裁审核")
    result = await arbitration_agent.arbitrate(
        state.gen_a_output, state.gen_b_output, state.retrieved_chunks
    )
    logger.info(
        "[Orchestrator] ✓ ARS: 仲裁完成, 辩论触发=%s, 回合数=%d",
        result.debate_triggered,
        result.debate_rounds,
    )
    return {
        "comparison_result": result,
        "confidence_scores": result.confidence_scores,
        "debate_round": result.debate_rounds,
        "debate_history": result.debate_log,
        "status": "ars_done",
    }


async def node_debate(state: SessionState) -> dict:
    """节点5: 辩论回合（分歧时触发）"""
    from services.ars.agent import arbitration_agent

    round_num = state.debate_round + 1
    if round_num > MAX_DEBATE_ROUNDS:
        logger.warning("[Orchestrator] 辩论已达上限%d轮，强制终止", MAX_DEBATE_ROUNDS)
        return {"status": "debate_max_rounds"}

    logger.info("[Orchestrator] → Debate: 第%d轮辩论开始", round_num)

    # 获取分歧的知识点
    disputed_points = [
        s for s in state.comparison_result.knowledge_point_scores
        if s.consistency < 0.8 and s.winner is None
    ]

    if not disputed_points:
        logger.info("[Orchestrator] 无分歧知识点，跳过辩论")
        return {"status": "debate_resolved"}

    debate_arguments = []
    for kp_score in disputed_points[:3]:  # 每轮最多辩3个知识点
        arg_a = await _debate_argument("gen_a", kp_score.knowledge_point, state)
        arg_b = await _debate_argument("gen_b", kp_score.knowledge_point, state)
        debate_arguments.extend([arg_a, arg_b])

    state.debate_history.extend(debate_arguments)
    logger.info("[Orchestrator] ✓ Debate: 第%d轮完成，产生%d条论点", round_num, len(debate_arguments))

    return {
        "debate_round": round_num,
        "debate_history": state.debate_history,
        "status": "debating",
    }


async def node_fusion(state: SessionState) -> dict:
    """节点6: 融合输出"""
    from services.ars.agent import arbitration_agent

    logger.info("[Orchestrator] → Fusion: 融合输出")
    final = await arbitration_agent.fusion(state)
    logger.info("[Orchestrator] ✓ Fusion: 最终内容生成完成")
    return {"final_output": final, "status": "complete"}


async def node_tis_interact(state: SessionState) -> dict:
    """节点7: 导学交互"""
    from services.tis.agent import tutoring_agent

    logger.info("[Orchestrator] → TIS: 导学交互准备")
    interaction = await tutoring_agent.prepare_interaction(state)
    state.interaction_log.append(interaction)
    return {"interaction_log": state.interaction_log, "status": "tis_ready"}


# ==================== 条件路由 ====================

def should_debate(state: SessionState) -> str:
    """判断是否需要辩论"""
    if state.comparison_result and state.comparison_result.debate_triggered:
        if state.debate_round < MAX_DEBATE_ROUNDS:
            return "debate"
    return "fusion"


def after_debate(state: SessionState) -> str:
    """辩论后决定去向"""
    if state.status == "debate_max_rounds":
        return "fusion"
    if state.comparison_result:
        disputed = [
            s for s in state.comparison_result.knowledge_point_scores
            if s.consistency < 0.8 and s.winner is None
        ]
        if disputed and state.debate_round < MAX_DEBATE_ROUNDS:
            return "debate"
    return "fusion"


# ==================== 构建StateGraph ====================

def build_orchestration_graph() -> StateGraph:
    """构建六Agent协同工作流。

    流程: LMS → KRS → [DGS-A ‖ DGS-B] → ARS → {辩论循环} → Fusion → TIS → END
    """
    workflow = StateGraph(SessionState)

    # 添加节点
    workflow.add_node("lms", node_lms)
    workflow.add_node("krs", node_krs)
    workflow.add_node("dgs_gen_a", node_dgs_gen_a)
    workflow.add_node("dgs_gen_b", node_dgs_gen_b)
    workflow.add_node("ars", node_ars_arbitrate)
    workflow.add_node("debate", node_debate)
    workflow.add_node("fusion", node_fusion)
    workflow.add_node("tis", node_tis_interact)

    # 设置入口
    workflow.set_entry_point("lms")

    # 连线
    workflow.add_edge("lms", "krs")
    workflow.add_edge("krs", "dgs_gen_a")
    workflow.add_edge("krs", "dgs_gen_b")
    workflow.add_edge("dgs_gen_a", "ars")
    workflow.add_edge("dgs_gen_b", "ars")

    # 条件分支：仲裁后决定辩论或融合
    workflow.add_conditional_edges("ars", should_debate, {"debate": "debate", "fusion": "fusion"})
    workflow.add_conditional_edges("debate", after_debate, {"debate": "debate", "fusion": "fusion"})

    workflow.add_edge("fusion", "tis")
    workflow.add_edge("tis", END)

    return workflow.compile()


# ==================== 辅助函数 ====================

def _build_search_query(profile: LearnerProfile) -> str:
    """根据学情画像构建检索查询。"""
    parts = []
    if profile.knowledge_blindspots:
        parts.append("重点关注: " + ", ".join(profile.knowledge_blindspots))
    if profile.strength_areas:
        parts.append("已有基础: " + ", ".join(profile.strength_areas))
    return " ".join(parts) if parts else "基础知识"


async def _debate_argument(agent_id: str, knowledge_point: str, state: SessionState):
    """生成单条辩论论点。"""
    from shared.schemas import DebateArgument
    from shared.utils import generate_id

    return DebateArgument(
        agent_id=agent_id,
        knowledge_point=knowledge_point,
        argument=f"[{agent_id}] 关于'{knowledge_point}'的论点",
        source_quote="（引用知识库原文）",
        source_chunk_id=generate_id(),
        round=state.debate_round + 1,
    )


# 全局编排图实例
orchestration_graph = build_orchestration_graph()
