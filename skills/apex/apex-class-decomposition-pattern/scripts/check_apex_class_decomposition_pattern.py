#!/usr/bin/env python3
"""
check_apex_class_decomposition_pattern.py

Static checker for the lightweight Domain / Service / Selector decomposition
pattern documented in this skill. Scans Apex `.cls` files for three signals
that indicate the pattern is being violated:

  P0  Class name suggests a trigger handler (matches *Handler or *Trigger*)
      AND the file contains an inline SOQL query [SELECT ...].
      Action: extract a <X>Selector and route the query through it.

  P1  Class is over 500 lines AND contains both inline SOQL [SELECT ...]
      and DML (insert/update/delete/upsert/merge).
      Action: split by role (Domain / Service / Selector).

  P0  Class extends BaseSelector AND contains DML
      (insert/update/delete/upsert/merge).
      Action: BaseSelector subclasses must be read-only.

stdlib only. Exits 1 on any P0 or P1 finding, 0 otherwise.

Usage:
    python3 check_apex_class_decomposition_pattern.py <path> [<path> ...]

Each <path> may be a .cls file or a directory (recursively scanned).
"""

from __future__ import annotations

import os
import re
import sys
from typing import Iterable, List, Tuple

SOQL_RE = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
DML_RE = re.compile(r"\b(?:insert|update|delete|upsert|merge)\s+[A-Za-z_]", re.IGNORECASE)
HANDLER_NAME_RE = re.compile(r"\b(?:class|interface)\s+([A-Za-z0-9_]*(?:Handler|Trigger[A-Za-z0-9_]*))\b")
EXTENDS_BASESELECTOR_RE = re.compile(r"\bextends\s+BaseSelector\b")
CLASS_NAME_RE = re.compile(r"\bclass\s+([A-Za-z0-9_]+)\b")

LINE_THRESHOLD_P1 = 500


def iter_cls_files(paths: Iterable[str]) -> Iterable[str]:
    for raw in paths:
        if os.path.isfile(raw) and raw.endswith(".cls"):
            yield raw
        elif os.path.isdir(raw):
            for root, _dirs, files in os.walk(raw):
                for name in files:
                    if name.endswith(".cls"):
                        yield os.path.join(root, name)
        else:
            print(f"WARN: skipping non-.cls or missing path: {raw}", file=sys.stderr)


def analyse(path: str) -> List[Tuple[str, str]]:
    """Return a list of (severity, message) findings for one .cls file."""
    findings: List[Tuple[str, str]] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [("P0", f"{path}: could not read file ({exc})")]

    line_count = text.count("\n") + 1
    has_soql = bool(SOQL_RE.search(text))
    has_dml = bool(DML_RE.search(text))
    handler_match = HANDLER_NAME_RE.search(text)
    extends_baseselector = bool(EXTENDS_BASESELECTOR_RE.search(text))
    class_match = CLASS_NAME_RE.search(text)
    class_name = class_match.group(1) if class_match else os.path.basename(path)

    # P0 — handler-named class with embedded SOQL
    if handler_match and has_soql:
        findings.append((
            "P0",
            f"{path}: class '{handler_match.group(1)}' looks like a trigger handler "
            f"and contains inline [SELECT]. Extract a <X>Selector extending BaseSelector "
            f"and call it from the handler.",
        ))

    # P0 — Selector subclass that performs DML
    if extends_baseselector and has_dml:
        findings.append((
            "P0",
            f"{path}: class '{class_name}' extends BaseSelector but contains DML "
            f"(insert/update/delete/upsert/merge). Selectors must be read-only — "
            f"move DML to a Service extending BaseService.",
        ))

    # P1 — large class mixing SOQL and DML
    if line_count > LINE_THRESHOLD_P1 and has_soql and has_dml:
        findings.append((
            "P1",
            f"{path}: class '{class_name}' is {line_count} lines AND mixes SOQL with DML. "
            f"Split by role: extract Selector first, then Service, then Domain "
            f"(see skills/apex/apex-class-decomposition-pattern/SKILL.md).",
        ))

    return findings


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    files = list(iter_cls_files(argv[1:]))
    if not files:
        print("No .cls files found in the supplied paths.", file=sys.stderr)
        return 0

    all_findings: List[Tuple[str, str]] = []
    for path in files:
        all_findings.extend(analyse(path))

    if not all_findings:
        print(f"OK - scanned {len(files)} file(s); no decomposition violations found.")
        return 0

    p0 = [f for f in all_findings if f[0] == "P0"]
    p1 = [f for f in all_findings if f[0] == "P1"]

    for severity, message in all_findings:
        print(f"[{severity}] {message}")

    print("")
    print(f"Summary: {len(p0)} P0, {len(p1)} P1, scanned {len(files)} file(s).")

    if p0 or p1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
