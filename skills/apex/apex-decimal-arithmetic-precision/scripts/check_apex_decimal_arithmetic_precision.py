#!/usr/bin/env python3
"""Checker for Apex Decimal arithmetic precision anti-patterns.

Scans Apex (.cls and .trigger) under force-app/ (or any --manifest-dir) and
flags concrete patterns that this skill warns against:

  D1  one-argument `divide(...)` calls — throws on non-terminating divides
  D2  `setScale(n)` single-argument — throws if rounding actually needed
  D3  Integer literal divided by Integer literal where the result is later
      treated as Decimal (e.g. `someInt / 100` assigned to Decimal)
  D4  `Decimal.valueOf(<non-string>)` calls — Double overload reintroduces
      binary-float noise
  D5  `.equals(` invoked on a Decimal-typed expression — likely scale-strict
      compare, usually wrong

Each finding emits `file:line: CODE  description`. Stdlib only.

Usage:
    python3 check_apex_decimal_arithmetic_precision.py
    python3 check_apex_decimal_arithmetic_precision.py --manifest-dir force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List


# Pre-compiled patterns. Apex is reasonably regex-friendly for these surface
# checks; we accept some false-positive risk in exchange for stdlib-only.

_RE_DIVIDE_ONEARG = re.compile(
    r"\.divide\(\s*([^,()]+(?:\([^)]*\))?[^,()]*)\)"
)
_RE_SETSCALE_ONEARG = re.compile(r"\.setScale\(\s*\d+\s*\)")
_RE_INT_DIV_INT = re.compile(r"\b\d+\s*/\s*\d+\b")
_RE_DECIMAL_VALUEOF = re.compile(r"Decimal\.valueOf\(\s*([^)]+)\)")
_RE_DECIMAL_EQUALS = re.compile(r"\b(\w+)\.equals\(")
_RE_DECIMAL_VAR_DECL = re.compile(r"\bDecimal\s+(\w+)\b")
_RE_DECIMAL_LITERAL_ARG = re.compile(r"^\s*['\"]")  # starts with quote → String overload


def _scan_file(path: Path) -> List[str]:
    findings: List[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: ERROR could not read ({exc})"]

    decimal_vars: set[str] = set()
    for line_no, raw in enumerate(text.splitlines(), 1):
        # Strip line comments and string literals to reduce false positives.
        # We don't run a full Apex parser; this is a heuristic.
        line = re.sub(r"//.*$", "", raw)
        line = re.sub(r"'(?:\\.|[^'\\])*'", "''", line)

        # Track variables declared as Decimal so we can flag .equals() on them.
        for match in _RE_DECIMAL_VAR_DECL.finditer(line):
            decimal_vars.add(match.group(1))

        # D1 — one-arg divide
        for match in _RE_DIVIDE_ONEARG.finditer(line):
            arg = match.group(1)
            # Allow comma-free single-arg only when divisor is a power-of-2/5
            # literal that always terminates against scale-2 numerators (rare).
            if "," in arg:
                continue
            findings.append(
                f"{path}:{line_no}: D1  one-argument divide() — use divide(divisor, scale, RoundingMode)"
            )

        # D2 — one-arg setScale
        for _ in _RE_SETSCALE_ONEARG.finditer(line):
            findings.append(
                f"{path}:{line_no}: D2  setScale(n) without RoundingMode — throws if rounding needed; use setScale(n, RoundingMode.X)"
            )

        # D3 — integer-divided-by-integer in a likely-Decimal context
        # We flag only if the line also references Decimal in a typed way,
        # to avoid matching benign array-index math.
        if _RE_INT_DIV_INT.search(line) and re.search(r"\bDecimal\b", line):
            findings.append(
                f"{path}:{line_no}: D3  integer/integer division in Decimal context — promote at least one operand to Decimal"
            )

        # D4 — Decimal.valueOf with non-String argument
        for match in _RE_DECIMAL_VALUEOF.finditer(line):
            arg = match.group(1).strip()
            if arg.startswith("'") or arg.startswith("\""):
                continue
            if arg.startswith("String."):
                continue
            # Bare integer literal (Decimal.valueOf(7)) is fine — Integer overload.
            if re.fullmatch(r"-?\d+", arg):
                continue
            # Heuristic: anything with a Double-typed source is the danger case.
            if re.search(r"(?:\bDouble\b|\bdouble\b|\)\s*$|\(\s*\(?\s*Double\s*\))", arg):
                findings.append(
                    f"{path}:{line_no}: D4  Decimal.valueOf(Double) reintroduces binary-float noise — use String overload or JSONParser.getDecimalValue()"
                )

        # D5 — .equals on a known Decimal var
        for match in _RE_DECIMAL_EQUALS.finditer(line):
            var = match.group(1)
            if var in decimal_vars:
                findings.append(
                    f"{path}:{line_no}: D5  Decimal.equals() is scale-strict — use == for value-equal compare, or setScale before equals"
                )

    return findings


def _iter_apex_files(root: Path):
    for ext in ("*.cls", "*.trigger"):
        yield from root.rglob(ext)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Flag Apex Decimal arithmetic anti-patterns under the given metadata directory.",
    )
    parser.add_argument(
        "--manifest-dir",
        default="force-app",
        help="Root directory of Apex sources (default: force-app).",
    )
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"Manifest directory not found: {root}", file=sys.stderr)
        return 2

    all_findings: List[str] = []
    files_scanned = 0
    for f in _iter_apex_files(root):
        files_scanned += 1
        all_findings.extend(_scan_file(f))

    if files_scanned == 0:
        print(f"No Apex sources found under {root}", file=sys.stderr)
        return 0

    if not all_findings:
        print(f"OK: scanned {files_scanned} Apex files, no Decimal anti-patterns found.")
        return 0

    for line in all_findings:
        print(f"WARN: {line}", file=sys.stderr)
    print(
        f"\nWARN: found {len(all_findings)} Decimal-arithmetic issue(s) across {files_scanned} file(s).",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
