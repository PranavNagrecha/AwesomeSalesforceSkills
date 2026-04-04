#!/usr/bin/env python3
"""Checker script for Agent Testing and Evaluation skill.

Scans a Salesforce metadata directory for AiEvaluationDefinition files and
checks them for common testing anti-patterns described in the skill's gotchas
and llm-anti-patterns references.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agent_testing_and_evaluation.py [--help]
    python3 check_agent_testing_and_evaluation.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


_EVAL_SUFFIX = ".aiEvaluationDefinition-meta.xml"
_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check AiEvaluationDefinition metadata files for common Agentforce "
            "testing anti-patterns: too few test cases, missing topic expectations, "
            "no multi-turn tests, and missing out-of-scope coverage."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--min-cases-per-file",
        type=int,
        default=4,
        help="Minimum number of test cases expected per AiEvaluationDefinition file (default: 4).",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    """Return a namespace-qualified tag name."""
    return f"{{{_NAMESPACE}}}{local}"


def _find_eval_files(manifest_dir: Path) -> list[Path]:
    """Recursively find all AiEvaluationDefinition metadata files."""
    return list(manifest_dir.rglob(f"*{_EVAL_SUFFIX}"))


def _check_file(path: Path, min_cases: int) -> list[str]:
    """Return issues found in a single AiEvaluationDefinition file."""
    issues: list[str] = []

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        issues.append(f"{path.name}: XML parse error — {exc}")
        return issues

    root = tree.getroot()

    # Collect all testCase elements (handles both namespaced and plain XML)
    test_cases = root.findall(_tag("testCases"))
    if not test_cases:
        # Try without namespace
        test_cases = root.findall("testCases")

    case_count = len(test_cases)

    # 1. Minimum test case count
    if case_count == 0:
        issues.append(
            f"{path.name}: No test cases found. "
            "AiEvaluationDefinition must contain at least one testCase."
        )
        return issues  # No point checking further

    if case_count < min_cases:
        issues.append(
            f"{path.name}: Only {case_count} test case(s) found (minimum: {min_cases}). "
            "Add edge-case, boundary, and out-of-scope utterances for adequate coverage."
        )

    # 2. Check that at least one test case has an expectTopicName assertion
    has_topic_expectation = False
    has_conversation_history = False
    topic_names_seen: set[str] = set()

    for case in test_cases:
        # Check expectations
        for expectation in case.findall(_tag("expectations")) or case.findall("expectations"):
            topic_el = expectation.find(_tag("expectTopicName")) or expectation.find("expectTopicName")
            if topic_el is not None and topic_el.text:
                has_topic_expectation = True
                topic_names_seen.add(topic_el.text.strip())

        # Check for conversation history (multi-turn)
        inputs_el = case.find(_tag("inputs")) or case.find("inputs")
        if inputs_el is not None:
            history = inputs_el.find(_tag("conversationHistory")) or inputs_el.find("conversationHistory")
            if history is not None:
                has_conversation_history = True

    if not has_topic_expectation:
        issues.append(
            f"{path.name}: No test case has an <expectTopicName> assertion. "
            "Add topic expectations to validate agent routing."
        )

    # 3. Warn if all test cases assert the same single topic (likely happy-path-only)
    if len(topic_names_seen) == 1 and case_count >= min_cases:
        issues.append(
            f"{path.name}: All {case_count} test cases assert the same topic "
            f"'{next(iter(topic_names_seen))}'. "
            "Consider adding cases for adjacent topics and out-of-scope utterances."
        )

    # 4. Informational: note if no multi-turn tests are present (not a hard error)
    if not has_conversation_history and case_count >= min_cases:
        issues.append(
            f"{path.name}: INFO — No multi-turn conversation history found in any test case. "
            "If the agent handles context-dependent flows, add conversationHistory inputs."
        )

    return issues


def check_agent_testing_and_evaluation(manifest_dir: Path, min_cases: int) -> list[str]:
    """Return a list of issue strings found across all AiEvaluationDefinition files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    eval_files = _find_eval_files(manifest_dir)

    if not eval_files:
        issues.append(
            "No AiEvaluationDefinition files found "
            f"(searched recursively under '{manifest_dir}'). "
            "Create at least one .aiEvaluationDefinition-meta.xml file to enable automated agent testing."
        )
        return issues

    for path in sorted(eval_files):
        file_issues = _check_file(path, min_cases)
        issues.extend(file_issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_agent_testing_and_evaluation(manifest_dir, args.min_cases_per_file)

    hard_issues = [i for i in issues if not i.split(":", 1)[-1].strip().startswith("INFO")]
    info_issues = [i for i in issues if i.split(":", 1)[-1].strip().startswith("INFO")]

    if not issues:
        print("No issues found.")
        return 0

    for issue in hard_issues:
        print(f"ISSUE: {issue}")

    for issue in info_issues:
        print(f"INFO:  {issue}")

    return 1 if hard_issues else 0


if __name__ == "__main__":
    sys.exit(main())
