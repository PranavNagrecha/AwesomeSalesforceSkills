#!/usr/bin/env python3
"""Static checks for Apex Enum anti-patterns.

Scans Apex source for the high-confidence anti-patterns documented in
`references/llm-anti-patterns.md`:

  1. `Enum.valueOf(...)` calls not wrapped in try/catch.
  2. `switch on <Enum>` blocks without a `when else` branch.
  3. `.ordinal()` calls whose result is assigned to a field
     (heuristic: `<sym>.ordinal()` followed by SObject-style
     assignment or JSON.serialize).

Stdlib only.

Usage:
    python3 check_apex_enum_patterns.py --src-root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# `MyEnum.valueOf(<expr>)` — captures the call. valueOf without a try/catch
# wrapping the line is suspicious.
_VALUEOF_RE = re.compile(r"\b([A-Z]\w*)\.valueOf\s*\(\s*([^)]+?)\s*\)")
_SWITCH_ON_RE = re.compile(r"\bswitch\s+on\s+(\w+)\s*\{", re.IGNORECASE)
_WHEN_ELSE_RE = re.compile(r"\bwhen\s+else\b", re.IGNORECASE)
_ORDINAL_RE = re.compile(r"\b(\w+)\.ordinal\s*\(\s*\)")


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _surrounding_try(text: str, pos: int) -> bool:
    """Heuristic: is `pos` inside a try { ... } block at any depth?"""
    # Walk backwards to find the nearest unbalanced `{` and check if the
    # token before it is `try`.
    depth = 0
    i = pos
    while i > 0:
        c = text[i]
        if c == "}":
            depth += 1
        elif c == "{":
            if depth == 0:
                # Look back from i for whitespace then `try`
                j = i - 1
                while j > 0 and text[j] in " \t\r\n":
                    j -= 1
                # Check tail of the prefix for "try"
                if text[max(0, j - 3): j + 1].endswith("try"):
                    return True
                i -= 1
                continue
            depth -= 1
        i -= 1
    return False


def _switch_blocks(text: str) -> list[tuple[int, int, str]]:
    """Return (start, end, switched_var) for each `switch on X { ... }`."""
    blocks: list[tuple[int, int, str]] = []
    for m in _SWITCH_ON_RE.finditer(text):
        var = m.group(1)
        body_start = m.end()
        depth = 1
        i = body_start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        blocks.append((body_start, i, var))
    return blocks


def _scan_apex(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    # 1. Enum.valueOf without try/catch
    for m in _VALUEOF_RE.finditer(text):
        # Skip the safe wrapper definitions themselves (containing the word
        # `try` somewhere in the next 150 chars before — coarse heuristic):
        head = text[max(0, m.start() - 200): m.start()]
        if "try" in head and "{" in head:
            continue
        findings.append(
            f"{path}:{_line_no(text, m.start())}: {m.group(1)}.valueOf(...) "
            "called without an enclosing try/catch — throws "
            "System.NoSuchElementException on unknown input "
            "(references/llm-anti-patterns.md § 1)"
        )

    # 2. switch on <Enum> without when else
    for start, end, var in _switch_blocks(text):
        body = text[start:end]
        if not _WHEN_ELSE_RE.search(body):
            findings.append(
                f"{path}:{_line_no(text, start)}: `switch on {var}` block has "
                "no `when else` branch — missed cases are silent no-ops "
                "(references/llm-anti-patterns.md § 2)"
            )

    # 3. .ordinal() flowing to an SObject field or serialization
    for m in _ORDINAL_RE.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        line = text[line_start:line_end if line_end != -1 else len(text)]
        if (
            "__c" in line
            or "JSON.serialize" in line
            or re.search(r"\.\w+\s*=\s*", line)
        ):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: {m.group(1)}.ordinal() "
                "result appears to be assigned/serialized — ordinals are "
                "positional and shift when values are reordered. Use "
                "`.name()` instead (references/llm-anti-patterns.md § 3)"
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
            "Scan Apex sources for enum anti-patterns "
            "(unwrapped valueOf, non-exhaustive switch, persisted ordinals)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Apex enum anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
