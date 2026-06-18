from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Literal
from dotenv import load_dotenv
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord

# Nạp .env TRƯỚC khi đọc REFLEXION_BACKEND (nếu không, biến trong .env sẽ không kịp có hiệu lực).
load_dotenv()

# Chọn backend qua biến môi trường REFLEXION_BACKEND (mặc định "mock" để autograde
# chạy không cần API). Đặt =llm để dùng LLM thật (xem llm_runtime.py / llm_client.py).
BACKEND = os.getenv("REFLEXION_BACKEND", "mock").lower()
if BACKEND == "llm":
    from .llm_runtime import FAILURE_MODE_BY_QID, actor_answer, evaluator, reflector
else:
    from .mock_runtime import FAILURE_MODE_BY_QID, actor_answer, evaluator, reflector

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        for attempt_id in range(1, self.max_attempts + 1):
            answer, actor_usage = actor_answer(example, attempt_id, self.agent_type, reflection_memory)
            judge, judge_usage = evaluator(example, answer)
            # B5: token/latency THẬT, cộng dồn chi phí Actor + Evaluator của attempt này.
            token_estimate = actor_usage.total_tokens + judge_usage.total_tokens
            latency_ms = actor_usage.latency_ms + judge_usage.latency_ms
            trace = AttemptTrace(attempt_id=attempt_id, answer=answer, score=judge.score, reason=judge.reason, token_estimate=token_estimate, latency_ms=latency_ms)
            final_answer = answer
            final_score = judge.score
            if judge.score == 1:
                traces.append(trace)
                break
            
            # Phương án C: reflect khi còn attempt phía sau; ghi nhận đầy đủ +
            # nạp memo giàu ngữ cảnh (failure_reason + lesson + next_strategy) vào memory.
            if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
                reflection, refl_usage = reflector(example, attempt_id, judge)
                reflections.append(reflection)            # -> RunRecord.reflections (report đếm được)
                trace.reflection = reflection             # -> đính vào trace của attempt sai
                trace.token_estimate += refl_usage.total_tokens   # cộng cả cost của reflector
                trace.latency_ms += refl_usage.latency_ms
                memo = (
                    f"[Attempt {attempt_id}] Sai vì: {reflection.failure_reason}. "
                    f"Bài học: {reflection.lesson}. Lần sau: {reflection.next_strategy}"
                )
                reflection_memory.append(memo)            # Actor dùng cho attempt kế tiếp
            traces.append(trace)
        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        failure_mode = "none" if final_score == 1 else FAILURE_MODE_BY_QID.get(example.qid, "wrong_final_answer")
        return RunRecord(qid=example.qid, question=example.question, gold_answer=example.gold_answer, agent_type=self.agent_type, predicted_answer=final_answer, is_correct=bool(final_score), attempts=len(traces), token_estimate=total_tokens, latency_ms=total_latency, failure_mode=failure_mode, reflections=reflections, traces=traces)

class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts)
