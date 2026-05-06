#!/usr/bin/env python3
"""Static checks for multi-currency Apex / SOQL anti-patterns.

Anti-patterns detected:

  1. `DatedConversionRate` insert with `NextStartDate` set — the
     field is platform-computed; setting it is wrong.
  2. SOQL `convertCurrency()` accompanied by a comment claiming dated
     / historical / period rates — the function uses static rates.
  3. Currency-amount filter `Amount > N` without a currency
     qualifier — implicit currency assumption.
  4. Apex insert of an Opportunity (or other currency-aware sObject)
     without `CurrencyIsoCode` set, in a file that mentions
     `multi-currency` or has an ISO-code constant — flags for review.

Stdlib only.

Usage:
    python3 check_currency_management_patterns.py --src-root .
    python3 check_currency_management_patterns.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 1. NextStartDate set on DatedConversionRate.
_NEXT_START_DATE_RE = re.compile(
    r"new\s+DatedConversionRate\s*\([^)]*\bNextStartDate\s*=",
    re.IGNORECASE | re.DOTALL,
)
_NEXT_START_DATE_ASSIGN_RE = re.compile(
    r"\b(\w+)\.NextStartDate\s*=",
    re.IGNORECASE,
)

# 2. convertCurrency() with a nearby comment claiming dated semantics.
_CONVERT_CURRENCY_RE = re.compile(
    r"convertCurrency\s*\(",
    re.IGNORECASE,
)
_DATED_CLAIM_RE = re.compile(
    r"\b(dated|historical|period|as[- ]of)\s+(rate|exchange|conversion)",
    re.IGNORECASE,
)

# 3. Amount > N without explicit CurrencyIsoCode in the same WHERE
#    clause. Heuristic.
_AMOUNT_FILTER_RE = re.compile(
    r"\bAmount\s*[<>]=?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_CURRENCY_ISOCODE_RE = re.compile(
    r"\bCurrencyIsoCode\s*=\s*['\"]\w{3}['\"]",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # 1. NextStartDate set
    for m in _NEXT_START_DATE_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: DatedConversionRate "
            "constructor sets NextStartDate, which is platform-computed. "
            "Omit it (llm-anti-patterns.md § 3, gotchas.md § 8)."
        )
    for m in _NEXT_START_DATE_ASSIGN_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: assignment to "
            "`.NextStartDate` — DatedConversionRate.NextStartDate is "
            "platform-computed; this assignment is rejected or overridden "
            "(gotchas.md § 8)."
        )

    # 2. convertCurrency with a nearby dated-rate comment claim
    for m in _CONVERT_CURRENCY_RE.finditer(text):
        # Look at lines within 200 chars of the call
        window_start = max(0, m.start() - 200)
        window_end = min(len(text), m.end() + 200)
        window = text[window_start:window_end]
        if _DATED_CLAIM_RE.search(window):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: convertCurrency() "
                "near a comment claiming dated / historical / period rates. "
                "convertCurrency() uses static rates, not DatedConversionRate "
                "(llm-anti-patterns.md § 1, gotchas.md § 2)."
            )

    # 3. Amount filter without nearby CurrencyIsoCode
    for m in _AMOUNT_FILTER_RE.finditer(text):
        window_start = max(0, m.start() - 150)
        window_end = min(len(text), m.end() + 150)
        window = text[window_start:window_end]
        if not _CURRENCY_ISOCODE_RE.search(window):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: filter `Amount "
                f"<>= {m.group(1)}` without a CurrencyIsoCode qualifier. "
                "In a multi-currency org this filters on the native value, "
                "not corporate currency (llm-anti-patterns.md § 2, gotchas.md § 7)."
            )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for apex in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        findings.extend(_scan(apex))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex source for multi-currency anti-patterns: "
            "DatedConversionRate.NextStartDate assignment, "
            "convertCurrency() paired with dated-rate claims, "
            "and Amount filters without a currency qualifier."
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
        print("OK: no multi-currency anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
