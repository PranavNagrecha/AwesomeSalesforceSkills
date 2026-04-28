#!/usr/bin/env python3
"""Checker script for the apex-with-without-sharing-decision skill.

Scans Apex .cls files in a metadata directory for sharing-keyword
issues:

  P0: A class containing @AuraEnabled has no class-level sharing
      keyword (with / without / inherited sharing). This is the most
      common Apex security regression in production reviews.

  P1: A class declared `without sharing` lacks a `// reason:` comment
      in the 5 lines immediately preceding the class declaration. Per
      repo convention, every elevation must be justified.

  WARN: A class declared `with sharing` calls
        `Database.executeBatch(this` somewhere in its body. Batch jobs
        usually need system context; `with sharing` here may silently
        under-process records.

Stdlib only. Issues print to stderr as `ISSUE:` lines. Exit 1 if any
P0 or P1 finding; exit 0 otherwise (WARN does not fail the build).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

CLASS_DECL_RE = re.compile(
    r"^\s*(?:global|public|private|protected)?\s*"
    r"(?:virtual\s+|abstract\s+)?"
    r"(with\s+sharing|without\s+sharing|inherited\s+sharing)?"
    r"\s*class\s+(\w+)",
    re.IGNORECASE,
)
AURAENABLED_RE = re.compile(r"@AuraEnabled\b", re.IGNORECASE)
EXEC_BATCH_SELF_RE = re.compile(r"Database\.executeBatch\s*\(\s*this\b", re.IGNORECASE)
REASON_COMMENT_RE = re.compile(r"//\s*reason\s*:", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex .cls files for sharing-keyword issues "
            "(missing keywords, unjustified `without sharing`, batch in `with sharing`)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Apex .cls files (default: current directory).",
    )
    return parser.parse_args()


def find_class_declarations(lines: List[str]) -> List[Tuple[int, str, str]]:
    """Return (line_index, keyword_or_empty, class_name) for each class declaration."""
    declarations: List[Tuple[int, str, str]] = []
    for idx, line in enumerate(lines):
        # Skip comments
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        match = CLASS_DECL_RE.match(line)
        if match:
            keyword = (match.group(1) or "").strip().lower()
            class_name = match.group(2)
            declarations.append((idx, keyword, class_name))
    return declarations


def check_file(path: Path) -> Tuple[List[str], List[str], List[str]]:
    """Return (p0_issues, p1_issues, warn_issues) for a single Apex .cls file."""
    p0: List[str] = []
    p1: List[str] = []
    warn: List[str] = []

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ([f"{path}: cannot read file ({exc})"], [], [])

    lines = text.splitlines()
    declarations = find_class_declarations(lines)
    if not declarations:
        return (p0, p1, warn)

    has_aura = bool(AURAENABLED_RE.search(text))
    has_exec_batch_self = bool(EXEC_BATCH_SELF_RE.search(text))

    for line_idx, keyword, class_name in declarations:
        line_no = line_idx + 1

        # P0: AuraEnabled class with no sharing keyword
        if has_aura and not keyword:
            p0.append(
                f"{path}:{line_no}: P0 class `{class_name}` contains @AuraEnabled "
                f"but declares no sharing keyword. Add `with sharing` (or document "
                f"why elevation is required)."
            )

        # P1: `without sharing` with no `// reason:` in the preceding 5 lines
        if keyword == "without sharing":
            window_start = max(0, line_idx - 5)
            preceding = "\n".join(lines[window_start:line_idx])
            if not REASON_COMMENT_RE.search(preceding):
                p1.append(
                    f"{path}:{line_no}: P1 class `{class_name}` is `without sharing` "
                    f"but no `// reason:` comment found in the 5 lines above the "
                    f"class declaration."
                )

        # WARN: `with sharing` class invoking Database.executeBatch(this, ...)
        if keyword == "with sharing" and has_exec_batch_self:
            warn.append(
                f"{path}:{line_no}: WARN class `{class_name}` is `with sharing` and "
                f"calls `Database.executeBatch(this, ...)`. Batch jobs typically need "
                f"system context; verify user-scoped behavior is intended here."
            )

    return (p0, p1, warn)


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ISSUE: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    cls_files = sorted(manifest_dir.rglob("*.cls"))
    if not cls_files:
        print(f"No .cls files found under {manifest_dir}.")
        return 0

    total_p0: List[str] = []
    total_p1: List[str] = []
    total_warn: List[str] = []

    for path in cls_files:
        p0, p1, warn = check_file(path)
        total_p0.extend(p0)
        total_p1.extend(p1)
        total_warn.extend(warn)

    for issue in total_p0 + total_p1 + total_warn:
        print(f"ISSUE: {issue}", file=sys.stderr)

    summary = (
        f"Scanned {len(cls_files)} .cls file(s): "
        f"{len(total_p0)} P0, {len(total_p1)} P1, {len(total_warn)} warn."
    )
    print(summary)

    if total_p0 or total_p1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
