#!/usr/bin/env python3
"""Checker for DataWeave-for-Apex anti-patterns and configuration issues.

Scans:
  **/*.dwl            — script source (DataWeaveResource lives in dw/, api_meta 264 L52116)
  **/*.dwl-meta.xml   — the DataWeaveResource metadata file (apiVersion required, L52129-52133)
  **/*.cls            — Apex callers

Rules, each mapped to a gotcha or anti-pattern in this skill:

  E1  ERROR  A `.dwl` stored under `staticresources/`. createScript() "loads a DataWeave
             2.0 script from the .dwl metadata file that is deployed in an org"
             (262 apexrefguide L155951); scripts are DataWeaveResource metadata in the
             dw folder (api_meta 264 L52116). Gotcha 1.
  E2  ERROR  `.dwl` declares a content type DataWeave in Apex does not support:
             application/flatfile, application/xlsx, application/avro
             (apexdev 264 L26979-26982). Anti-pattern 5.
  W2  WARN   A `.dwl` in dw/ with no paired `.dwl-meta.xml` (apiVersion is Required,
             api_meta 264 L52132). Gotcha 6.
  W3  WARN   `as Number`/`as Date`/`as Boolean` without `default` on the same line.
  W4  WARN   `createScript(` inside a `for`/`while` loop body.
  W6  WARN   A catch of the DataWeave exception that never references getMessage().
  W7  WARN   Apex names `Dataweave.ExecuteException` / `Dataweave.ScriptException`; the
             documented type is System.DataWeaveScriptException (apexdev 264 L26887).

Exit codes: 1 on a missing directory or any ERROR; 0 otherwise (WARN included) unless
--strict, which promotes WARN to a failing exit.

Usage:
    python3 check_dataweave_for_apex.py --manifest-dir force-app [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

UNSUPPORTED_MIME = {"application/flatfile", "application/xlsx", "application/avro"}

_RE_DWL_INPUT = re.compile(r"^\s*input\s+\w+\s+(\S+)", re.M)
_RE_DWL_OUTPUT = re.compile(r"^\s*output\s+(\S+)", re.M)
_RE_DWL_AS_TYPE = re.compile(r"\bas\s+(?:Number|Date|Boolean|DateTime)\b")
_RE_CREATE_SCRIPT = re.compile(r"\.createScript\s*\(", re.I)
_RE_LOOP_OPEN = re.compile(r"\b(?:for|while)\s*\(")
_RE_CATCH_DW = re.compile(
    r"catch\s*\(\s*((?:System\.)?DataWeaveScriptException|Dataweave\.(?:Execute|Script)Exception)\s+(\w+)\s*\)",
    re.I,
)
_RE_LEGACY_EXC = re.compile(r"\bDataweave\.(ExecuteException|ScriptException)\b", re.I)
_RE_GET_MESSAGE = re.compile(r"\.getMessage\(\)")

Finding = Tuple[str, str]


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _scan_dwl(path: Path, root: Path) -> List[Finding]:
    out: List[Finding] = []
    rel = path.relative_to(root)
    text = _read(path)
    if text is None:
        return [("ERROR", f"{rel}: could not read file")]

    if "staticresources" in {p.lower() for p in rel.parts}:
        out.append(("ERROR", f"{rel}: E1 DataWeave script stored as a static resource — createScript() loads DataWeaveResource metadata from dw/ (api_meta 264 L52116)"))
    elif not path.with_name(path.name + "-meta.xml").exists():
        out.append(("WARN", f"{rel}: W2 no paired {path.name}-meta.xml — DataWeaveResource requires apiVersion (api_meta 264 L52132)"))

    for regex, kind in ((_RE_DWL_INPUT, "input"), (_RE_DWL_OUTPUT, "output")):
        for match in regex.finditer(text):
            mime = match.group(1).lower()
            if mime in UNSUPPORTED_MIME:
                line_no = text[: match.start()].count("\n") + 1
                out.append(("ERROR", f"{rel}:{line_no}: E2 {kind} type '{mime}' is not supported by DataWeave in Apex (apexdev 264 L26979-26982)"))

    for line_no, raw in enumerate(text.splitlines(), 1):
        if _RE_DWL_AS_TYPE.search(raw) and "default" not in raw:
            out.append(("WARN", f"{rel}:{line_no}: W3 `as <Type>` without `default` — throws on a null source"))
    return out


def _scan_apex(path: Path, root: Path) -> List[Finding]:
    out: List[Finding] = []
    rel = path.relative_to(root)
    text = _read(path)
    if text is None:
        return [("ERROR", f"{rel}: could not read file")]

    lines = text.splitlines()
    loop_stack: List[int] = []
    depth = 0
    pending_loop = 0
    for line_no, raw in enumerate(lines, 1):
        line = re.sub(r"//.*$", "", raw)
        line = re.sub(r"'(?:\\.|[^'\\])*'", "''", line)
        pending_loop += len(_RE_LOOP_OPEN.findall(line))
        for ch in line:
            if ch == "{":
                depth += 1
                if pending_loop > 0:
                    loop_stack.append(depth)
                    pending_loop -= 1
            elif ch == "}":
                if loop_stack and loop_stack[-1] == depth:
                    loop_stack.pop()
                depth -= 1
        if loop_stack and _RE_CREATE_SCRIPT.search(line):
            out.append(("WARN", f"{rel}:{line_no}: W4 createScript() inside a loop — hoist it above; scripts are stateless"))

        legacy = _RE_LEGACY_EXC.search(line)
        if legacy:
            out.append(("WARN", f"{rel}:{line_no}: W7 Dataweave.{legacy.group(1)} is not a documented type — catch System.DataWeaveScriptException (apexdev 264 L26887)"))

        m = _RE_CATCH_DW.search(line)
        if m:
            var = m.group(2)
            window = "\n".join(lines[line_no - 1 : line_no + 8])
            if not re.search(rf"\b{re.escape(var)}\.getMessage\(\)", window) and not _RE_GET_MESSAGE.search(window):
                out.append(("WARN", f"{rel}:{line_no}: W6 catch {m.group(1)} without {var}.getMessage() — diagnostic detail discarded"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Flag DataWeave-for-Apex configuration and call-site issues under the given metadata directory.",
    )
    parser.add_argument("--manifest-dir", default="force-app", help="Root directory of Salesforce metadata (default: force-app).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings as well as ERROR.")
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    findings: List[Finding] = []
    scanned = 0
    for path in sorted(root.rglob("*.dwl")):
        scanned += 1
        findings.extend(_scan_dwl(path, root))
    for path in sorted(root.rglob("*.cls")):
        scanned += 1
        findings.extend(_scan_apex(path, root))

    if scanned == 0:
        print(f"WARN: no .dwl or .cls files found under {root}; nothing to check.")
        return 0

    for level, msg in findings:
        print(f"{level}: {msg}")
    errors = sum(1 for level, _ in findings if level == "ERROR")
    warns = len(findings) - errors
    print(f"Scanned {scanned} file(s): {errors} error(s), {warns} warning(s).")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
