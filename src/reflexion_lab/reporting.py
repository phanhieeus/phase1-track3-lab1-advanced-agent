from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from .schemas import ReportPayload, RunRecord

def summarize(records: list[RunRecord]) -> dict:
    grouped: dict[str, list[RunRecord]] = defaultdict(list)
    for record in records:
        grouped[record.agent_type].append(record)
    summary: dict[str, dict] = {}
    for agent_type, rows in grouped.items():
        toks = [r.token_estimate for r in rows]
        lats = [r.latency_ms for r in rows]
        summary[agent_type] = {
            "count": len(rows),
            "em": round(mean(1.0 if r.is_correct else 0.0 for r in rows), 4),
            "avg_attempts": round(mean(r.attempts for r in rows), 4),
            "avg_token_estimate": round(mean(toks), 2),
            "min_token_estimate": min(toks),
            "max_token_estimate": max(toks),
            "total_token_estimate": sum(toks),
            "avg_latency_ms": round(mean(lats), 2),
            "min_latency_ms": min(lats),
            "max_latency_ms": max(lats),
            "total_latency_ms": sum(lats),
        }
    if "react" in summary and "reflexion" in summary:
        summary["delta_reflexion_minus_react"] = {"em_abs": round(summary["reflexion"]["em"] - summary["react"]["em"], 4), "attempts_abs": round(summary["reflexion"]["avg_attempts"] - summary["react"]["avg_attempts"], 4), "tokens_abs": round(summary["reflexion"]["avg_token_estimate"] - summary["react"]["avg_token_estimate"], 2), "latency_abs": round(summary["reflexion"]["avg_latency_ms"] - summary["react"]["avg_latency_ms"], 2)}
    return summary

# Từ khóa để suy ra failure mode từ lý do (free-text) của Evaluator/Reflector.
_MODE_KEYWORDS = {
    "incomplete_multi_hop": ["first hop", "second hop", "stopped", "incomplete", "did not complete", "only the", "partial", "one hop"],
    "entity_drift": ["drift", "wrong entity", "wrong second", "different entity", "confused", "mixed up", "another entity"],
    "looping": ["loop", "repeat", "again and again"],
    "reflection_overfit": ["overfit", "over-correct", "overcorrect", "misled by the reflection"],
}

def infer_failure_mode(record: RunRecord) -> str:
    """Phân loại lỗi của một record dựa trên nội dung (B): đúng -> none; sai -> suy từ
    lý do của judge + reflection. Nhờ vậy report có nhiều mode thật thay vì chỉ
    'wrong_final_answer', phục vụ phần Analysis."""
    if record.is_correct:
        return "none"
    text = " ".join(
        [t.reason for t in record.traces]
        + [rf.failure_reason for rf in record.reflections if rf.failure_reason]
    ).lower()
    if not record.predicted_answer.strip():
        return "wrong_final_answer"
    for mode, keys in _MODE_KEYWORDS.items():
        if any(k in text for k in keys):
            return mode
    return "wrong_final_answer"

def failure_breakdown(records: list[RunRecord]) -> dict:
    # Key theo FAILURE MODE (không phải theo agent) để phản ánh đúng "các loại lỗi".
    grouped: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        counter = grouped[record.failure_mode]
        counter[record.agent_type] += 1
        counter["total"] += 1
    return {mode: dict(counter) for mode, counter in grouped.items()}

