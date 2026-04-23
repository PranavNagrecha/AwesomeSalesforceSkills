#!/usr/bin/env python3
"""Heuristic checker for Agentforce token-cost risks.

Scans topic definitions (markdown or JSON) for:
- Instructions over a configurable token budget (approximate via word count).
- Excessive examples (> 5).
- Absence of explicit out-of-scope section (often correlates with bloat).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


APPROX_TOKENS_PER_WORD = 1.35


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect topic definitions for token-cost risks.",
    )
    parser.add_argument(
        "--topics-dir",
        default=".",
        help="Directory containing topic markdown or JSON files.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=500,
        help="Max target tokens per topic instruction (default: 500).",
    )
    return parser.parse_args()


def approx_tokens(text: str) -> int:
    return int(len(text.split()) * APPROX_TOKENS_PER_WORD)


def extract_instructions(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
            return json.dumps(data.get("instructions", data))
        except json.JSONDecodeError:
            return text
    return text


def check_file(path: Path, max_tokens: int) -> list[str]:
    issues: list[str] = []
    text = extract_instructions(path)
    tokens = approx_tokens(text)

    if tokens > max_tokens:
        issues.append(f"{path}: topic instructions ≈ {tokens} tokens (budget {max_tokens})")

    example_count = text.lower().count("example")
    if example_count > 7:
        issues.append(f"{path}: {example_count} 'example' occurrences — likely too many examples")

    if "out-of-scope" not in text.lower() and "does not do" not in text.lower():
        issues.append(f"{path}: no explicit out-of-scope section — usually correlates with instruction bloat")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.topics_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md")) + list(root.rglob("*.json"))
    if not targets:
        print("No topic files found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path, args.max_tokens))

    if not all_issues:
        print("No token-cost risks detected.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
