#!/usr/bin/env python3
"""Prepare a tiny LongMemEval sample for OpenClaw Neo4j Memory MVP experiments.

This script does not run benchmark evaluation. It only converts a small number
of LongMemEval instances into plain text files that can be fed into the current
`test_corpus_import.py` flow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def render_session(session_idx: int, turns: List[Dict[str, Any]], session_date: str = "") -> str:
    lines = []
    header = f"## Session {session_idx}"
    if session_date:
        header += f" ({session_date})"
    lines.append(header)
    for turn in turns:
        role = turn.get("role", "unknown")
        content = (turn.get("content") or "").strip()
        if not content:
            continue
        lines.append(f"[{role}] {content}")
    return "\n".join(lines)


def render_instance(instance: Dict[str, Any]) -> str:
    lines = [
        f"# LongMemEval Sample {instance.get('question_id', 'unknown')}",
        f"question_type: {instance.get('question_type', '')}",
        f"question_date: {instance.get('question_date', '')}",
        "",
        "## Evaluation Question",
        instance.get("question", ""),
        "",
        "## Reference Answer",
        instance.get("answer", ""),
        "",
        "## Conversation History",
    ]

    sessions = instance.get("haystack_sessions", [])
    dates = instance.get("haystack_dates", [])
    for idx, session in enumerate(sessions, start=1):
        session_date = dates[idx - 1] if idx - 1 < len(dates) else ""
        lines.append(render_session(idx, session, session_date=session_date))
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a tiny LongMemEval sample corpus")
    parser.add_argument("input", help="Path to LongMemEval json file")
    parser.add_argument("--output-dir", default="tmp/longmemeval-sample", help="Output directory")
    parser.add_argument("--limit", type=int, default=2, help="Number of instances to export")
    parser.add_argument("--question-type", default="", help="Optional question_type filter")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected a JSON list of LongMemEval instances")

    selected = []
    for item in data:
        if args.question_type and item.get("question_type") != args.question_type:
            continue
        selected.append(item)
        if len(selected) >= args.limit:
            break

    manifest = []
    for item in selected:
        qid = item.get("question_id", f"sample-{len(manifest)+1}")
        file_path = output_dir / f"{qid}.md"
        file_path.write_text(render_instance(item), encoding="utf-8")
        manifest.append({
            "question_id": qid,
            "question_type": item.get("question_type"),
            "question_date": item.get("question_date"),
            "output_file": str(file_path),
        })

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Prepared {len(manifest)} LongMemEval sample files in {output_dir}")
    for row in manifest:
        print(f"- {row['question_id']} -> {row['output_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
