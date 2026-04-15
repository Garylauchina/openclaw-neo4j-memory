#!/usr/bin/env python3
"""Minimal external-corpus import test script for the OpenClaw Neo4j Memory MVP.

This script is intentionally for experimentation, not full production migration.
It reads a text file or a directory of text-like files, splits content into chunks,
and feeds them into the current mainline memory ingest path.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from openclaw_memory_mvp import OpenClawMemoryMVP

TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".text"}


def iter_input_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in TEXT_EXTENSIONS:
            yield file_path


def chunk_text(text: str, chunk_chars: int) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    return [text[i:i + chunk_chars] for i in range(0, len(text), chunk_chars)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Test-import external corpus into Neo4j memory")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("--chunk-chars", type=int, default=1200, help="Chunk size in characters")
    parser.add_argument("--limit-files", type=int, default=0, help="Max number of files to process (0 = unlimited)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not write")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM extraction")
    parser.add_argument("--source-tag", default="external_corpus_test", help="Source tag for this import batch")
    parser.add_argument("--import-batch", default="", help="Explicit import batch id")
    args = parser.parse_args()

    target = Path(args.input).expanduser().resolve()
    if not target.exists():
        print(f"Input not found: {target}", file=sys.stderr)
        return 1

    files = list(iter_input_files(target))
    if args.limit_files > 0:
        files = files[:args.limit_files]

    if not files:
        print("No supported text files found.", file=sys.stderr)
        return 1

    total_files = 0
    total_chunks = 0
    total_entities = 0
    total_relations = 0
    import_batch = args.import_batch or f"{target.name}-{target.stat().st_mtime_ns}"

    memory = None
    if not args.dry_run:
        memory = OpenClawMemoryMVP()
        memory.init()

    try:
        for file_path in files:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            chunks = chunk_text(content, args.chunk_chars)
            if not chunks:
                continue

            total_files += 1
            print(f"\n# {file_path} -> {len(chunks)} chunks")
            for idx, chunk in enumerate(chunks, start=1):
                total_chunks += 1
                metadata = {
                    "source_path": str(file_path),
                    "source_tag": args.source_tag,
                    "import_batch": import_batch,
                    "chunk_index": idx,
                    "chunk_total": len(chunks),
                    "import_mode": "test_corpus_import",
                }
                if args.dry_run:
                    print(f"  - dry-run chunk {idx}/{len(chunks)} ({len(chunk)} chars)")
                    continue
                result = memory.ingest_memory(chunk, metadata=metadata, use_llm=not args.no_llm)
                data = result.get("data", {})
                total_entities += int(data.get("entities_written", 0) or 0)
                total_relations += int(data.get("relations_written", 0) or 0)
                print(
                    f"  - imported chunk {idx}/{len(chunks)}: "
                    f"entities={data.get('entities_written', 0)} relations={data.get('relations_written', 0)}"
                )
    finally:
        if memory is not None:
            memory.close()

    print("\n=== Summary ===")
    print(f"source_tag={args.source_tag}")
    print(f"import_batch={import_batch}")
    print(f"files={total_files}")
    print(f"chunks={total_chunks}")
    if not args.dry_run:
        print(f"entities_written={total_entities}")
        print(f"relations_written={total_relations}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
