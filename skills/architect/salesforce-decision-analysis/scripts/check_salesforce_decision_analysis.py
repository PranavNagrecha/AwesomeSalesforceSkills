#!/usr/bin/env python3
"""Validate a Salesforce decision-analysis packet without external packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_MARKDOWN_HEADINGS = (
    "decision frame",
    "constraints and non-goals",
    "evidence ledger",
    "options",
    "hard-gate assessment",
    "criteria and weights",
    "weighted comparison",
    "sensitivity analysis",
    "risk, reversibility, and exit",
    "recommendation",
)
VALID_GATE_STATES = {"PASS", "FAIL", "UNKNOWN"}
VALID_EVIDENCE_STATES = {"fact", "recommendation", "assumption", "unknown"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a Salesforce decision-analysis packet.")
    parser.add_argument("--input", required=True, help="Markdown or JSON decision packet")
    return parser.parse_args()


def _extract_percentages(criteria_section: str) -> list[float]:
    values: list[float] = []
    for line in criteria_section.splitlines():
        if not line.lstrip().startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        for cell in cells:
            match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", cell)
            if match:
                values.append(float(match.group(1)))
                break
    return values


def check_markdown(text: str) -> list[str]:
    issues: list[str] = []
    lower = text.lower()
    for heading in REQUIRED_MARKDOWN_HEADINGS:
        if not re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.IGNORECASE | re.MULTILINE):
            issues.append(f"missing H2 section: {heading}")

    options = re.findall(r"^###\s+Option\s+[A-Za-z0-9]+\b", text, re.MULTILINE)
    if len(options) < 2:
        issues.append("fewer than two viable option sections")

    section_match = re.search(
        r"^##\s+Criteria and Weights\s*$([\s\S]*?)(?=^##\s+|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if section_match:
        weights = _extract_percentages(section_match.group(1))
        if not weights:
            issues.append("criteria section has no percentage weights")
        elif abs(sum(weights) - 100.0) > 0.1:
            issues.append(f"criteria weights sum to {sum(weights):g}, expected 100")

    if not any(state in text for state in VALID_GATE_STATES):
        issues.append("hard-gate section has no PASS/FAIL/UNKNOWN state")
    if not any(state in lower for state in VALID_EVIDENCE_STATES):
        issues.append("evidence ledger has no fact/recommendation/assumption/unknown state")
    if "ranking changed" not in lower:
        issues.append("sensitivity analysis does not state whether ranking changed")
    if "conditions that would change" not in lower and "recommendation would change" not in lower:
        issues.append("recommendation has no reversal condition")
    if "confidence" not in lower:
        issues.append("recommendation has no confidence statement")
    if "rollback" not in lower and "exit" not in lower:
        issues.append("packet has no rollback or exit path")
    return issues


def _require(obj: dict[str, Any], key: str, issues: list[str]) -> Any:
    if key not in obj:
        issues.append(f"missing JSON key: {key}")
        return None
    return obj[key]


def check_json(obj: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(obj, dict):
        return ["JSON root must be an object"]
    for key in (
        "decision_frame", "constraints", "evidence", "options", "hard_gates",
        "criteria", "comparison", "sensitivity", "risks", "recommendation",
    ):
        _require(obj, key, issues)

    options = obj.get("options")
    if not isinstance(options, list) or len(options) < 2:
        issues.append("options must contain at least two entries")

    criteria = obj.get("criteria")
    if isinstance(criteria, list):
        weights = [item.get("weight") for item in criteria if isinstance(item, dict)]
        if not weights or any(not isinstance(value, (int, float)) for value in weights):
            issues.append("every criterion needs a numeric weight")
        elif abs(sum(weights) - 100.0) > 0.1:
            issues.append(f"criteria weights sum to {sum(weights):g}, expected 100")
    else:
        issues.append("criteria must be an array")

    evidence = obj.get("evidence")
    if isinstance(evidence, list):
        for index, item in enumerate(evidence):
            if not isinstance(item, dict) or item.get("state") not in VALID_EVIDENCE_STATES:
                issues.append(f"evidence[{index}] has invalid state")
    else:
        issues.append("evidence must be an array")

    gates = obj.get("hard_gates")
    if isinstance(gates, list):
        for index, item in enumerate(gates):
            if not isinstance(item, dict) or item.get("state") not in VALID_GATE_STATES:
                issues.append(f"hard_gates[{index}] has invalid state")
    else:
        issues.append("hard_gates must be an array")

    recommendation = obj.get("recommendation")
    if isinstance(recommendation, dict):
        for key in ("status", "confidence", "conditions_that_change", "validation_actions"):
            if not recommendation.get(key):
                issues.append(f"recommendation missing {key}")
    return issues


def main() -> int:
    args = parse_args()
    path = Path(args.input)
    if not path.is_file():
        print(f"ERROR: not found: {path}")
        return 2
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read {path}: {exc}")
        return 2

    if path.suffix.lower() == ".json":
        try:
            issues = check_json(json.loads(text))
        except json.JSONDecodeError as exc:
            issues = [f"invalid JSON: {exc}"]
    else:
        issues = check_markdown(text)

    if issues:
        for issue in issues:
            print(f"ISSUE: {issue}")
        return 1
    print(f"PASS: decision packet is structurally complete: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
