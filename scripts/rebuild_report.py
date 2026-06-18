"""Dựng lại report.json/report.md từ các file *_runs.jsonl đã lưu — KHÔNG gọi lại LLM.

Dùng khi logic reporting thay đổi (vd phân loại failure mode mới, discussion động) và
muốn cập nhật report cho một lần chạy đã tốn API trước đó.

  python scripts/rebuild_report.py --runs-dir outputs/llm_100
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.reflexion_lab.reporting import build_report, save_report  # noqa: E402
from src.reflexion_lab.schemas import RunRecord  # noqa: E402


def load_runs(path: Path) -> list[RunRecord]:
    if not path.exists():
        return []
    return [RunRecord.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", required=True, help="Thư mục chứa react_runs.jsonl / reflexion_runs.jsonl")
    ap.add_argument("--dataset", default=None, help="Tên dataset (mặc định lấy từ report.json cũ)")
    ap.add_argument("--mode", default=None, help="mock|llm (mặc định lấy từ report.json cũ)")
    args = ap.parse_args()

    d = Path(args.runs_dir)
    records = load_runs(d / "react_runs.jsonl") + load_runs(d / "reflexion_runs.jsonl")
    if not records:
        raise SystemExit(f"Không tìm thấy record nào trong {d}")

    dataset = args.dataset
    mode = args.mode
    old = d / "report.json"
    if (dataset is None or mode is None) and old.exists():
        meta = json.loads(old.read_text(encoding="utf-8")).get("meta", {})
        dataset = dataset or meta.get("dataset", d.name)
        mode = mode or meta.get("mode", "llm")

    report = build_report(records, dataset_name=dataset or d.name, mode=mode or "llm")
    json_path, md_path = save_report(report, d)
    print(f"Rebuilt {json_path} ({len(records)} records)")
    print(f"  failure_modes: {report.failure_modes}")
    print(f"  discussion len: {len(report.discussion)}")


if __name__ == "__main__":
    main()
