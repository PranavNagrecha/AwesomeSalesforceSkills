#!/usr/bin/env python3
"""Static checks for Apex `switch on` blocks operating over SObject expressions.

Catches three high-confidence anti-patterns documented in this skill:

  1. Switch-on-SObject without a `when else` branch — the silent-skip bug.
  2. Redundant cast inside a typed `when` branch — `Account a = (Account) record;`
     where `a` was already typed by the binding.
  3. `Type.forName(...)` used inside a `switch on` expression — wrong type
     entirely (returns System.Type, not SObject).

Stdlib only. Tokenizes with deliberately conservative regexes — Apex is
not a regular language so this is a *signal* tool, not a parser. False
negatives are accepted; false positives should be rare.

Usage:
    python3 check_apex_switch_on_sobject.py --src-root .
    python3 check_apex_switch_on_sobject.py --src-root force-app/main/default
    python3 check_apex_switch_on_sobject.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Match "switch on <expr> {" — we'll inspect the matched body for `when else`
# and the `Type.forName(...)` smell in the expression.
_SWITCH_OPEN_RE = re.compile(
    r"\bswitch\s+on\s+(?P<expr>[^\{\n]+)\{",
    re.IGNORECASE,
)

_WHEN_ELSE_RE = re.compile(r"\bwhen\s+else\b", re.IGNORECASE)
_TYPE_FORNAME_RE = re.compile(r"\bType\.forName\s*\(", re.IGNORECASE)

# Loose match for `when SObjectType varName {` — captures type and bound var.
_BINDING_HEADER_RE = re.compile(
    r"\bwhen\s+(?P<type>[A-Za-z_][\w]*(?:__c|__e|__r)?)\s+(?P<var>[A-Za-z_]\w*)\s*\{",
    re.IGNORECASE,
)

# Redundant cast inside a binding branch: <SameType> <newvar> = (<SameType>) <boundvar>;
_REDUNDANT_CAST_TPL = r"\b{type}\s+\w+\s*=\s*\(\s*{type}\s*\)\s*{var}\s*[;,)]"


def _find_matching_brace(text: str, open_pos: int) -> int:
    """Return the index of `}` matching the `{` at ``open_pos``, or len(text)
    if unbalanced. Skips quoted strings and comments to avoid false matches."""
    depth = 0
    i = open_pos
    in_string = False
    in_line_comment = False
    in_block_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
        elif in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if ch == "\\":
                i += 1
            elif ch == "'":
                in_string = False
        else:
            if ch == "/" and nxt == "/":
                in_line_comment = True
                i += 1
            elif ch == "/" and nxt == "*":
                in_block_comment = True
                i += 1
            elif ch == "'":
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return len(text)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_apex_file(path: Path) -> list[str]:
    """Return findings for one .cls / .trigger file."""
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for m in _SWITCH_OPEN_RE.finditer(text):
        expr = m.group("expr").strip()
        body_start = m.end() - 1
        body_end = _find_matching_brace(text, body_start)
        body = text[body_start : body_end + 1]
        line_no = _line_no(text, m.start())

        if _TYPE_FORNAME_RE.search(expr):
            findings.append(
                f"{path}:{line_no}: switch on `{expr}` uses Type.forName() — "
                "Type.forName returns System.Type, not an SObject. Use "
                "Schema.getGlobalDescribe().get(name).newSObject() instead "
                "(references/gotchas.md § 2)"
            )

        has_binding = bool(_BINDING_HEADER_RE.search(body))
        if has_binding and not _WHEN_ELSE_RE.search(body):
            findings.append(
                f"{path}:{line_no}: switch on `{expr}` has no `when else` branch — "
                "unhandled SObject types will silently skip "
                "(references/gotchas.md § 1)"
            )

        for binding in _BINDING_HEADER_RE.finditer(body):
            t = binding.group("type")
            v = binding.group("var")
            if t.lower() in {"null", "else"}:
                continue
            cast_re = re.compile(_REDUNDANT_CAST_TPL.format(type=re.escape(t), var=re.escape(v)))
            if cast_re.search(body):
                rel_line = line_no + body[: binding.start()].count("\n")
                findings.append(
                    f"{path}:{rel_line}: redundant cast inside `when {t} {v}` — "
                    f"`{v}` is already typed {t} in this scope "
                    "(references/llm-anti-patterns.md § 1)"
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
            "Scan Apex sources for switch-on-SObject anti-patterns "
            "(missing when-else, redundant cast, Type.forName misuse)."
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
        print("OK: no switch-on-SObject anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
