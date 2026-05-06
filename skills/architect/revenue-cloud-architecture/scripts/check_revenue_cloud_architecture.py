#!/usr/bin/env python3
"""Static checks for Revenue Cloud / RLM architecture anti-patterns.

Anti-patterns detected:

  1. `Http.send` / `HttpRequest` references inside an Apex trigger —
     synchronous callouts from triggers are blocked.
  2. DML `delete` against `Asset`, `Contract`, or `Order` — breaks
     RLM state-period model.
  3. Mixed namespace usage in one file: both `blng__` and unqualified
     RLM Billing objects (`Invoice`, `BillingSchedule`,
     `LegalEntity`) — likely indicates confusion.
  4. QuoteLineItem / OrderItem insert literals without
     `PricebookEntryId`.

Stdlib only.

Usage:
    python3 check_revenue_cloud_architecture.py --src-root .
    python3 check_revenue_cloud_architecture.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_TRIGGER_HEADER_RE = re.compile(r"\btrigger\s+\w+\s+on\s+\w+", re.IGNORECASE)
_HTTP_SEND_RE = re.compile(r"\bHttp(?:Request)?\b|\bHttp\.send\b")

_DELETE_RLM_RE = re.compile(
    r"\bdelete\s+\[[^\]]*\bFROM\s+(Asset|Contract|Order)\b",
    re.IGNORECASE | re.DOTALL,
)

_BLNG_RE = re.compile(r"\bblng__\w+__c\b")
_RLM_NATIVE_RE = re.compile(
    r"\b(Invoice|BillingSchedule|LegalEntity|AccountingPeriod)\b\s+\w+\s*[=;,)]",
)

_QUOTELINE_INSERT_RE = re.compile(
    r"new\s+(QuoteLineItem|OrderItem)\s*\(([^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)
_HAS_PBE_RE = re.compile(r"\bPricebookEntryId\s*=", re.IGNORECASE)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    is_trigger = path.suffix.lower() == ".trigger" or bool(
        _TRIGGER_HEADER_RE.search(text[:200])
    )

    # 1. Http callout in trigger
    if is_trigger:
        for m in _HTTP_SEND_RE.finditer(text):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: Http callout reference "
                "inside a trigger — synchronous trigger callouts are blocked. "
                "Use @future(callout=true), Queueable, or emit a Platform "
                "Event / use CDC (llm-anti-patterns.md § 1, gotchas.md § 1)."
            )

    # 2. Delete against RLM entities
    for m in _DELETE_RLM_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: DML `delete` against "
            f"`{m.group(1)}` — breaks the RLM state-period model. Cancellation "
            "is a state transition, not a delete (llm-anti-patterns.md § 4, "
            "gotchas.md § 7)."
        )

    # 3. Mixed namespace
    has_blng = bool(_BLNG_RE.search(text))
    has_native = bool(_RLM_NATIVE_RE.search(text))
    if has_blng and has_native:
        findings.append(
            f"{path}: file mixes `blng__` (Salesforce Billing managed "
            "package) with native RLM Billing object names. These are "
            "different products; pick one namespace deliberately "
            "(llm-anti-patterns.md § 2, gotchas.md § 3)."
        )

    # 4. QuoteLineItem / OrderItem without PricebookEntryId
    for m in _QUOTELINE_INSERT_RE.finditer(text):
        body = m.group(2)
        if not _HAS_PBE_RE.search(body):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: `new {m.group(1)}(...)` "
                "without PricebookEntryId — RLM Pricing still requires the "
                "PricebookEntry linkage (llm-anti-patterns.md § 5)."
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
            "Scan Apex source for Revenue Cloud / RLM architecture anti-"
            "patterns: synchronous trigger callouts, DML delete on Asset / "
            "Contract / Order, mixed `blng__` and native RLM namespaces, "
            "QuoteLineItem / OrderItem inserts without PricebookEntryId."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Revenue Cloud architecture anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
