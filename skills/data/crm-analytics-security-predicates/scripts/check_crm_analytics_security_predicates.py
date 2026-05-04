#!/usr/bin/env python3
"""Static checks for CRM Analytics security-predicate definitions.

Scans CRM Analytics dataset XMD JSON files for the high-confidence
anti-patterns documented in this skill:

  1. `securityPredicate` value referencing a literal Salesforce User Id
     (15 or 18 chars, starts with `005`) — hardcoded service-account
     bypass that breaks on user recreation.
  2. `securityPredicate` value containing `.descendants` / `.ancestors`
     / `.hierarchy` against `$User.UserRoleId` — fictional SAQL
     traversal.
  3. `securityPredicate` value using `matches "$User.UserName"` or
     `matches "$User.Email"` — regex against unbounded user-supplied
     input is injection-risky and unstable.
  4. Dataset XMD with NO `securityPredicate` — flagged as a soft note
     for review (may be intentional).

Stdlib only. Walks `*.xmd.json`, `*.wave-*.json`, and any JSON file in
a CRM-Analytics-shaped path.

Usage:
    python3 check_crm_analytics_security_predicates.py --src-root .
    python3 check_crm_analytics_security_predicates.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 18-char or 15-char Salesforce User Id (User keyPrefix is 005).
_USER_ID_RE = re.compile(r"\b005[a-zA-Z0-9]{12}([a-zA-Z0-9]{3})?\b")

# Fictional role-hierarchy traversals.
_FAKE_TRAVERSAL_RE = re.compile(
    r"\$User\.UserRoleId\.(?:descendants|ancestors|hierarchy)",
    re.IGNORECASE,
)

# matches regex against unbounded user-supplied input.
_MATCHES_USERNAME_RE = re.compile(
    r"\bmatches\s+\"\$User\.(?:UserName|Email)\"",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_predicate_text(path: Path, text: str, predicate: str, key_pos: int) -> list[str]:
    findings: list[str] = []

    # Smell 1: hardcoded User Id
    for m in _USER_ID_RE.finditer(predicate):
        findings.append(
            f"{path}:{_line_no(text, key_pos)}: securityPredicate references hardcoded "
            f"User Id `{m.group(0)}` — brittle on service-account recreation. "
            "Use the `Manage Analytics` permission for bypass instead "
            "(references/llm-anti-patterns.md § 5)"
        )

    # Smell 2: fictional role-hierarchy traversal
    if _FAKE_TRAVERSAL_RE.search(predicate):
        findings.append(
            f"{path}:{_line_no(text, key_pos)}: securityPredicate uses a fictional "
            "`$User.UserRoleId.descendants/ancestors/hierarchy` — SAQL has no "
            "role-hierarchy traversal. Compute the chain in the dataflow / recipe "
            "and use `matches \"$User.UserRoleId\"` against the precomputed column "
            "(references/llm-anti-patterns.md § 4)"
        )

    # Smell 3: matches against unbounded user-supplied input
    if _MATCHES_USERNAME_RE.search(predicate):
        findings.append(
            f"{path}:{_line_no(text, key_pos)}: securityPredicate uses `matches` "
            "against `$User.UserName` or `$User.Email` — regex against unbounded "
            "user-supplied input is injection-risky. Prefer `$User.Id` or "
            "normalize at dataflow time "
            "(references/llm-anti-patterns.md § 8)"
        )

    return findings


def _scan_xmd(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # Scan the raw text for `"securityPredicate": "..."` occurrences. JSON
    # parsing is also tried below for accuracy, but raw-text scan covers
    # files that might not strictly parse.
    for m in re.finditer(
        r'"securityPredicate"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
        text,
    ):
        predicate = m.group(1).encode("utf-8").decode("unicode_escape")
        findings.extend(_scan_predicate_text(path, text, predicate, m.start()))

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []
    # CRM Analytics dataset XMD files use various naming conventions; cover the
    # common ones.
    patterns = ["**/*.xmd.json", "**/*.wave-meta.xml", "**/*-meta.xml"]
    for pattern in patterns:
        for f in root.glob(pattern):
            if f.suffix.lower() == ".xml":
                # XML files: scan as text for the predicate element.
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for m in re.finditer(
                    r"<securityPredicate>([^<]*)</securityPredicate>",
                    text,
                    re.IGNORECASE | re.DOTALL,
                ):
                    findings.extend(_scan_predicate_text(f, text, m.group(1), m.start()))
            else:
                findings.extend(_scan_xmd(f))

    # Also scan any *.json file under a CRM-Analytics-shaped directory.
    for f in root.rglob("*.json"):
        s = str(f).lower()
        if "wave" in s or "analytics" in s or "dataset" in s:
            findings.extend(_scan_xmd(f))

    # Deduplicate (same finding may surface from multiple globs).
    return sorted(set(findings))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan CRM Analytics dataset XMD / metadata for security-predicate "
            "anti-patterns (hardcoded User Ids, fictional role-hierarchy "
            "traversals, matches against unbounded user input)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the metadata tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no CRM Analytics predicate anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
