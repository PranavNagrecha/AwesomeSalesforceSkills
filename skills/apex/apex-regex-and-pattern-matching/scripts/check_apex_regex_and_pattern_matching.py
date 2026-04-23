#!/usr/bin/env python3
r"""Checker for Apex regex usage.

Flags the high-signal mistakes from references/llm-anti-patterns.md:

  1. Apex string literals containing a suspected single-escape regex
     metacharacter (e.g. `'\d'` instead of `'\\d'`).
  2. `Pattern.compile(` inside a `for` or `while` loop.
  3. `.split('<metachar>'` without escaping the metacharacter.
  4. `replaceAll` / `replaceFirst` replacement that concatenates a variable
     without `Matcher.quoteReplacement`.
  5. Regex concatenated from user input without `Pattern.quote`.
  6. Pattern with nested quantifiers (`(...+)+`, `(.*)*`, `(.+)+`).
  7. `matches()` called on a string that is likely longer than the pattern
     (heuristic — flags as REVIEW, not HIGH).

Stdlib only. Emits JSON for scoring.

Usage:
    python3 check_apex_regex_and_pattern_matching.py --path force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

SINGLE_ESCAPE_IN_LITERAL = re.compile(
    r"'[^'\n]*?(?<!\\)\\([dswbnDWSB])[^']*?'"
)
COMPILE_IN_LOOP = re.compile(
    r"(for\s*\([^\)]*\)|while\s*\([^\)]*\))[^{]*\{[^}]*Pattern\.compile\s*\(",
    re.DOTALL,
)
SPLIT_METACHAR = re.compile(
    r"\.split\(\s*'((?:[.\|\(\)\$\*\+\?\[\]\{\}\^])|\\[^\\])'\s*[,\)]"
)
REPLACE_WITH_CONCAT = re.compile(
    r"\.(replaceAll|replaceFirst)\s*\(\s*[^,]+,\s*([^)]*\+[^)]*)\)",
)
QUOTE_REPLACEMENT = re.compile(r"Matcher\.quoteReplacement\s*\(")
PATTERN_CONCAT_INPUT = re.compile(
    r"\.(matches|replaceAll|replaceFirst|matcher)\s*\(\s*(?:'[^']*'\s*\+\s*)?\w+\s*(?:\+\s*'[^']*')?\s*\)",
)
PATTERN_QUOTE = re.compile(r"Pattern\.quote\s*\(")
NESTED_QUANT = re.compile(r"\([^()]*[+*][^()]*\)[+*]")
MATCHES_ON_LARGE = re.compile(
    r"(?<![A-Za-z0-9_])(body|content|description|notes?|email(?:Body)?|html|text|payload)\.matches\s*\(",
    re.IGNORECASE,
)


def apex_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.cls"):
        if path.name.endswith("_Test.cls"):
            continue
        yield path
    for path in root.rglob("*.trigger"):
        yield path


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    for m in SINGLE_ESCAPE_IN_LITERAL.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "single-backslash-regex-literal",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    f"Regex literal {m.group(0)!r} uses a single backslash; "
                    "Apex string literals require `\\\\d`, `\\\\w`, etc."
                ),
            }
        )

    for m in COMPILE_IN_LOOP.finditer(text):
        issues.append(
            {
                "severity": "MEDIUM",
                "rule": "pattern-compile-in-loop",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    "Pattern.compile(...) appears inside a loop. Hoist to a "
                    "`private static final Pattern` field to compile once per transaction."
                ),
            }
        )

    for m in SPLIT_METACHAR.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "split-on-unescaped-metachar",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    f"String.split is a regex; delimiter {m.group(1)!r} contains "
                    "an unescaped metacharacter. Escape with `\\\\.` or equivalent."
                ),
            }
        )

    for m in REPLACE_WITH_CONCAT.finditer(text):
        replacement = m.group(2)
        if "quoteReplacement" not in replacement:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "replacement-not-quoted",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "Dynamic replacement concatenation without "
                        "Matcher.quoteReplacement — `$` and `\\\\` in the value will be interpreted."
                    ),
                }
            )

    for m in NESTED_QUANT.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "nested-quantifier",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    f"Pattern fragment {m.group(0)!r} has nested quantifiers. "
                    "This is a classic ReDoS source on adversarial input."
                ),
            }
        )

    for m in MATCHES_ON_LARGE.finditer(text):
        issues.append(
            {
                "severity": "REVIEW",
                "rule": "matches-on-likely-large-string",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    "`.matches()` requires whole-string match; on large fields "
                    "(body, notes, html) this often should be `Pattern...matcher(s).find()`."
                ),
            }
        )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint Apex regex usage.")
    parser.add_argument(
        "--path",
        default="force-app/main/default",
        help="Root directory to scan (default: force-app/main/default).",
    )
    parser.add_argument("--format", choices=["json", "text"], default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.path)
    if not root.exists():
        print(json.dumps({"error": f"path not found: {root}"}))
        return 2

    issues: list[dict] = []
    for apex_path in apex_files(root):
        issues.extend(check_file(apex_path))

    score = sum(SEVERITY_WEIGHTS.get(i["severity"], 0) for i in issues)

    if args.format == "json":
        print(json.dumps({"score": score, "issues": issues}, indent=2))
    else:
        for issue in issues:
            print(
                f"{issue['severity']:8} {issue['file']}:{issue['line']}  "
                f"[{issue['rule']}] {issue['message']}"
            )
        print(f"\nTotal weighted score: {score}")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
