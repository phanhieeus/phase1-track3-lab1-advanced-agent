"""Backend LLM thật — thay thế `mock_runtime.py` (Bước B4).

Mỗi hàm giữ đúng vai trò và tham số như mock, nhưng trả về thêm `Usage` (token/latency
thật) để `agents.py` ghi vào trace (B5). Parse output có nhánh fallback (3b): JSON hỏng
không làm sập cả benchmark.

Bật backend này bằng biến môi trường: REFLEXION_BACKEND=llm
"""
from __future__ import annotations
import json
import re
from .llm_client import chat
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
from .schemas import JudgeResult, QAExample, ReflectionEntry, Usage

# Backend LLM không biết trước "gold failure mode" nên để agents.py suy ra (mặc định wrong_final_answer).
FAILURE_MODE_BY_QID: dict[str, str] = {}

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)
_FINAL_RE = re.compile(r"final answer\s*:\s*(.+)", re.IGNORECASE | re.DOTALL)


def _format_context(example: QAExample) -> str:
    return "\n".join(f"- {c.title}: {c.text}" for c in example.context)


def _extract_json(text: str) -> dict:
    """Trích object JSON đầu tiên trong text (LLM đôi khi bọc ```json hoặc thêm chữ)."""
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError("no JSON object found")
    return json.loads(match.group(0))


def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> tuple[str, Usage]:
    memory_block = ""
    if reflection_memory:
        lessons = "\n".join(f"- {m}" for m in reflection_memory)
        memory_block = f"\n\nREFLECTION MEMORY (lessons from your previous failed attempts):\n{lessons}"
    user = (
        f"QUESTION:\n{example.question}\n\n"
        f"CONTEXT:\n{_format_context(example)}"
        f"{memory_block}"
    )
    text, usage = chat(ACTOR_SYSTEM, user, temperature=0.0)
    match = _FINAL_RE.search(text)
    answer = match.group(1).strip() if match else text.strip()
    # Lấy dòng đầu của phần answer, tránh model viết lan man sau câu trả lời.
    answer = answer.splitlines()[0].strip() if answer else answer
    return answer, usage


def evaluator(example: QAExample, answer: str) -> tuple[JudgeResult, Usage]:
    user = (
        f"QUESTION:\n{example.question}\n\n"
        f"GOLD ANSWER:\n{example.gold_answer}\n\n"
        f"PREDICTED ANSWER:\n{answer}"
    )
    text, usage = chat(EVALUATOR_SYSTEM, user, temperature=0.0, json_mode=True)
    try:
        data = _extract_json(text)
        return JudgeResult.model_validate(data), usage
    except Exception:
        # Fallback an toàn: coi như sai, giữ benchmark tiếp tục chạy.
        return JudgeResult(score=0, reason=f"parse_error: {text[:160]}"), usage


def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> tuple[ReflectionEntry, Usage]:
    user = (
        f"ATTEMPT #{attempt_id} was judged WRONG.\n\n"
        f"QUESTION:\n{example.question}\n\n"
        f"CONTEXT:\n{_format_context(example)}\n\n"
        f"JUDGE REASONING:\n{judge.reason}"
    )
    text, usage = chat(REFLECTOR_SYSTEM, user, temperature=0.4, json_mode=True)
    try:
        data = _extract_json(text)
        data.pop("attempt_id", None)  # attempt_id do code set, không tin từ LLM
        return ReflectionEntry(attempt_id=attempt_id, **data), usage
    except Exception:
        return (
            ReflectionEntry(
                attempt_id=attempt_id,
                next_strategy="Suy luận lại từng hop một cách tường minh, bám sát từng đoạn context.",
                failure_reason=judge.reason,
            ),
            usage,
        )
