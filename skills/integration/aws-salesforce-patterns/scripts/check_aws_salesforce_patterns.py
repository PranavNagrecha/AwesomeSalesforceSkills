#!/usr/bin/env python3
"""Static checks for AWS-Salesforce integration code in a project tree.

Scans Apex sources and Named Credential metadata for the high-confidence
anti-patterns documented in this skill's references/llm-anti-patterns.md
and references/gotchas.md. Stdlib only — no pip dependencies.

What this script catches:

  1. Hard-coded AWS endpoint hosts in Apex source (Lambda Function URLs,
     API Gateway, *.amazonaws.com). Should be in a Named Credential.
  2. AWS access key prefixes (AKIA, ASIA) in Apex or static resource
     XML — credentials must never live in source.
  3. PlatformEvent Apex triggers that ALSO contain HTTP callouts —
     classic "DIY Event Relay" anti-pattern; recommend Event Relay
     instead.

It is deliberately a *signal* tool, not a gate. It prints findings and
exits 1 if any are found so a CI step can flag the diff for review;
exit 0 means clean.

Usage:
    python3 check_aws_salesforce_patterns.py --src-root .
    python3 check_aws_salesforce_patterns.py --src-root force-app/main/default
    python3 check_aws_salesforce_patterns.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Patterns that should never appear in Apex source — auth/endpoint config
# belongs in Named Credentials, not in code.
_AWS_HOST_RE = re.compile(
    r"https?://[^\s'\"<>]*(?:"
    r"\.amazonaws\.com|"        # API Gateway, Lambda invoke, etc.
    r"\.lambda-url\.[^\s'\"<>]*\.on\.aws|"  # Lambda Function URLs
    r"\.execute-api\.[^\s'\"<>]+"           # explicit API Gateway pattern
    r")",
    re.IGNORECASE,
)

# AWS short-term and long-term access-key prefixes. Catching either in
# committed source means a credential is in the repo, full stop.
_AWS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{12,}\b")

# Heuristic: PlatformEvent triggers that also issue HTTP callouts. The
# trigger keyword + an Http construction in the same file is the smell.
_TRIGGER_HEADER_RE = re.compile(r"\btrigger\s+\w+\s+on\s+\w+__e\b", re.IGNORECASE)
_HTTP_CALLOUT_RE = re.compile(r"\b(?:HttpRequest|Http\s*\(\s*\))\b")


def _scan_apex_file(path: Path) -> list[str]:
    """Return findings (as human-readable strings) for one .cls / .trigger file."""
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for match in _AWS_HOST_RE.finditer(text):
        line_no = text[: match.start()].count("\n") + 1
        findings.append(
            f"{path}:{line_no}: hard-coded AWS endpoint `{match.group(0)}` "
            "— move to a Named Credential (see references/llm-anti-patterns.md § 2)"
        )

    for match in _AWS_KEY_RE.finditer(text):
        line_no = text[: match.start()].count("\n") + 1
        findings.append(
            f"{path}:{line_no}: AWS access-key prefix `{match.group(0)[:6]}…` in source "
            "— credentials must live in Named Credential or Custom Metadata, never in code"
        )

    if _TRIGGER_HEADER_RE.search(text) and _HTTP_CALLOUT_RE.search(text):
        findings.append(
            f"{path}: Platform Event trigger with inline HTTP callout — "
            "this is the DIY Event Relay anti-pattern. Use Salesforce Event Relay "
            "→ EventBridge instead (see SKILL.md Pattern A and "
            "skills/integration/event-relay-configuration)"
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    """Walk ``root`` for Apex sources and return every finding."""
    findings: list[str] = []
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    apex_files = list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))
    if not apex_files:
        # Not an error — small projects may have no Apex.
        return []

    for apex_file in apex_files:
        findings.extend(_scan_apex_file(apex_file))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex sources for AWS-integration anti-patterns "
            "(hard-coded endpoints, access keys, DIY Event Relay)."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the source tree to scan (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no AWS-Salesforce integration anti-patterns detected.")
        return 0

    for finding in findings:
        print(f"WARN: {finding}", file=sys.stderr)
    print(
        f"\n{len(findings)} finding(s). See references/llm-anti-patterns.md "
        "and references/gotchas.md for the rationale and the correct pattern.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
