"""双生成Agent —— 双Agent独立生成内容，策略互异"""

import json
import logging
from pathlib import Path
from shared.schemas import LearnerProfile, KnowledgeChunk, GeneratedContent, AgentException
from shared.llm import LLMClient
from shared.config import settings
from shared.utils import generate_id

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"


class GenerationAgent:
    """内容生成Agent基类"""

    def __init__(self, agent_id: str, model: str, temperature: float, strategy: str):
        self.agent_id = agent_id
        self.strategy = strategy
        self.llm = LLMClient(
            model=model,
            temperature=temperature,
            max_tokens=4096,
            timeout=settings.llm_timeout,
        )

    async def generate(
        self, profile: LearnerProfile, knowledge_chunks: list[KnowledgeChunk]
    ) -> GeneratedContent:
        """生成个性化学习内容。"""
        try:
            system_prompt = self._load_system_prompt()
            user_prompt = self._build_user_prompt(profile, knowledge_chunks)
            response = await self.llm.invoke(system_prompt, user_prompt)
            return self._parse_response(response)
        except AgentException:
            raise
        except Exception as e:
            logger.error("生成Agent[%s]失败: %s", self.agent_id, e, exc_info=True)
            raise AgentException(f"DGS-{self.agent_id}", str(e))

    def _load_system_prompt(self) -> str:
        filename = "gen_a_rigorous.txt" if self.strategy == "rigorous" else "gen_b_creative.txt"
        prompt_path = PROMPT_DIR / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return _RIGOROUS_PROMPT if self.strategy == "rigorous" else _CREATIVE_PROMPT

    def _build_user_prompt(
        self, profile: LearnerProfile, knowledge_chunks: list[KnowledgeChunk]
    ) -> str:
        chunks_text = "\n\n---\n\n".join(
            f"[来源: {c.title}]\n{c.content}" for c in knowledge_chunks[:10]
        )
        return f"""## 学习者画像
- 知识广度: {profile.knowledge_breadth:.2f}
- 知识深度: {profile.knowledge_depth:.2f}
- 学习风格: {profile.learning_style}
- 工程能力: {profile.engineering_ability:.2f}
- 认知负荷: {profile.cognitive_load:.2f}
- 知识盲区: {', '.join(profile.knowledge_blindspots) if profile.knowledge_blindspots else '无'}
- 优势领域: {', '.join(profile.strength_areas) if profile.strength_areas else '无'}

## 知识库素材
{chunks_text}

请根据以上信息生成个性化学习内容。"""

    def _parse_response(self, response: str) -> GeneratedContent:
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
            else:
                data = json.loads(response)
        except json.JSONDecodeError:
            data = {
                "lecture_notes": response[:2000],
                "practice_guide": "请参考讲义内容进行练习。",
                "quiz_questions": [],
                "knowledge_points_covered": [],
                "source_references": [],
            }

        return GeneratedContent(
            agent_id=self.agent_id,
            strategy=self.strategy,
            lecture_notes=data.get("lecture_notes", ""),
            practice_guide=data.get("practice_guide", ""),
            quiz_questions=data.get("quiz_questions", []),
            knowledge_points_covered=data.get("knowledge_points_covered", []),
            source_references=data.get("source_references", []),
        )


_RIGOROUS_PROMPT = """你是一个专业严谨的领域知识生成专家（策略：严谨推理，低温）。

## 核心原则
1. **知识库约束**：所有生成内容必须在提供的知识库素材中有段落级依据，不得自由发挥
2. **逻辑严谨**：概念定义准确、推理步骤完整、示例与知识点严格对应
3. **难度匹配**：根据学习者画像调整内容的深度和广度

## 输出格式
严格返回JSON格式，包含以下字段：
{
  "lecture_notes": "<Markdown格式的定制化讲义，包含概念讲解、原理分析、代码示例>",
  "practice_guide": "<实操指南，包含环境准备、步骤说明、预期输出、常见错误>",
  "quiz_questions": [
    {"type": "single_choice|multi_choice|fill_blank|coding", "difficulty": "easy|medium|hard", "question": "...", "answer": "...", "analysis": "..."}
  ],
  "knowledge_points_covered": ["知识点1", "知识点2"],
  "source_references": [{"chunk_id": "...", "title": "...", "used_in": "段落描述"}]
}
"""

_CREATIVE_PROMPT = """你是一个创意启发的领域知识引导专家（策略：创意引导，高温）。

## 核心原则
1. **实操优先**：以真实项目场景为出发点，引导学习者"做中学"
2. **启发式引导**：多用提问、类比、场景化描述，激发学习兴趣
3. **知识库约束**：所有内容仍在知识库范围内，但可以用更生动的案例和故事化表达
4. **难度匹配**：根据学习者画像调整引导方式

## 输出格式
严格返回JSON格式：
{
  "lecture_notes": "<Markdown格式的讲义，以项目场景引入，包含生动案例和类比>",
  "practice_guide": "<启发式实操指南，包含挑战任务、提示(hint)、扩展思考>",
  "quiz_questions": [
    {"type": "scenario|open_ended|coding", "difficulty": "easy|medium|hard", "question": "...", "answer_guide": "...", "thinking_prompt": "..."}
  ],
  "knowledge_points_covered": ["知识点1", "知识点2"],
  "source_references": [{"chunk_id": "...", "title": "...", "used_in": "段落描述"}]
}
"""

# 全局实例
generation_agent_a = GenerationAgent("gen_a", settings.dgs_model_a, settings.dgs_temperature_a, "rigorous")
generation_agent_b = GenerationAgent("gen_b", settings.dgs_model_b, settings.dgs_temperature_b, "creative")
