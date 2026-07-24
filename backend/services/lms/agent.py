"""学情建模Agent —— 五维画像构建"""

import json
import logging
from pathlib import Path
from shared.schemas import LearnerProfile, LearnerProfileInput, AgentException
from shared.llm import LLMClient
from shared.config import settings
from services.lms.schemas import LMSConfig

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"


class LearnerModelingAgent:
    def __init__(self, config: LMSConfig | None = None):
        self.config = config or LMSConfig(
            model=settings.lms_model,
            temperature=settings.lms_temperature,
            timeout=settings.llm_timeout,
        )
        self.llm = LLMClient(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout,
        )

    async def analyze(self, input_data: LearnerProfileInput) -> LearnerProfile:
        """分析学习者，构建五维学情画像。"""
        try:
            system_prompt = self._load_prompt("lms_system.txt")
            user_prompt = self._build_user_prompt(input_data)
            response = await self.llm.invoke(system_prompt, user_prompt)
            return self._parse_response(response)
        except AgentException:
            raise
        except Exception as e:
            logger.error("学情建模失败: %s", e, exc_info=True)
            raise AgentException("LMS", str(e))

    def _load_prompt(self, filename: str) -> str:
        prompt_path = PROMPT_DIR / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return _DEFAULT_LMS_SYSTEM_PROMPT

    def _build_user_prompt(self, input_data: LearnerProfileInput) -> str:
        return f"""请分析以下学习者的学情信息，构建五维画像：

学历背景：{input_data.background}
自评数据：{json.dumps(input_data.self_assessment, ensure_ascii=False)}
前置测试结果：{json.dumps(input_data.pre_test_results, ensure_ascii=False)}
学习目标：{json.dumps(input_data.learning_goals or [], ensure_ascii=False)}

请严格以JSON格式返回五维画像分析结果。"""

    def _parse_response(self, response: str) -> LearnerProfile:
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
            else:
                data = json.loads(response)
        except json.JSONDecodeError:
            logger.warning("LLM返回非JSON格式，使用启发式解析")
            data = _heuristic_parse(response)

        return LearnerProfile(
            knowledge_breadth=float(data.get("knowledge_breadth", 0.5)),
            knowledge_depth=float(data.get("knowledge_depth", 0.5)),
            learning_style=data.get("learning_style", "balanced"),
            engineering_ability=float(data.get("engineering_ability", 0.5)),
            cognitive_load=float(data.get("cognitive_load", 0.3)),
            dimension_scores=data.get("dimension_scores", {}),
            knowledge_blindspots=data.get("knowledge_blindspots", []),
            strength_areas=data.get("strength_areas", []),
        )


def _heuristic_parse(text: str) -> dict:
    """启发式解析LLM返回的非JSON文本。"""
    import re
    result = {
        "knowledge_breadth": 0.5,
        "knowledge_depth": 0.5,
        "learning_style": "balanced",
        "engineering_ability": 0.5,
        "cognitive_load": 0.3,
        "dimension_scores": {},
        "knowledge_blindspots": [],
        "strength_areas": [],
    }
    for field in ["knowledge_breadth", "knowledge_depth", "engineering_ability", "cognitive_load"]:
        m = re.search(rf'"{field}"\s*:\s*([\d.]+)', text)
        if m:
            result[field] = max(0, min(1, float(m.group(1))))
    style_m = re.search(r'"learning_style"\s*:\s*"(\w+)"', text)
    if style_m:
        result["learning_style"] = style_m.group(1)
    return result


_DEFAULT_LMS_SYSTEM_PROMPT = """你是一个专业的学习者学情建模专家。你的任务是分析学习者的背景信息，构建五维学情画像。

## 五维画像定义

1. **知识广度** (knowledge_breadth, 0-1): 学习者已覆盖的知识域范围。0=零基础，1=广泛覆盖。
2. **知识深度** (knowledge_depth, 0-1): 每个知识域的理解深度。0=仅了解概念，1=能创新应用。
3. **学习风格** (learning_style): theory_first(理论先行), practice_first(实操先行), balanced(均衡)。
4. **工程能力** (engineering_ability, 0-1): 理论转化为实操的水平。0=无法动手，1=独立开发项目。
5. **认知负荷** (cognitive_load, 0-1): 当前学习节奏压力。0=轻松，1=严重过载。

## 输出要求

严格以JSON格式返回，包含以下字段：
{
  "knowledge_breadth": <float 0-1>,
  "knowledge_depth": <float 0-1>,
  "learning_style": "<theory_first|practice_first|balanced>",
  "engineering_ability": <float 0-1>,
  "cognitive_load": <float 0-1>,
  "dimension_scores": {<细分维度得分>},
  "knowledge_blindspots": ["<知识盲区1>", "<知识盲区2>", ...],
  "strength_areas": ["<优势领域1>", "<优势领域2>", ...]
}
"""

# 全局实例
learner_modeling_agent = LearnerModelingAgent()