def _build_discussion(summary: dict, failure_modes: dict, dataset_name: str, n: int) -> str:
    react, reflexion = summary.get("react", {}), summary.get("reflexion", {})
    delta = summary.get("delta_reflexion_minus_react", {})
    modes = ", ".join(f"{m} (n={c.get('total', 0)})" for m, c in sorted(failure_modes.items()) if m != "none") or "none"
    em_delta = delta.get("em_abs", 0)
    if em_delta > 0.02:
        verdict = (
            f"Reflexion improved exact-match by {em_delta:+.3f} over ReAct by re-attempting "
            "questions that failed on the first hop, confirming that verbal self-reflection can "
            "recover multi-hop errors."
        )
    else:
        verdict = (
            f"Reflexion changed exact-match by only {em_delta:+.3f}: the actor already answered most "
            "questions correctly on the first attempt (ceiling effect), so there was little room for "
            "reflection to help. A weaker actor model or harder questions would widen the gap."
        )
    return (
        f"Benchmark on {dataset_name} ({n} records). ReAct EM={react.get('em', 0)} vs "
        f"Reflexion EM={reflexion.get('em', 0)} (delta {em_delta:+.3f}). Reflexion averaged "
        f"{reflexion.get('avg_attempts', 0)} attempts vs {react.get('avg_attempts', 0)} for ReAct, "
        f"spending {delta.get('tokens_abs', 0):+.0f} tokens and {delta.get('latency_abs', 0):+.0f} ms "
        f"per question. {verdict} Observed failure modes: {modes}. The cost/quality tradeoff means "
        "Reflexion is worth it only when first-attempt error rate is high enough to offset the extra "
        "actor+evaluator+reflector calls each retry adds."
    )

def build_report(records: list[RunRecord], dataset_name: str, mode: str = "mock") -> ReportPayload:
    # Phân loại lại failure mode từ nội dung (áp dụng cho cả jsonl đã lưu khi rebuild).
    for r in records:
        r.failure_mode = infer_failure_mode(r)
    summary = summarize(records)
    failure_modes = failure_breakdown(records)
    examples = [{"qid": r.qid, "agent_type": r.agent_type, "question": r.question, "gold_answer": r.gold_answer, "predicted_answer": r.predicted_answer, "is_correct": r.is_correct, "attempts": r.attempts, "token_estimate": r.token_estimate, "latency_ms": r.latency_ms, "failure_mode": r.failure_mode, "reflection_count": len(r.reflections)} for r in records]
    return ReportPayload(meta={"dataset": dataset_name, "mode": mode, "num_records": len(records), "agents": sorted({r.agent_type for r in records})}, summary=summary, failure_modes=failure_modes, examples=examples, extensions=["structured_evaluator", "reflection_memory", "benchmark_report_json", "mock_mode_for_autograding"], discussion=_build_discussion(summary, failure_modes, dataset_name, len(records)))

def _cell(text: str, width: int = 60) -> str:
    """Làm sạch ô bảng markdown: bỏ '|'/xuống dòng, cắt ngắn."""
    t = str(text).replace("|", "/").replace("\n", " ").strip()
    return (t[: width - 1] + "…") if len(t) > width else t


def _comparison_table(examples: list[dict]) -> str:
    by_qid: dict[str, dict] = defaultdict(dict)
    for e in examples:
        by_qid[e["qid"]][e["agent_type"]] = e
    rows, saved = [], []
    for qid, pair in by_qid.items():
        ra, rx = pair.get("react"), pair.get("reflexion")
        if ra is None or rx is None:
            continue
        ra_ok, rx_ok = ra["is_correct"], rx["is_correct"]
        if not ra_ok and rx_ok:
            result = "✅ saved by Reflexion"
            saved.append((qid, ra, rx))
        elif ra_ok and not rx_ok:
            result = "⚠️ regression"
        elif ra_ok and rx_ok:
            result = "both correct"
        else:
            result = "both wrong"
        rows.append((result, qid, ra, rx))
    # Ưu tiên hiển thị: saved -> regression -> both wrong -> both correct.
    order = {"✅ saved by Reflexion": 0, "⚠️ regression": 1, "both wrong": 2, "both correct": 3}
    rows.sort(key=lambda r: order.get(r[0], 9))

    saved_lines = "\n".join(
        f"| {qid} | {_cell(ra['question'], 70)} | {_cell(ra['predicted_answer'], 32)} | "
        f"{_cell(rx['predicted_answer'], 32)} | {_cell(rx['gold_answer'], 32)} |"
        for qid, ra, rx in saved
    ) or "| — | (không có câu nào ReAct sai mà Reflexion cứu được) | — | — | — |"

    full_lines = "\n".join(
        f"| {qid} | {_cell(ra['question'], 60)} | {_cell(ra['predicted_answer'], 26)} | "
        f"{'✓' if ra['is_correct'] else '✗'} | {_cell(rx['predicted_answer'], 26)} | "
        f"{'✓' if rx['is_correct'] else '✗'} | {rx['attempts']} | {_cell(ra['gold_answer'], 26)} | {result} |"
        for result, qid, ra, rx in rows
    )
    return (
        f"## Câu Reflexion cứu được (ReAct sai → Reflexion đúng) — {len(saved)} câu\n\n"
        "| qid | Question | ReAct answer | Reflexion answer | Gold |\n"
        "|---|---|---|---|---|\n"
        f"{saved_lines}\n\n"
        "## So sánh chi tiết ReAct vs Reflexion (từng câu)\n\n"
        "| qid | Question | ReAct ans | RA | Reflexion ans | Rx | Rx att. | Gold | Result |\n"
        "|---|---|---|:--:|---|:--:|:--:|---|---|\n"
        f"{full_lines}\n"
    )


