"""共享Pydantic Schema。所有Agent间通信使用结构化Schema。"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AgentException(Exception):
    def __init__(self, agent_name: str, message: str, original_error: Optional[Exception] = None):
        self.agent_name = agent_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{agent_name}] {message}")


# ===== 用户 =====
class UserRegister(BaseModel):
    username: str; phone: str = ""; email: str = ""
    password: str; code: str = ""

class UserLogin(BaseModel):
    account: str; password: str

class UserInfo(BaseModel):
    id: str = ""; username: str = "用户昵称"; email: str = ""; phone: str = ""
    avatar: str = ""; role: str = "student"
    learning_direction: list[str] = Field(default_factory=list)
    learning_mode: str = "balanced"
    created_at: str = ""

class UserSettings(BaseModel):
    content_detail: str = "standard"
    code_ratio: int = 50
    notify_email: bool = True; notify_sms: bool = False; notify_app: bool = True

# ===== 学情画像 =====
class LearnerProfileInput(BaseModel):
    background: str = ""
    self_assessment: dict = Field(default_factory=dict)
    pre_test_results: dict = Field(default_factory=dict)
    learning_goals: list[str] = Field(default_factory=list)

class LearnerProfile(BaseModel):
    user_id: str = ""
    comprehensive_score: float = 50
    ability_level: str = "beginner"
    knowledge_breadth: float = Field(default=0.5, ge=0, le=1)
    knowledge_depth: float = Field(default=0.5, ge=0, le=1)
    learning_style: str = "balanced"
    engineering_ability: float = Field(default=0.3, ge=0, le=1)
    cognitive_load: float = Field(default=0.3, ge=0, le=1)
    innovation_ability: float = Field(default=0.3, ge=0, le=1)
    dimension_scores: dict = Field(default_factory=dict)
    knowledge_blindspots: list[str] = Field(default_factory=list)
    strength_areas: list[str] = Field(default_factory=list)

# ===== 知识库 =====
class KnowledgeChunk(BaseModel):
    chunk_id: str; document_id: str; title: str; content: str
    domain: str = ""; difficulty: str = "medium"
    similarity_score: float = 0.0; credibility: float = 0.8
    keywords: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

class RetrievalRequest(BaseModel):
    query: str; learner_profile: Optional[LearnerProfile] = None
    top_k: int = 10; domain: str = ""

class RetrievalResult(BaseModel):
    chunks: list[KnowledgeChunk]; query_analysis: dict = Field(default_factory=dict)

# ===== 生成 =====
class GeneratedContent(BaseModel):
    agent_id: str = ""; strategy: str = ""
    lecture_notes: str = ""; practice_guide: str = ""
    quiz_questions: list[dict] = Field(default_factory=list)
    knowledge_points_covered: list[str] = Field(default_factory=list)
    source_references: list[dict] = Field(default_factory=list)

class KnowledgePointScore(BaseModel):
    knowledge_point: str; score_a: float = 0; score_b: float = 0
    consistency: float = 0; winner: str = ""; reason: str = ""

class ArbitrationResult(BaseModel):
    knowledge_point_scores: list[KnowledgePointScore] = Field(default_factory=list)
    debate_triggered: bool = False; debate_rounds: int = 0
    debate_log: list[dict] = Field(default_factory=list)
    confidence_scores: dict = Field(default_factory=dict)

class DebateArgument(BaseModel):
    agent_id: str; knowledge_point: str; argument: str
    source_quote: str = ""; source_chunk_id: str = ""; round: int = 0

# ===== 会话 =====
class SessionState(BaseModel):
    session_id: str = ""
    learner_profile: Optional[LearnerProfile] = None
    retrieved_chunks: list[KnowledgeChunk] = Field(default_factory=list)
    gen_a_output: Optional[GeneratedContent] = None
    gen_b_output: Optional[GeneratedContent] = None
    comparison_result: Optional[ArbitrationResult] = None
    debate_round: int = 0
    debate_history: list[dict] = Field(default_factory=list)
    final_output: Optional[GeneratedContent] = None
    confidence_scores: dict = Field(default_factory=dict)
    source_traces: list[dict] = Field(default_factory=list)
    interaction_log: list[dict] = Field(default_factory=list)
    status: str = "init"; error_message: str = ""

class SessionResult(BaseModel):
    session_id: str; status: str = ""
    learner_profile: Optional[LearnerProfile] = None
    final_content: Optional[GeneratedContent] = None
    debate_summary: dict = Field(default_factory=dict)
    confidence_scores: dict = Field(default_factory=dict)
    source_traces: list[dict] = Field(default_factory=list)

class InteractionRequest(BaseModel):
    interaction_type: str = "answer"
    content: dict = Field(default_factory=dict)
    session_id: str = ""

class InteractionResponse(BaseModel):
    response_type: str = "巩固练习"
    content: str = ""; analysis: dict = Field(default_factory=dict)

# ===== 统一响应 =====
class APIResponse(BaseModel):
    code: int = 0; message: str = "success"
    data: Optional[dict] = None; request_id: str = ""
