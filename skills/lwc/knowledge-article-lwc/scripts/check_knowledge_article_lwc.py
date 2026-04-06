#!/usr/bin/env python3
"""Checker script for Knowledge Article LWC skill.

Scans Salesforce project metadata and LWC source files for common issues
related to Knowledge article retrieval in Lightning Web Components.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_knowledge_article_lwc.py [--help]
    python3 check_knowledge_article_lwc.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC and Apex files for common Knowledge article anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_missing_publish_status_filter(apex_files: list[Path]) -> list[str]:
    """Warn when a SOQL query against Knowledge__kav lacks PublishStatus filter."""
    issues: list[str] = []
    pattern_kav_query = re.compile(
        r"FROM\s+Knowledge__kav\b", re.IGNORECASE
    )
    pattern_publish_status = re.compile(
        r"PublishStatus\s*=", re.IGNORECASE
    )
    for path in apex_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Find each SELECT block containing Knowledge__kav
        # Simple line-window heuristic: check within 10 lines of the FROM clause
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if pattern_kav_query.search(line):
                # Look in a window of 10 lines before and after for PublishStatus
                window_start = max(0, i - 10)
                window_end = min(len(lines), i + 10)
                window = "\n".join(lines[window_start:window_end])
                if not pattern_publish_status.search(window):
                    issues.append(
                        f"{path}: line {i + 1} — SOQL query against Knowledge__kav "
                        "appears to be missing 'PublishStatus = \\'Online\\'' filter. "
                        "Omitting this returns draft and archived versions."
                    )
    return issues


def check_dml_on_vote_stat(apex_files: list[Path]) -> list[str]:
    """Warn when DML is attempted on KnowledgeArticleVoteStat."""
    issues: list[str] = []
    pattern = re.compile(
        r"\b(insert|upsert|update|delete)\b[^;]*KnowledgeArticleVoteStat",
        re.IGNORECASE | re.DOTALL,
    )
    for path in apex_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in pattern.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            issues.append(
                f"{path}: line {line_no} — DML on KnowledgeArticleVoteStat is not "
                "supported. Use KbManagement.PublishingService.rateKnowledgeArticle() instead."
            )
    return issues


def check_inner_html_assignment(lwc_js_files: list[Path]) -> list[str]:
    """Warn when innerHTML is assigned in a component that references Knowledge."""
    issues: list[str] = []
    pattern_inner_html = re.compile(r"\.innerHTML\s*=", re.IGNORECASE)
    pattern_knowledge = re.compile(r"knowledge", re.IGNORECASE)
    for path in lwc_js_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if pattern_inner_html.search(text) and pattern_knowledge.search(text):
            for i, line in enumerate(text.splitlines(), start=1):
                if pattern_inner_html.search(line):
                    issues.append(
                        f"{path}: line {i} — '.innerHTML =' assignment detected in a "
                        "component that references Knowledge. Use "
                        "<lightning-formatted-rich-text> instead to prevent XSS."
                    )
    return issues


def check_hallucinated_knowledge_wire_adapter(lwc_js_files: list[Path]) -> list[str]:
    """Warn when a nonexistent lightning/knowledgeApi import is used."""
    issues: list[str] = []
    pattern = re.compile(
        r"from\s+['\"]lightning/knowledge(?:Api|Management)['\"]",
        re.IGNORECASE,
    )
    for path in lwc_js_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                issues.append(
                    f"{path}: line {i} — Import from 'lightning/knowledgeApi' or "
                    "'lightning/knowledgeManagement' is not a valid LWC platform "
                    "module. Use a custom @AuraEnabled Apex method for Knowledge retrieval."
                )
    return issues


def check_cacheable_voting_method(apex_files: list[Path]) -> list[str]:
    """Warn when rateKnowledgeArticle is called from a cacheable=true Apex method."""
    issues: list[str] = []
    cacheable_block_pattern = re.compile(
        r"@AuraEnabled\s*\(\s*cacheable\s*=\s*true\s*\)(.*?)(?=@AuraEnabled|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    rate_call_pattern = re.compile(r"rateKnowledgeArticle", re.IGNORECASE)
    for path in apex_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in cacheable_block_pattern.finditer(text):
            block = match.group(1)
            if rate_call_pattern.search(block):
                line_no = text[: match.start()].count("\n") + 1
                issues.append(
                    f"{path}: near line {line_no} — "
                    "rateKnowledgeArticle() called inside a cacheable=true @AuraEnabled "
                    "method. Voting is a DML-equivalent operation and must use a "
                    "non-cacheable @AuraEnabled method."
                )
    return issues


# ---------------------------------------------------------------------------
# File discovery helpers
# ---------------------------------------------------------------------------

def find_apex_files(root: Path) -> list[Path]:
    """Return all .cls files under the root directory."""
    return list(root.rglob("*.cls"))


def find_lwc_js_files(root: Path) -> list[Path]:
    """Return all LWC JavaScript files (.js) that are not test files."""
    return [
        p for p in root.rglob("*.js")
        if "__tests__" not in p.parts and ".test." not in p.name
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_knowledge_article_lwc(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_apex_files(manifest_dir)
    lwc_js_files = find_lwc_js_files(manifest_dir)

    issues.extend(check_missing_publish_status_filter(apex_files))
    issues.extend(check_dml_on_vote_stat(apex_files))
    issues.extend(check_cacheable_voting_method(apex_files))
    issues.extend(check_inner_html_assignment(lwc_js_files))
    issues.extend(check_hallucinated_knowledge_wire_adapter(lwc_js_files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_knowledge_article_lwc(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
