from __future__ import annotations
from .schemas import QAExample, JudgeResult, ReflectionEntry, Usage
from .utils import normalize_answer

FIRST_ATTEMPT_WRONG = {"hp2": "London", "hp4": "Atlantic Ocean", "hp6": "Red Sea", "hp8": "Andes"}
FAILURE_MODE_BY_QID = {"hp2": "incomplete_multi_hop", "hp4": "wrong_final_answer", "hp6": "entity_drift", "hp8": "entity_drift"}


def _usage(total: int, latency: int) -> Usage:
    # Số liệu giả lập, deterministic — đủ để report mock có token/latency hợp lý.
    completion = min(24, total)
    return Usage(prompt_tokens=total - completion, completion_tokens=completion, total_tokens=total, latency_ms=latency)


def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> tuple[str, Usage]:
    bump = 40 if agent_type == "reflexion" else 0
    usage = _usage(300 + attempt_id * 60 + bump, 150 + attempt_id * 30 + (20 if agent_type == "reflexion" else 0))
    if example.qid not in FIRST_ATTEMPT_WRONG:
        return example.gold_answer, usage
    if agent_type == "react":
        return FIRST_ATTEMPT_WRONG[example.qid], usage
    if attempt_id == 1 and not reflection_memory:
        return FIRST_ATTEMPT_WRONG[example.qid], usage
    return example.gold_answer, usage


def evaluator(example: QAExample, answer: str) -> tuple[JudgeResult, Usage]:
    usage = _usage(120, 80)
    if normalize_answer(example.gold_answer) == normalize_answer(answer):
        return JudgeResult(score=1, reason="Final answer matches the gold answer after normalization."), usage
    if normalize_answer(answer) == "london":
        return JudgeResult(score=0, reason="The answer stopped at the birthplace city and never completed the second hop to the river.", missing_evidence=["Need to identify the river that flows through London."], spurious_claims=[]), usage
    return JudgeResult(score=0, reason="The final answer selected the wrong second-hop entity.", missing_evidence=["Need to ground the answer in the second paragraph."], spurious_claims=[answer]), usage


def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> tuple[ReflectionEntry, Usage]:
    usage = _usage(90, 70)
    strategy = "Do the second hop explicitly: birthplace city -> river through that city." if example.qid == "hp2" else "Verify the final entity against the second paragraph before answering."
    entry = ReflectionEntry(attempt_id=attempt_id, failure_reason=judge.reason, lesson="A partial first-hop answer is not enough; the final answer must complete all hops.", next_strategy=strategy)
    return entry, usage
