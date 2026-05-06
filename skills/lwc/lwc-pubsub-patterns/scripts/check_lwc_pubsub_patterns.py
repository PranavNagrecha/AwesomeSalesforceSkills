#!/usr/bin/env python3
"""Static checks for LWC pub/sub anti-patterns.

Anti-patterns detected:

  1. `subscribe(` call in an LWC `.js` file without a corresponding
     `unsubscribe(` in the same file — leaked subscription.
  2. Import of legacy `c/pubsub` utility — recommend LMS for new
     code.
  3. `subscribe(` inside `renderedCallback` without a subscription-
     existence guard — produces duplicate subscriptions on re-render.
  4. `publish(` calls whose payload includes a function expression
     — LMS messages must be JSON-serializable.

Stdlib only.

Usage:
    python3 check_lwc_pubsub_patterns.py --src-root .
    python3 check_lwc_pubsub_patterns.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SUBSCRIBE_RE = re.compile(r"\bsubscribe\s*\(", re.IGNORECASE)
_UNSUBSCRIBE_RE = re.compile(r"\bunsubscribe\s*\(", re.IGNORECASE)

_PUBSUB_IMPORT_RE = re.compile(
    r"from\s+['\"]c/pubsub['\"]",
    re.IGNORECASE,
)

_RENDERED_CALLBACK_RE = re.compile(
    r"renderedCallback\s*\(\s*\)\s*\{([\s\S]*?)\n\s*\}",
)
_GUARD_RE = re.compile(r"this\.subscription", re.IGNORECASE)

_PUBLISH_FUNC_RE = re.compile(
    r"publish\s*\([^)]*\{[^}]*=>",
    re.IGNORECASE | re.DOTALL,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    has_sub = bool(_SUBSCRIBE_RE.search(text))
    has_unsub = bool(_UNSUBSCRIBE_RE.search(text))
    if has_sub and not has_unsub:
        # Find first subscribe location for the report
        m = _SUBSCRIBE_RE.search(text)
        findings.append(
            f"{path}:{_line_no(text, m.start())}: `subscribe(` with no "
            "`unsubscribe(` in the same file — likely leaked subscription. "
            "Pair every subscribe with an unsubscribe in disconnectedCallback "
            "(llm-anti-patterns.md § 1, gotchas.md § 1)."
        )

    for m in _PUBSUB_IMPORT_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: imports legacy `c/pubsub` "
            "utility. New code should use Lightning Message Service "
            "(`lightning/messageService`) (llm-anti-patterns.md § 3)."
        )

    for m in _RENDERED_CALLBACK_RE.finditer(text):
        body = m.group(1)
        if _SUBSCRIBE_RE.search(body) and not _GUARD_RE.search(body):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: subscribe(...) inside "
                "renderedCallback without a `this.subscription` existence "
                "guard — produces duplicate subscriptions on re-render "
                "(llm-anti-patterns.md § 7, gotchas.md § 8)."
            )

    for m in _PUBLISH_FUNC_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: publish(...) payload "
            "appears to contain a function expression (=>) — LMS messages "
            "must be JSON-serializable; functions are stripped "
            "(llm-anti-patterns.md § 6, gotchas.md § 9)."
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for js in root.rglob("*.js"):
        findings.extend(_scan(js))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC JavaScript for pub/sub anti-patterns: subscribe "
            "without unsubscribe, legacy `c/pubsub` imports, subscribe in "
            "renderedCallback without guard, and publish payloads with "
            "function expressions."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the LWC source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no LWC pub/sub anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
