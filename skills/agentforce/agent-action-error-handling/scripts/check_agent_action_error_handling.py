#!/usr/bin/env python3
"""check_agent_action_error_handling.py — lint Apex invocable actions for
agent-hostile error handling.

Scans every *.cls under --manifest-dir that carries @InvocableMethod and
reports (comments and string literals are stripped first):

  * more than one @InvocableMethod in a class — "Only one method in a class can
    have the InvocableMethod annotation" (apexdev 264 L5476)
  * a `throw` inside the @InvocableMethod body — failures should be returned as a result object,
    one result per input "even if errors occur" (apexdev 264 L5372-5373)
  * AuraHandledException in an invocable class (no planner contract;
    UNVERIFIED 2026-10-21)
  * getMessage() assigned to a user-facing field (userMessage / message /
    errorMessage)
  * an HTTP callout without callout=true on the annotation — "If the method
    calls to an external system, add callout=true" (apexdev 264 L5461-5462)

Severity: ERROR only for a missing --manifest-dir (exit 1). Every finding is
WARN (exit 0 unless --strict). An empty directory prints one WARN, exit 0.
Stdlib only.

Usage:
    python3 check_agent_action_error_handling.py --manifest-dir force-app
    python3 check_agent_action_error_handling.py --manifest-dir force-app --strict
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

COMMENTS = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
STRINGS = re.compile(r"'(?:\\.|[^'\\])*'")
INVOCABLE = re.compile(r"@InvocableMethod\b", re.I)
THROW = re.compile(r"\bthrow\s+new\b|\bthrow\s+\w", re.I)
AURA = re.compile(r"\bAuraHandledException\b")
MSG_TO_FIELD = re.compile(r"\.(userMessage|message|errorMessage)\s*=[^;]*getMessage\s*\(", re.I)
CALLOUT = re.compile(r"\bnew\s+Http\s*\(\s*\)\s*\.\s*send\b|\bHttpRequest\b", re.I)
CALLOUT_TRUE = re.compile(r"@InvocableMethod\s*\([^)]*callout\s*=\s*true", re.I | re.S)


def strip(source: str) -> str:
    return STRINGS.sub("''", COMMENTS.sub(" ", source))


def invocable_bodies(text: str) -> list:
    """Body of each @InvocableMethod method, brace-matched. A throw in a
    private helper whose caller catches it (the skeleton's validate()) is fine."""
    bodies = []
    for match in INVOCABLE.finditer(text):
        start = text.find("{", match.end())
        if start < 0:
            continue
        depth = 0
        for pos in range(start, len(text)):
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
                if depth == 0:
                    bodies.append(text[start:pos + 1])
                    break
    return bodies


def check_class(path: Path) -> list:
    text = strip(path.read_text(encoding="utf-8", errors="replace"))
    count = len(INVOCABLE.findall(text))
    if not count:
        return []
    out = []
    if count > 1:
        out.append(f"{path}: {count} @InvocableMethod annotations; only one method in a "
                   "class can carry it (apexdev 264 L5476).")
    if any(THROW.search(body) for body in invocable_bodies(text)):
        out.append(f"{path}: `throw` inside the @InvocableMethod body; return a typed failure "
                   "in the request's slot instead (apexdev 264 L5372-5373).")
    if AURA.search(text):
        out.append(f"{path}: AuraHandledException in an invocable class; return USER_ERROR "
                   "with an authored userMessage.")
    if MSG_TO_FIELD.search(text):
        out.append(f"{path}: getMessage() assigned to a user-facing field; log the raw "
                   "error and return authored copy.")
    if CALLOUT.search(text) and not CALLOUT_TRUE.search(text):
        out.append(f"{path}: HTTP callout without callout=true on @InvocableMethod "
                   "(apexdev 264 L5461-5462).")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint invocable Apex actions for "
                                     "agent-friendly error handling.")
    parser.add_argument("--manifest-dir", required=True, help="Directory to scan for .cls files.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings.")
    args = parser.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    classes = sorted(root.rglob("*.cls"))
    if not classes:
        print(f"WARN: {root}: no .cls files found.")
        return 1 if args.strict else 0
    warns = [w for path in classes for w in check_class(path)]
    for warn in warns:
        print(f"WARN: {warn}")
    print(f"0 error(s), {len(warns)} warning(s).")
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
