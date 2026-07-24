"""导学交互Agent —— 动态追问 + 适应性反馈 + 学习路径规划"""

import logging
from pathlib import Path
from shared.schemas import SessionState, InteractionRequest, InteractionResponse, AgentException
from shared.llm import LLMClient
from shared.config import settings

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"


class TutoringInteractionAgent:
    def __init__(self):
        self.llm = LLMClient(
            model=settings.tis_model,
            temperature=settings.tis_temperature,
            max_tokens=2048,
            timeout=settings.llm_timeout,
        )

    async def prepare_interaction(self, state: SessionState) -> dict:
        """准备交互上下文。"""
        return {
            "type": "interaction_ready",
            "session_id": state.session_id,
            "final_content_available": state.final_output is not None,
            "learning_style": state.learner_profile.learning_style if state.learner_profile else "balanced",
        }

    async def handle_interaction(self, request: InteractionRequest, state: SessionState) -> InteractionResponse:
        """处理学习交互（答题/追问），返回适应性反馈。"""
        try:
            if request.interaction_type == "answer":
                return await self._evaluate_answer(request.content, state)
            elif request.interaction_type == "question":
                return await self._handle_followup_question(request.content, state)
            elif request.interaction_type == "feedback":
                return await self._process_feedback(request.content, state)
            else:
                return InteractionResponse(
                    response_type="巩固练习",
                    content="请继续学习，如有疑问随时提出。",
                )
        except Exception as e:
            logger.error("导学交互失败: %s", e, exc_info=True)
            raise AgentException("TIS", str(e))

    async def _evaluate_answer(self, content: dict, state: SessionState) -> InteractionResponse:
        """评估学习者答案，决定下一步：降维解释/巩固练习/进阶挑战。"""
        is_correct = content.get("is_correct", False)
        question_difficulty = content.get("difficulty", "medium")
        attempt_count = content.get("attempt_count", 1)

        profile = state.learner_profile

        if not is_correct and attempt_count >= 2:
            return InteractionResponse(
                response_type="降维解释",
                content="看起来这个知识点还需要巩固。让我用更基础的方式重新解释一下...",
                analysis={"reason": "多次答错", "action": "降低难度，回到基础概念"},
            )
        elif not is_correct:
            return InteractionResponse(
                response_type="巩固练习",
                content="回答不太对，让我们换个角度理解这个问题...",
                analysis={"reason": "首次答错", "action": "提供提示，鼓励再试"},
            )
        elif question_difficulty == "hard" and profile and profile.knowledge_depth > 0.7:
            return InteractionResponse(
                response_type="进阶挑战",
                content="回答得很好！你已经掌握了这个难点，要不要挑战更深入的内容？",
                analysis={"reason": "高难度答对且深度>0.7", "action": "推荐进阶内容"},
            )
        else:
            return InteractionResponse(
                response_type="巩固练习",
                content="回答正确！让我们继续巩固，确保完全掌握。",
                analysis={"reason": "答对", "action": "继续下一知识点"},
            )

    async def _handle_followup_question(self, content: dict, state: SessionState) -> InteractionResponse:
        """处理学习者的追问。"""
        question = content.get("question", "")
        return InteractionResponse(
            response_type="巩固练习",
            content=f"关于「{question[:50]}」的问题，让我结合知识库为你详细解答...",
            analysis={"reason": "学习者主动追问", "action": "以当前知识点为基础扩展"},
        )

    async def _process_feedback(self, content: dict, state: SessionState) -> InteractionResponse:
        """处理学习者对内容的反馈。"""
        feedback_type = content.get("feedback_type", "too_hard")
        if feedback_type == "too_hard":
            return InteractionResponse(
                response_type="降维解释",
                content="理解，当前内容可能有些难度。让我调整讲解方式...",
                analysis={"reason": "学习者反馈太困难", "action": "降低难度"},
            )
        elif feedback_type == "too_easy":
            return InteractionResponse(
                response_type="进阶挑战",
                content="看来你已经掌握了这部分内容！让我推荐更有挑战性的材料。",
                analysis={"reason": "学习者反馈太简单", "action": "提高难度"},
            )
        return InteractionResponse(
            response_type="巩固练习",
            content="感谢反馈！我已经记录了你的学习偏好。",
        )


tutoring_agent = TutoringInteractionAgent()
