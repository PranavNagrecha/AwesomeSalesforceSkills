#!/usr/bin/env python3
"""Static checks for Apex String / regex anti-patterns.

Catches four high-confidence anti-patterns from this skill's references:

  1. `String.format` with printf-style placeholders (`%s`, `%d`).
  2. `Pattern.compile(...)` inside a loop body — should be `static final`.
  3. `String.split(<regex>)` (single-arg) where trailing-empty preservation
     might matter — flagged for review (false positives possible).
  4. `Matcher.group(...)` calls without a `find()` or `matches()` gate
     visible in the same method scope.

Stdlib only. Conservative regexes; signal tool not parser.

Usage:
    python3 check_apex_string_and_regex.py --src-root .
    python3 check_apex_string_and_regex.py --src-root force-app/main/default
    python3 check_apex_string_and_regex.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Smell 1: String.format with %s / %d / %f / %n placeholders.
_PRINTF_FORMAT_RE = re.compile(
    r"String\.format\s*\(\s*['\"][^'\"]*%[sdfn][^'\"]*['\"]",
    re.IGNORECASE,
)

# Smell 2: Pattern.compile inside a for/while body. We do this in two
# passes — find every Pattern.compile, then check whether the enclosing
# method context shows a for/while opening before it without an intervening
# closing brace.
_PATTERN_COMPILE_RE = re.compile(r"\bPattern\.compile\s*\(", re.IGNORECASE)
_LOOP_HEAD_RE = re.compile(r"\b(?:for|while)\s*\(", re.IGNORECASE)

# Smell 3: split(regex) single-arg, where the result is later indexed.
_SPLIT_SINGLE_ARG_RE = re.compile(
    r"\.split\s*\(\s*['\"][^'\"]*['\"]\s*\)",
    re.IGNORECASE,
)
# Heuristic to flag indexing of the result: any [0..9] subscript on a List.
_LIST_INDEX_AFTER_SPLIT_RE = re.compile(r"\[\s*\d+\s*\]")

# Smell 4: m.group(...) without a preceding find()/matches() in the same method.
_MATCHER_GROUP_RE = re.compile(r"\b(\w+)\.group\s*\(", re.IGNORECASE)
_MATCH_GATE_RE = re.compile(r"\.(find|matches)\s*\(", re.IGNORECASE)

# Method-body delimiters — finds the opening `{` of a method.
_METHOD_HEAD_RE = re.compile(
    r"\b(?:public|private|protected|global|static|virtual|override)\s+[\w<>,\s\[\]]+?\b\w+\s*\([^\)]*\)\s*\{",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _enclosing_method(text: str, pos: int) -> tuple[int, int] | None:
    """Return (method_start, method_end) for the method enclosing position
    ``pos``, or None if ``pos`` isn't inside a method body. Crude — finds the
    closest method header before pos and walks braces forward."""
    last_head = None
    for m in _METHOD_HEAD_RE.finditer(text):
        if m.start() > pos:
            break
        last_head = m
    if last_head is None:
        return None
    body_start = last_head.end() - 1
    depth = 0
    i = body_start
    in_string = False
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\":
                i += 1
            elif ch == "'":
                in_string = False
        elif ch == "'":
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return body_start, i
        i += 1
    return body_start, len(text)


def _is_inside_loop(text: str, pos: int) -> bool:
    """Approximate test: between the enclosing method's start and ``pos``,
    is there an unmatched `{` whose head is a `for` / `while`?"""
    method = _enclosing_method(text, pos)
    if method is None:
        return False
    method_start, _ = method
    # Walk from method_start to pos, counting braces and tracking loop heads.
    loop_depth_stack: list[bool] = []  # True = current open brace is a loop body
    i = method_start
    last_head_was_loop = False
    while i < pos:
        ch = text[i]
        if ch == "{":
            loop_depth_stack.append(last_head_was_loop)
            last_head_was_loop = False
        elif ch == "}":
            if loop_depth_stack:
                loop_depth_stack.pop()
        else:
            # Look ahead to see if a for/while head started here
            if _LOOP_HEAD_RE.match(text, i):
                last_head_was_loop = True
        i += 1
    return any(loop_depth_stack)


def _scan_apex_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _PRINTF_FORMAT_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: String.format uses printf-style placeholder; "
            "Apex needs MessageFormat ({0}, {1}). See references/gotchas.md § 2"
        )

    for m in _PATTERN_COMPILE_RE.finditer(text):
        if _is_inside_loop(text, m.start()):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: Pattern.compile inside a loop — "
                "hoist to `private static final Pattern ...` at class scope. "
                "See references/gotchas.md § 3"
            )

    for m in _SPLIT_SINGLE_ARG_RE.finditer(text):
        # Look at the next 200 chars for a numeric subscript on the result.
        tail = text[m.end() : m.end() + 200]
        if _LIST_INDEX_AFTER_SPLIT_RE.search(tail):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: single-arg split(regex) followed by "
                "numeric index — trailing empties may be silently dropped. "
                "Use split(regex, -1) if positional access matters. See references/gotchas.md § 1"
            )

    for m in _MATCHER_GROUP_RE.finditer(text):
        var = m.group(1)
        # Look backwards in the enclosing method for a .find() / .matches() call on the same var.
        method = _enclosing_method(text, m.start())
        if method is None:
            continue
        method_start, _ = method
        prelude = text[method_start : m.start()]
        gate_re = re.compile(rf"\b{re.escape(var)}\.(find|matches)\s*\(", re.IGNORECASE)
        if not gate_re.search(prelude):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: `{var}.group(...)` with no prior "
                f"`{var}.find()` / `{var}.matches()` in this method — will throw "
                "System.StringException at runtime. See references/gotchas.md § 4"
            )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    apex_files = list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))
    findings: list[str] = []
    for apex_file in apex_files:
        findings.extend(_scan_apex_file(apex_file))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex sources for String / regex anti-patterns "
            "(printf format, in-loop Pattern.compile, single-arg split with index access, "
            "ungated Matcher.group)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no String/regex anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
