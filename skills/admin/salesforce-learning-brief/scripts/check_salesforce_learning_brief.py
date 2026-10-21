#!/usr/bin/env python3
"""Heuristically validate a learner-facing Salesforce brief.

Contract (audit 2026-10-21): --input <file> or --manifest-dir <dir of .md
briefs>. A missing path is ERROR, exit 1. Structural findings are WARN, exit 0
unless --strict. An empty directory prints one WARN, exit 0.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = (
    "learning outcome",
    "prerequisites",
    "mental model",
    "core concepts",
    "decision points",
    "recommended workflow",
    "worked example",
    "boundaries and caveats",
    "common failure modes",
    "knowledge check",
    "practice task",
    "do not teach as fact",
    "sources",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a Salesforce learning brief.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="One learning-brief markdown file.")
    group.add_argument("--manifest-dir", help="Directory of learning-brief .md files.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings.")
    return parser.parse_args()


def extract_section(text: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def check(text: str) -> list[str]:
    issues: list[str] = []
    lower = text.lower()
    for heading in REQUIRED_HEADINGS:
        if not extract_section(text, heading):
            issues.append(f"missing or empty H2 section: {heading}")

    outcome = extract_section(text, "learning outcome")
    for label in ("time budget", "release / api context", "source boundary"):
        if label not in outcome.lower():
            issues.append(f"learning outcome section lacks {label}")

    example = extract_section(text, "worked example").lower()
    for phrase in ("assumption", "expected result", "verify", "does not prove"):
        if phrase not in example:
            issues.append(f"worked example lacks {phrase}")

    checks = extract_section(text, "knowledge check")
    question_count = len(re.findall(r"^\d+\.\s+\S", checks, re.MULTILINE))
    if question_count < 3:
        issues.append("knowledge check has fewer than three numbered questions/answers")
    if "### Answers".lower() not in checks.lower():
        issues.append("knowledge check lacks an Answers subsection")

    if not re.search(r"\b(?:C|S)-\d+\b", text, re.IGNORECASE) and not re.search(
        r"https?://|\[[^\]]+\]\([^\)]+\)", text
    ):
        issues.append("brief has no claim/source identifier or citation")

    practice = extract_section(text, "practice task").lower()
    if "safe environment" not in practice or "stop condition" not in practice:
        issues.append("practice task lacks safe environment or stop condition")

    if "platform guarantee" not in lower or "official recommendation" not in lower:
        issues.append("boundaries do not distinguish guarantee from recommendation")
    return issues


def main() -> int:
    args = parse_args()
    target = Path(args.input or args.manifest_dir)
    if args.input and not target.is_file() or args.manifest_dir and not target.is_dir():
        print(f"ERROR: not found: {target}")
        sys.exit(1)
    files = [target] if args.input else sorted(target.rglob("*.md"))
    if not files:
        print(f"WARN: {target}: no learning-brief .md files found.")
        return 1 if args.strict else 0
    warns = 0
    for path in files:
        issues = check(path.read_text(encoding="utf-8", errors="replace"))
        for issue in issues:
            print(f"WARN: {path}: {issue}")
        warns += len(issues)
        if not issues:
            print(f"PASS: learning brief is structurally complete: {path}")
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
