#!/usr/bin/env python3
"""Heuristically validate a Salesforce learning-research packet."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = (
    "research question",
    "context identity",
    "terminology",
    "source inventory",
    "claim ledger",
    "contradictions",
    "freshness and lifecycle",
    "gaps and unsupported claims",
    "safe examples",
    "learning brief handoff",
)
CLAIM_STATES = (
    "verified-fact", "official-recommendation", "inference",
    "assumption", "unknown", "unsupported",
)
FRESHNESS_STATES = ("current", "preview", "beta", "retired", "historical", "unknown")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a Salesforce learning-research packet.")
    parser.add_argument("--input", required=True)
    return parser.parse_args()


def table_rows(section: str) -> list[str]:
    return [
        line for line in section.splitlines()
        if line.lstrip().startswith("|") and "---" not in line
    ]


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1) if match else ""


def check(text: str) -> list[str]:
    issues: list[str] = []
    lower = text.lower()
    for heading in REQUIRED_HEADINGS:
        if not section(text, heading):
            issues.append(f"missing or empty H2 section: {heading}")

    sources = table_rows(section(text, "source inventory"))
    if len(sources) < 2:  # header plus at least one source
        issues.append("source inventory has no source row")
    elif not re.search(r"\bS-\d+\b", "\n".join(sources), re.IGNORECASE):
        issues.append("source inventory has no stable S-n identifier")

    claims = table_rows(section(text, "claim ledger"))
    if len(claims) < 2:
        issues.append("claim ledger has no claim row")
    else:
        joined = "\n".join(claims).lower()
        if not re.search(r"\bC-\d+\b", joined, re.IGNORECASE):
            issues.append("claim ledger has no stable C-n identifier")
        if not any(state in joined for state in CLAIM_STATES):
            issues.append("claim ledger has no recognized claim state")
        if not any(state in joined for state in FRESHNESS_STATES):
            issues.append("claim ledger has no freshness state")
        if "high" not in joined and "medium" not in joined and "low" not in joined:
            issues.append("claim ledger has no confidence level")

    if "retrieved" not in lower or not re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text):
        issues.append("packet lacks retrieval/observation date evidence")
    if "source boundary" not in lower:
        issues.append("research question does not declare a source boundary")
    if "do not teach as fact" not in lower:
        issues.append("brief handoff lacks a do-not-teach-as-fact list")
    return issues


def main() -> int:
    args = parse_args()
    path = Path(args.input)
    if not path.is_file():
        print(f"ERROR: not found: {path}")
        return 2
    issues = check(path.read_text(encoding="utf-8", errors="replace"))
    if issues:
        for issue in issues:
            print(f"ISSUE: {issue}")
        return 1
    print(f"PASS: learning research packet is structurally complete: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
