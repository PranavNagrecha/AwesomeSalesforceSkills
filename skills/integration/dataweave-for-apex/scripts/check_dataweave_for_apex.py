#!/usr/bin/env python3
"""Checker for DataWeave-for-Apex anti-patterns and configuration issues.

Scans:
  staticresources/*.dwl       — script source
  staticresources/*.resource-meta.xml — content type and cache control
  classes/**.cls              — Apex callers

Flags concrete patterns this skill warns against:

  W1  Static resource has cacheControl != Public — re-parse on every call
  W2  Static resource has contentType != application/dw — won't load
  W3  `.dwl` references `as Number`/`as Date`/`as Boolean` without `default`
  W4  Apex `Dataweave.Script.createScript(` inside a `for`/`while` loop body
  W5  `.dwl` declares input/output MIME type outside the supported set
  W6  Apex catches Dataweave.ExecuteException without referencing getMessage()

Usage:
    python3 check_dataweave_for_apex.py
    python3 check_dataweave_for_apex.py --manifest-dir force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List

SUPPORTED_MIME = {
    "application/json",
    "application/xml",
    "application/csv",
    "application/x-www-form-urlencoded",
    "application/dw",
    "text/plain",
}

_RE_RESOURCE_CACHE = re.compile(r"<cacheControl>\s*(\w+)\s*</cacheControl>", re.I)
_RE_RESOURCE_TYPE = re.compile(r"<contentType>\s*([^<]+?)\s*</contentType>", re.I)
_RE_DWL_INPUT = re.compile(r"^\s*input\s+\w+\s+(\S+)\s*$", re.M)
_RE_DWL_OUTPUT = re.compile(r"^\s*output\s+(\S+)\s*$", re.M)
_RE_DWL_AS_TYPE = re.compile(r"\bas\s+(?:Number|Date|Boolean|DateTime)\b")
_RE_DEFAULT_NEAR_AS = re.compile(r"\bdefault\b.{0,80}\bas\s+(?:Number|Date|Boolean|DateTime)\b|\bas\s+(?:Number|Date|Boolean|DateTime)\b.{0,80}\bdefault\b")
_RE_CREATE_SCRIPT = re.compile(r"Dataweave\.Script\.createScript\(")
_RE_LOOP_OPEN = re.compile(r"\b(?:for|while)\s*\(")
_RE_CATCH_EXEC = re.compile(r"catch\s*\(\s*Dataweave\.ExecuteException\s+(\w+)\s*\)")
_RE_GET_MESSAGE = re.compile(r"\.getMessage\(\)")


def _scan_dwl(path: Path) -> List[str]:
    out: List[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: ERROR could not read ({exc})"]

    for match in _RE_DWL_INPUT.finditer(text):
        mime = match.group(1)
        if mime not in SUPPORTED_MIME:
            line_no = text[:match.start()].count("\n") + 1
            out.append(
                f"{path}:{line_no}: W5  unsupported input MIME '{mime}' — supported: {', '.join(sorted(SUPPORTED_MIME))}"
            )
    for match in _RE_DWL_OUTPUT.finditer(text):
        mime = match.group(1)
        if mime not in SUPPORTED_MIME:
            line_no = text[:match.start()].count("\n") + 1
            out.append(
                f"{path}:{line_no}: W5  unsupported output MIME '{mime}' — supported: {', '.join(sorted(SUPPORTED_MIME))}"
            )

    for line_no, raw in enumerate(text.splitlines(), 1):
        if _RE_DWL_AS_TYPE.search(raw) and "default" not in raw:
            # Soft heuristic — check the surrounding 80 chars in same logical line.
            out.append(
                f"{path}:{line_no}: W3  `as <Type>` without `default` — throws on null source"
            )
    return out


def _scan_resource_meta(path: Path) -> List[str]:
    out: List[str] = []
    # Only check resources whose paired `.resource` is a `.dwl` script.
    paired_dwl = path.with_suffix("").with_suffix(".dwl")
    if not paired_dwl.exists():
        return out
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: ERROR could not read ({exc})"]

    cache = _RE_RESOURCE_CACHE.search(text)
    if cache and cache.group(1).lower() != "public":
        out.append(
            f"{path}: W1  cacheControl='{cache.group(1)}' — DataWeave scripts should be Public to avoid per-call re-parse"
        )

    ctype = _RE_RESOURCE_TYPE.search(text)
    if ctype and ctype.group(1).lower() != "application/dw":
        out.append(
            f"{path}: W2  contentType='{ctype.group(1)}' — must be application/dw for Dataweave.Script.createScript to load"
        )
    return out


def _scan_apex(path: Path) -> List[str]:
    out: List[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: ERROR could not read ({exc})"]

    lines = text.splitlines()
    loop_depth = 0
    brace_after_loop_open: List[int] = []
    pending_loop = 0
    for line_no, raw in enumerate(lines, 1):
        # Strip line comments and string literals (rough).
        line = re.sub(r"//.*$", "", raw)
        line = re.sub(r"'(?:\\.|[^'\\])*'", "''", line)
        # Loop-depth tracking by counting open/close braces after a loop keyword.
        for _ in _RE_LOOP_OPEN.finditer(line):
            pending_loop += 1
        for ch in line:
            if ch == "{" and pending_loop > 0:
                loop_depth += 1
                pending_loop -= 1
                brace_after_loop_open.append(loop_depth)
            elif ch == "}" and brace_after_loop_open and loop_depth == brace_after_loop_open[-1]:
                brace_after_loop_open.pop()
                loop_depth -= 1
        if loop_depth > 0 and _RE_CREATE_SCRIPT.search(line):
            out.append(
                f"{path}:{line_no}: W4  Dataweave.Script.createScript() inside a loop — hoist above; scripts are stateless"
            )

        m = _RE_CATCH_EXEC.search(line)
        if m:
            var = m.group(1)
            window = "\n".join(lines[line_no:line_no + 8])
            if not _RE_GET_MESSAGE.search(window) and var not in window:
                out.append(
                    f"{path}:{line_no}: W6  catch Dataweave.ExecuteException without referencing {var}.getMessage() — diagnostic detail discarded"
                )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Flag DataWeave-for-Apex configuration and call-site issues under the given metadata directory.",
    )
    parser.add_argument(
        "--manifest-dir",
        default="force-app",
        help="Root directory of Salesforce metadata (default: force-app).",
    )
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"Manifest directory not found: {root}", file=sys.stderr)
        return 2

    findings: List[str] = []
    files_scanned = 0
    for path in root.rglob("*.dwl"):
        files_scanned += 1
        findings.extend(_scan_dwl(path))
    for path in root.rglob("*.resource-meta.xml"):
        files_scanned += 1
        findings.extend(_scan_resource_meta(path))
    for path in root.rglob("*.cls"):
        files_scanned += 1
        findings.extend(_scan_apex(path))

    if files_scanned == 0:
        print(f"No DataWeave or Apex files found under {root}", file=sys.stderr)
        return 0

    if not findings:
        print(f"OK: scanned {files_scanned} files, no DataWeave-for-Apex issues found.")
        return 0

    for line in findings:
        print(f"WARN: {line}", file=sys.stderr)
    print(
        f"\nWARN: found {len(findings)} DataWeave-for-Apex issue(s) across {files_scanned} file(s).",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
