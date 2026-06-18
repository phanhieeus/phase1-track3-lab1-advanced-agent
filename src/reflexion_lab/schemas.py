from __future__ import annotations
from typing import Literal, Optional, TypedDict
from pydantic import BaseModel, ConfigDict, Field

class ContextChunk(BaseModel):
    title: str
    text: str

class QAExample(BaseModel):
    qid: str
    difficulty: Literal["easy", "medium", "hard"]
    question: str
    gold_answer: str
    context: list[ContextChunk]

class JudgeResult(BaseModel):
    # Phương án B: nhị phân + validated, robust với JSON từ LLM (xem docs mục 4.1.1)
    model_config = ConfigDict(extra="ignore")
    score: Literal[0, 1]                                       # đường đúng/sai → required
    reason: str                                               # nguồn cho ReflectionEntry.failure_reason → required
    missing_evidence: list[str] = Field(default_factory=list)  # mock bỏ qua khi score=1 → phải có default
    spurious_claims: list[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class ReflectionEntry(BaseModel):
    # Phương án B: next_strategy là field then chốt (required); field mô tả fail-safe (default)
    model_config = ConfigDict(extra="ignore")
    attempt_id: int
    next_strategy: str                                        # được append vào reflection_memory → required
    failure_reason: str = ""                                  # mô tả cho report → fail-safe
    lesson: str = ""

class Usage(BaseModel):
    # Số liệu thật trả về từ một lời gọi LLM (mock sinh giá trị giả lập tương đương).
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0

class AttemptTrace(BaseModel):
    attempt_id: int
    answer: str
    score: int
    reason: str
    reflection: Optional[ReflectionEntry] = None
    token_estimate: int = 0
    latency_ms: int = 0

class RunRecord(BaseModel):
    qid: str
    question: str
    gold_answer: str
    agent_type: Literal["react", "reflexion"]
    predicted_answer: str
    is_correct: bool
    attempts: int
    token_estimate: int
    latency_ms: int
    failure_mode: Literal["none", "entity_drift", "incomplete_multi_hop", "wrong_final_answer", "looping", "reflection_overfit"]
    reflections: list[ReflectionEntry] = Field(default_factory=list)
    traces: list[AttemptTrace] = Field(default_factory=list)

class ReportPayload(BaseModel):
    meta: dict
    summary: dict
    failure_modes: dict
    examples: list[dict]
    extensions: list[str]
    discussion: str

class ReflexionState(TypedDict):
    question: str
    context: list[str]
    trajectory: list[str]
    reflection_memory: list[str]
    attempt_count: int
    success: bool
    final_answer: str