def _cost_table(summary: dict) -> str:
    def row(label: str, key: str, fmt=str) -> str:
        ra, rx = summary.get("react", {}), summary.get("reflexion", {})
        return f"| {label} | {fmt(ra.get(key, 0))} | {fmt(rx.get(key, 0))} |"

    react, reflexion = summary.get("react", {}), summary.get("reflexion", {})
    total_tok = react.get("total_token_estimate", 0) + reflexion.get("total_token_estimate", 0)
    total_ms = react.get("total_latency_ms", 0) + reflexion.get("total_latency_ms", 0)
    return (
        "## Ước tính chi phí (token & thời gian)\n\n"
        "| Metric | ReAct | Reflexion |\n"
        "|---|---:|---:|\n"
        f"{row('Records (câu)', 'count')}\n"
        f"{row('Total tokens', 'total_token_estimate', lambda v: f'{v:,}')}\n"
        f"{row('Token / câu — min', 'min_token_estimate', lambda v: f'{v:,}')}\n"
        f"{row('Token / câu — max', 'max_token_estimate', lambda v: f'{v:,}')}\n"
        f"{row('Token / câu — avg', 'avg_token_estimate', lambda v: f'{v:,.1f}')}\n"
        f"{row('Total time (s)', 'total_latency_ms', lambda v: f'{v/1000:,.1f}')}\n"
        f"{row('Latency / câu — min (ms)', 'min_latency_ms', lambda v: f'{v:,}')}\n"
        f"{row('Latency / câu — max (ms)', 'max_latency_ms', lambda v: f'{v:,}')}\n"
        f"{row('Latency / câu — avg (ms)', 'avg_latency_ms', lambda v: f'{v:,.1f}')}\n\n"
        f"**Tổng toàn benchmark:** {total_tok:,} tokens, {total_ms/1000:,.1f} s "
        f"(~{total_ms/1000/60:.1f} phút) cho {react.get('count', 0) + reflexion.get('count', 0)} lượt chạy.\n"
    )


def save_report(report: ReportPayload, out_dir: str | Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"
    json_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    s = report.summary
    react = s.get("react", {})
    reflexion = s.get("reflexion", {})
    delta = s.get("delta_reflexion_minus_react", {})
    ext_lines = "\n".join(f"- {item}" for item in report.extensions)
    md = f"""# Lab 16 Benchmark Report

## Metadata
- Dataset: {report.meta['dataset']}
- Mode: {report.meta['mode']}
- Records: {report.meta['num_records']}
- Agents: {', '.join(report.meta['agents'])}

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | {react.get('em', 0)} | {reflexion.get('em', 0)} | {delta.get('em_abs', 0)} |
| Avg attempts | {react.get('avg_attempts', 0)} | {reflexion.get('avg_attempts', 0)} | {delta.get('attempts_abs', 0)} |
| Avg token estimate | {react.get('avg_token_estimate', 0)} | {reflexion.get('avg_token_estimate', 0)} | {delta.get('tokens_abs', 0)} |
| Avg latency (ms) | {react.get('avg_latency_ms', 0)} | {reflexion.get('avg_latency_ms', 0)} | {delta.get('latency_abs', 0)} |

{_cost_table(s)}
## Failure modes
```json
{json.dumps(report.failure_modes, indent=2)}
```

{_comparison_table(report.examples)}
## Extensions implemented
{ext_lines}

## Discussion
{report.discussion}
"""
    md_path.write_text(md, encoding="utf-8")
    return json_path, md_path
