#!/usr/bin/env python3
"""Static checks for Messaging.InboundEmailHandler implementations.

Catches:
  1. Class implementing `Messaging.InboundEmailHandler` declared
     `public` instead of `global`.
  2. `handleInboundEmail` method declared non-`global`.
  3. Stack trace exposed in `result.message` (information disclosure).
  4. Synchronous `Http().send(...)` called from an inbound-email
     handler (blocks email processing).
  5. Map-style `email.headers.get(...)` (wrong shape).

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_IMPL_RE = re.compile(
    r"\b(public|global|private|protected)\s+(?:virtual\s+|abstract\s+|with\s+sharing\s+|without\s+sharing\s+)*class\s+(\w+)\s+implements\s+(?:[^\{]*?)Messaging\.InboundEmailHandler",
    re.IGNORECASE,
)
_METHOD_RE = re.compile(
    r"\b(public|global|private|protected)\s+Messaging\.InboundEmailResult\s+handleInboundEmail\s*\(",
    re.IGNORECASE,
)
_STACK_TRACE_LEAK_RE = re.compile(
    r"\.message\s*=\s*[^;]*getStackTraceString\s*\(",
    re.IGNORECASE,
)
_SYNC_HTTP_RE = re.compile(r"\bnew\s+Http\s*\(\s*\)\s*\.send\s*\(", re.IGNORECASE)
_HEADERS_GET_RE = re.compile(r"\bemail\.headers\.get\s*\(", re.IGNORECASE)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    impl = _IMPL_RE.search(text)
    is_handler = impl is not None
    if is_handler:
        modifier = impl.group(1).lower()
        cls = impl.group(2)
        if modifier != "global":
            findings.append(
                f"{path}:{_line_no(text, impl.start())}: class `{cls}` implements "
                f"Messaging.InboundEmailHandler with `{modifier}` access — must be "
                "`global` (references/llm-anti-patterns.md § 1)"
            )

        method = _METHOD_RE.search(text)
        if method is not None:
            mmod = method.group(1).lower()
            if mmod != "global":
                findings.append(
                    f"{path}:{_line_no(text, method.start())}: "
                    f"`handleInboundEmail` declared `{mmod}` — must be `global` "
                    "(references/llm-anti-patterns.md § 1)"
                )

    for m in _STACK_TRACE_LEAK_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: assigning getStackTraceString() to "
            "an InboundEmailResult.message field exposes the stack trace to the "
            "(potentially anonymous) sender — information disclosure "
            "(references/llm-anti-patterns.md § 3)"
        )

    if is_handler:
        for m in _SYNC_HTTP_RE.finditer(text):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: synchronous `Http().send(...)` "
                "in an inbound email handler — backs up the inbound queue under "
                "load. Publish a Platform Event for async fan-out instead "
                "(references/llm-anti-patterns.md § 5)"
            )

    for m in _HEADERS_GET_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: `email.headers.get(...)` — "
            "headers is a List, not a Map; iterate instead "
            "(references/llm-anti-patterns.md § 2)"
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
            "Scan Apex source for InboundEmailHandler anti-patterns "
            "(non-global class/method, stack trace leak, sync callout, "
            "Map-style headers access)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no InboundEmailHandler anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
