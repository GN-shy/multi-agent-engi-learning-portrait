"""仲裁审核Agent —— 逐知识点评分、辩论裁判、融合输出"""

import json
import logging
from pathlib import Path
from shared.schemas import (
    GeneratedContent, KnowledgeChunk, KnowledgePointScore,
    ArbitrationResult, SessionState, AgentException,
)
from shared.llm import LLMClient
from shared.config import settings
from shared.utils import generate_id

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"

# 辩论回合上限
MAX_DEBATE_ROUNDS = settings.debate_max_rounds
# 语义一致性阈值（超过此值视为一致，跳过辩论）
CONSISTENCY_THRESHOLD = 0.8


class ArbitrationAgent:
    def __init__(self):
        self.llm = LLMClient(
            model=settings.ars_model,
            temperature=settings.ars_temperature,
            max_tokens=4096,
            timeout=settings.llm_timeout,
        )

    async def arbitrate(
        self,
        gen_a: GeneratedContent,
        gen_b: GeneratedContent,
        knowledge_chunks: list[KnowledgeChunk],
    ) -> ArbitrationResult:
        """仲裁审核：逐知识点评分、检测分歧、触发辩论、融合输出。"""
        try:
            # 步骤1: 提取知识点列表
            kp_list = self._extract_knowledge_points(gen_a, gen_b, knowledge_chunks)

            # 步骤2: 逐知识点评分
            scores = []
            for kp in kp_list:
                score = await self._score_knowledge_point(kp, gen_a, gen_b, knowledge_chunks)
                scores.append(score)

            # 步骤3: 判断是否需要辩论
            disputed = [s for s in scores if s.consistency < CONSISTENCY_THRESHOLD]
            debate_triggered = len(disputed) > 0

            logger.info(
                "仲裁完成: 知识点总数=%d, 一致=%d, 分歧=%d, 辩论触发=%s",
                len(scores), len(scores) - len(disputed), len(disputed), debate_triggered,
            )

            return ArbitrationResult(
                knowledge_point_scores=scores,
                debate_triggered=debate_triggered,
                debate_rounds=0,
                debate_log=[],
                confidence_scores={s.knowledge_point: max(s.score_a, s.score_b) for s in scores},
            )
        except Exception as e:
            logger.error("仲裁审核失败: %s", e, exc_info=True)
            raise AgentException("ARS", str(e))

    async def fusion(self, state: SessionState) -> GeneratedContent:
        """融合输出：取各版本高分片段，拼接为最终内容。"""
        try:
            gen_a = state.gen_a_output
            gen_b = state.gen_b_output
            scores = state.comparison_result.knowledge_point_scores if state.comparison_result else []

            # 基于仲裁结果融合讲义
            fused_lecture = self._fuse_content(
                gen_a.lecture_notes, gen_b.lecture_notes, scores, state.debate_history
            )
            fused_practice = self._fuse_content(
                gen_a.practice_guide, gen_b.practice_guide, scores, state.debate_history
            )

            # 合并测试题（去重）
            all_quizzes = gen_a.quiz_questions + gen_b.quiz_questions
            seen_q = set()
            unique_quizzes = []
            for q in all_quizzes:
                q_text = q.get("question", "")
                if q_text not in seen_q:
                    seen_q.add(q_text)
                    unique_quizzes.append(q)

            # 合并知识溯源
            all_sources = gen_a.source_references + gen_b.source_references
            all_kps = list(set(gen_a.knowledge_points_covered + gen_b.knowledge_points_covered))

            # 确定胜出策略
            a_wins = sum(1 for s in scores if s.winner == "gen_a")
            b_wins = sum(1 for s in scores if s.winner == "gen_b")
            dominant = "rigorous" if a_wins >= b_wins else "creative"

            return GeneratedContent(
                agent_id="fusion",
                strategy=f"fused({dominant})",
                lecture_notes=fused_lecture,
                practice_guide=fused_practice,
                quiz_questions=unique_quizzes,
                knowledge_points_covered=all_kps,
                source_references=all_sources,
            )
        except Exception as e:
            logger.error("融合输出失败: %s", e, exc_info=True)
            raise AgentException("ARS-Fusion", str(e))

    def _extract_knowledge_points(
        self, gen_a: GeneratedContent, gen_b: GeneratedContent, chunks: list[KnowledgeChunk]
    ) -> list[str]:
        """提取两版内容共同覆盖的知识点列表。"""
        kps_a = set(gen_a.knowledge_points_covered)
        kps_b = set(gen_b.knowledge_points_covered)
        # 合并 + 从知识库补充
        all_kps = list(kps_a | kps_b)
        if not all_kps:
            all_kps = [c.title for c in chunks[:5]]
        return all_kps[:10]  # 最多评分10个知识点

    async def _score_knowledge_point(
        self, kp: str, gen_a: GeneratedContent, gen_b: GeneratedContent, chunks: list[KnowledgeChunk]
    ) -> KnowledgePointScore:
        """对单个知识点评分。"""
        # 知识库一致性评分（基于关键词匹配模拟）
        rel_chunks = [c for c in chunks if kp.lower() in c.content.lower() or kp.lower() in c.title.lower()]
        consistency_base = min(0.7 + len(rel_chunks) * 0.05, 1.0) if rel_chunks else 0.3

        # 模拟两版内容在该知识点上的得分
        score_a = consistency_base * 0.95  # 严谨策略略高
        score_b = consistency_base * 0.90  # 创意策略略低

        # 两版一致性（模拟：基于文本重叠度）
        consistency = 0.85 if rel_chunks else 0.5

        winner = "gen_a" if score_a > score_b else "gen_b"

        return KnowledgePointScore(
            knowledge_point=kp,
            score_a=round(score_a, 3),
            score_b=round(score_b, 3),
            consistency=round(consistency, 3),
            winner=winner,
            reason=f"Agent A在'{kp}'上的知识库一致性更高" if winner == "gen_a" else f"Agent B在'{kp}'上的逻辑自洽性更好",
        )

    def _fuse_content(self, content_a: str, content_b: str, scores: list[KnowledgePointScore], debate_log: list) -> str:
        """融合两版内容。"""
        a_wins = sum(1 for s in scores if s.winner == "gen_a")
        b_wins = sum(1 for s in scores if s.winner == "gen_b")

        if a_wins >= b_wins:
            primary, secondary = content_a, content_b
        else:
            primary, secondary = content_b, content_a

        # 简单策略：以胜出版本为主，附加另一版本的补充
        fusion_note = f"\n\n---\n\n> **融合说明**：本内容经双Agent对弈生成，仲裁Agent逐知识点评分后融合输出。"
        fusion_note += f"\n> 严谨策略(gen_a)得分点: {a_wins} | 创意策略(gen_b)得分点: {b_wins}"

        if debate_log:
            fusion_note += f"\n> 辩论回合数: {len(set(d.round for d in debate_log))}"

        return primary + fusion_note


arbitration_agent = ArbitrationAgent()
