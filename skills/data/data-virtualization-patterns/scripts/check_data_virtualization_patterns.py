#!/usr/bin/env python3
"""Static checks for data-virtualization (Salesforce Connect) anti-patterns.

Scans Apex sources, trigger metadata XML, and flow metadata XML for
patterns that External Objects (`__x`) cannot support.

Anti-patterns detected:

  1. Apex triggers on a `__x` object — not supported by the platform.
  2. Validation rule metadata XML referencing a `__x` object — also
     not supported.
  3. Record-triggered flow metadata referencing a `__x` source object.
  4. Indirect Lookup metadata XML where the referenced field is not
     marked as External Id (heuristic — flags for review).

Stdlib only.

Usage:
    python3 check_data_virtualization_patterns.py --src-root .
    python3 check_data_virtualization_patterns.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 1. Apex trigger on `__x` object.
_TRIGGER_HEADER_RE = re.compile(
    r"\btrigger\s+\w+\s+on\s+(\w+__x)\b",
    re.IGNORECASE,
)

# 2. Validation rule XML / object directory ending in __x.
_OBJECT_X_DIR_RE = re.compile(r"objects/[^/]+__x/", re.IGNORECASE)

# 3. Record-triggered flow XML with start.object referencing __x.
_FLOW_START_OBJECT_RE = re.compile(
    r"<object>\s*(\w+__x)\s*</object>",
    re.IGNORECASE,
)

# 4. Indirect Lookup field XML.
_INDIRECT_LOOKUP_RE = re.compile(
    r"<type>IndirectLookup</type>",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _TRIGGER_HEADER_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: trigger declared on "
            f"`{m.group(1)}` — External Objects do not support Apex triggers. "
            "Drive automation through the source system or replicate the data "
            "into a custom object (llm-anti-patterns.md § 1, gotchas.md § 1)."
        )

    return findings


def _scan_xml(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    spath = str(path)

    # Validation rule under an __x object directory
    if _OBJECT_X_DIR_RE.search(spath) and (
        ".validationRule-meta.xml" in spath or "/validationRules/" in spath
    ):
        findings.append(
            f"{path}: validation rule metadata under an External Object "
            "(`__x`) directory — validation rules do not run on External "
            "Objects (gotchas.md § 2)."
        )

    # Record-triggered flow on __x
    for m in _FLOW_START_OBJECT_RE.finditer(text):
        if path.suffix.lower() == ".xml" and "flow" in spath.lower():
            findings.append(
                f"{path}:{_line_no(text, m.start())}: flow start object "
                f"`{m.group(1)}` is an External Object — record-triggered "
                "flows do not fire on External Objects "
                "(llm-anti-patterns.md § 1, gotchas.md § 2)."
            )

    # IndirectLookup heuristic flag (review for uniqueness on parent)
    for m in _INDIRECT_LOOKUP_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: IndirectLookup defined — "
            "verify the referenced parent field is marked External Id AND "
            "Unique (gotchas.md § 3)."
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
    for xml in root.rglob("*.xml"):
        findings.extend(_scan_xml(xml))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for External Object / Salesforce "
            "Connect anti-patterns: Apex triggers on `__x` objects, "
            "validation rules under `__x` objects, record-triggered flows "
            "on `__x` start objects, and IndirectLookup definitions that "
            "need uniqueness review on the parent field."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the Salesforce source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no data-virtualization anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
