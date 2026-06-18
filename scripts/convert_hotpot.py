"""Chuyển HotpotQA (distractor) -> định dạng QAExample của lab, lấy mẫu ngẫu nhiên.

HotpotQA record: {_id, question, answer, type, level, supporting_facts, context}
  - context: list[[title, [sent1, sent2, ...]]]
QAExample (lab): {qid, difficulty(easy|medium|hard), question, gold_answer, context:[{title,text}]}

Cách dùng:
  python scripts/convert_hotpot.py \
      --src data/hotpot_dev_distractor_v1.json \
      --out data/hotpot_dev_100.json \
      --n 100 --seed 42
"""
from __future__ import annotations
import argparse
import json
import random
from collections import Counter
from pathlib import Path

# Cho phép import package của lab để validate.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.reflexion_lab.schemas import QAExample  # noqa: E402

ALLOWED = {"easy", "medium", "hard"}


def to_qaexample(rec: dict, idx: int) -> dict:
    level = rec.get("level")
    difficulty = level if level in ALLOWED else "medium"  # guard nếu thiếu/khác
    context = [
        {"title": title, "text": " ".join(sents).strip()}
        for title, sents in rec.get("context", [])
    ]
    return {
        "qid": rec.get("_id") or f"hotpot_{idx}",
        "difficulty": difficulty,
        "question": rec["question"],
        "gold_answer": rec["answer"],
        "context": context,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="data/hotpot_dev_distractor_v1.json")
    ap.add_argument("--out", default="data/hotpot_dev_100.json")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    raw = json.loads(Path(args.src).read_text(encoding="utf-8"))
    n = min(args.n, len(raw))
    random.seed(args.seed)
    sample = random.sample(raw, n)

    examples = [to_qaexample(rec, i) for i, rec in enumerate(sample)]
    # Validate từng mẫu bằng schema của lab (fail sớm nếu sai định dạng).
    for ex in examples:
        QAExample.model_validate(ex)

    Path(args.out).write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8")

    dist = Counter(ex["difficulty"] for ex in examples)
    ctx = sum(len(ex["context"]) for ex in examples) / len(examples)
    print(f"Wrote {len(examples)} examples -> {args.out}")
    print(f"  difficulty: {dict(dist)}")
    print(f"  avg context passages per question: {ctx:.1f}")
    print(f"  seed={args.seed} (change seed for a different sample)")


if __name__ == "__main__":
    main()
