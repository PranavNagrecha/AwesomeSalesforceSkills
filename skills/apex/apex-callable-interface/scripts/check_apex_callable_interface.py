#!/usr/bin/env python3
"""Checker for Apex Callable interface usage.

Flags high-signal mistakes:

  1. `switch on action` without a `when else` throw branch.
  2. `Type.forName(...).newInstance()` chained without a null check.
  3. `implements Callable` on a class with no action-vocabulary doc comment.
  4. `public` (not `global`) on a Callable class likely intended as an extension point.
  5. Raw cast `(Type) args.get('key')` on a line without a `containsKey` or null check.

Stdlib only. Emits JSON.

Usage:
    python3 check_apex_callable_interface.py --path force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

IMPLEMENTS_CALLABLE = re.compile(
    r"(global|public)\s+(?:with\s+sharing\s+|without\s+sharing\s+|inherited\s+sharing\s+)?"
    r"class\s+(\w+)\s+implements\s+[^{]*\bCallable\b",
    re.IGNORECASE,
)
SWITCH_ON_ACTION_HEADER = re.compile(r"switch\s+on\s+action\s*\{")
WHEN_ELSE = re.compile(r"when\s+else\s*[\{:]")
TYPE_FORNAME_NEWINSTANCE = re.compile(
    r"Type\.forName\s*\([^)]*\)\s*\.\s*newInstance\s*\("
)
ARGS_GET_CAST = re.compile(r"\(\s*(?:Id|Integer|Decimal|String|Boolean|Date|Datetime|Long|Double)\s*\)\s*args\.get\s*\(\s*'([^']+)'\s*\)")
CONTAINS_KEY = re.compile(r"args\.containsKey\s*\(\s*'([^']+)'")


def apex_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.cls"):
        yield path


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    class_match = IMPLEMENTS_CALLABLE.search(text)
    is_callable_class = class_match is not None

    if is_callable_class:
        access, class_name = class_match.group(1), class_match.group(2)
        # Doc comment: look for /** ... */ immediately before the class.
        preceding = text[: class_match.start()]
        has_doc_comment = bool(
            re.search(r"/\*\*[\s\S]{10,}\*/\s*$", preceding.rstrip() + "\n")
        )
        if not has_doc_comment:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "callable-missing-action-docs",
                    "file": str(path),
                    "line": line_of(text, class_match.start()),
                    "message": (
                        f"Class {class_name} implements Callable but has no header "
                        "doc comment documenting action names, args keys, and return."
                    ),
                }
            )

        # Warn if public in a file path containing 'package' or 'extension' (likely extension point)
        path_lower = str(path).lower()
        if access == "public" and ("extension" in path_lower or "package" in path_lower):
            issues.append(
                {
                    "severity": "LOW",
                    "rule": "callable-public-not-global",
                    "file": str(path),
                    "line": line_of(text, class_match.start()),
                    "message": (
                        f"Callable class {class_name} is public; if this is a managed "
                        "package extension point, subscribers cannot instantiate it."
                    ),
                }
            )

    for m in SWITCH_ON_ACTION_HEADER.finditer(text):
        brace_start = m.end() - 1  # position of '{'
        depth = 1
        i = brace_start + 1
        while i < len(text) and depth > 0:
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        body = text[brace_start + 1 : i - 1] if depth == 0 else text[brace_start + 1 :]
        if not WHEN_ELSE.search(body):
            issues.append(
                {
                    "severity": "HIGH",
                    "rule": "switch-on-action-no-default",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "'switch on action' without a 'when else' branch. "
                        "Typo actions silently fall through."
                    ),
                }
            )

    for m in TYPE_FORNAME_NEWINSTANCE.finditer(text):
        # Look for a null check for Type.forName within a window before the match.
        window = text[max(0, m.start() - 300) : m.start()]
        if "Type.forName" not in window and "forName" not in window:
            issues.append(
                {
                    "severity": "HIGH",
                    "rule": "type-forname-unchecked",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "Type.forName(...).newInstance() chained without a prior null check "
                        "on Type.forName result."
                    ),
                }
            )

    if is_callable_class:
        cast_offsets = [(m.start(), m.group(1)) for m in ARGS_GET_CAST.finditer(text)]
        guarded = {m.group(1) for m in CONTAINS_KEY.finditer(text)}
        for offset, key in cast_offsets:
            if key not in guarded:
                issues.append(
                    {
                        "severity": "LOW",
                        "rule": "unguarded-args-cast",
                        "file": str(path),
                        "line": line_of(text, offset),
                        "message": (
                            f"Cast on args.get('{key}') without args.containsKey('{key}') guard."
                        ),
                    }
                )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint Apex Callable interface usage.")
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
