#!/usr/bin/env python3
"""Static checks for Apex outbound-email anti-patterns.

Scans Apex source for the high-confidence anti-patterns documented in
`references/llm-anti-patterns.md`:

  1. setHtmlBody / setPlainTextBody whose literal argument contains
     `{!` (template merge syntax that sends literally).
  2. Messaging.sendEmail call inside a `for (... : Trigger.new)` loop.
  3. setTemplateId combined with setTargetObjectId for what looks like
     a non-Contact/Lead/User.
  4. Discarded Messaging.sendEmail return value (no var assignment, no
     try/catch wrapper).

Stdlib only.

Usage:
    python3 check_apex_outbound_email_patterns.py --src-root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_LITERAL_MERGE_RE = re.compile(
    r"\.set(?:Html|PlainText)Body\s*\(\s*'([^']*\{![^']*)'\s*\)",
    re.IGNORECASE,
)
_TRIGGER_LOOP_RE = re.compile(
    r"for\s*\(\s*\w+\s+\w+\s*:\s*Trigger\.(new|old)\s*\)\s*\{",
    re.IGNORECASE,
)
_SEND_EMAIL_RE = re.compile(r"\bMessaging\.sendEmail\s*\(")
_TEMPLATE_ID_RE = re.compile(r"\.setTemplateId\s*\(")
_TARGET_OBJECT_RE = re.compile(r"\.setTargetObjectId\s*\(\s*(\w+(?:\.\w+)*)\s*\)")
_NON_CLU_HINTS = (
    "account", "opp", "case", "order", "asset", "product",
    "campaign", "task", "event", "__c",
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _block_end(text: str, brace_pos: int) -> int:
    depth = 1
    i = brace_pos + 1
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return i


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _LITERAL_MERGE_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: setHtmlBody/"
            "setPlainTextBody literal contains '{!' — merge syntax is "
            "only honored by renderStoredEmailTemplate, not setBody "
            "(references/llm-anti-patterns.md § 2)"
        )

    for tm in _TRIGGER_LOOP_RE.finditer(text):
        body_start = text.find("{", tm.end() - 1)
        if body_start == -1:
            continue
        body_end = _block_end(text, body_start)
        body = text[body_start:body_end]
        for sm in _SEND_EMAIL_RE.finditer(body):
            findings.append(
                f"{path}:{_line_no(text, body_start + sm.start())}: "
                "Messaging.sendEmail inside a `for (… : Trigger.new)` "
                "loop — un-bulkified and pre-commit "
                "(references/llm-anti-patterns.md § 4)"
            )

    if _TEMPLATE_ID_RE.search(text):
        for m in _TARGET_OBJECT_RE.finditer(text):
            arg = m.group(1).lower()
            if any(h in arg for h in _NON_CLU_HINTS):
                findings.append(
                    f"{path}:{_line_no(text, m.start())}: "
                    f"setTargetObjectId({m.group(1)}) likely non-Contact/"
                    "Lead/User. Use renderStoredEmailTemplate(tpl, null, "
                    "whatId) instead "
                    "(references/llm-anti-patterns.md § 3)"
                )

    for m in _SEND_EMAIL_RE.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_prefix = text[line_start:m.start()].strip()
        head = text[max(0, m.start() - 250): m.start()]
        if "=" not in line_prefix and "try" not in head:
            findings.append(
                f"{path}:{_line_no(text, m.start())}: Messaging.sendEmail "
                "return value discarded and not in a try block — "
                "per-recipient failures are silently ignored "
                "(references/llm-anti-patterns.md § 5)"
            )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for apex in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        findings.extend(_scan_apex(apex))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex sources for outbound-email anti-patterns "
            "(literal merge in setBody, sendEmail in trigger loop, "
            "wrong setTargetObjectId, discarded return value)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Apex outbound-email anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
