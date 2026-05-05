#!/usr/bin/env python3
"""Static heuristics for LWC LDS write code.

Walks an LWC source tree (typically `force-app/main/default/lwc/`) and
flags concrete code-smell patterns this skill cares about:

  1. updateRecord with `Id` at the top level of recordInput (REST muscle memory).
  2. Schema-import objects used as fields keys without `.fieldApiName`.
  3. catch blocks reading `err.message` instead of the structured UI API envelope.
  4. Imports of nonexistent `updateRecords` (plural) from `lightning/uiRecordApi`.
  5. `await updateRecord(...)` inside a `for` / `for...of` loop (sequential bulk).
  6. Spreading a wired record into `fields` (likely includes read-only fields).
  7. `deleteRecord` whose resolved value is read (it is undefined).

Usage:
    python3 check_lwc_lds_writes.py [--manifest-dir path]

Stdlib only — no pip dependencies. Exits 1 when any issue is found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Static heuristics for LWC LDS write code.",
    )
    parser.add_argument(
        "--manifest-dir",
        default="force-app",
        help="Root directory of the SFDX project (default: force-app).",
    )
    return parser.parse_args()


JS_FILE_GLOBS = ("**/lwc/**/*.js",)


def iter_lwc_js_files(root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in JS_FILE_GLOBS:
        for path in root.glob(pattern):
            if path in seen:
                continue
            seen.add(path)
            if path.is_file() and "__tests__" not in path.parts:
                yield path


# ----- pattern matchers ---------------------------------------------------

# updateRecord({ Id: ... }) at top-level (regardless of whitespace, single quote, etc.)
ID_TOPLEVEL_RE = re.compile(
    r"updateRecord\s*\(\s*\{\s*Id\s*:",
    re.MULTILINE,
)

# fields: { [NAME_FIELD]: ... } (computed key without .fieldApiName)
COMPUTED_KEY_RE = re.compile(
    r"\[\s*([A-Z_][A-Z0-9_]*)\s*\]\s*:",
)

# catch (err) { ... err.message ... } in proximity to updateRecord/createRecord/deleteRecord
ERR_MESSAGE_RE = re.compile(
    r"\b(updateRecord|createRecord|deleteRecord)\b[\s\S]{0,800}?catch\s*\([^)]*\)\s*\{[\s\S]{0,400}?\berr(?:or)?\.message\b",
)

# import { updateRecords ... } from 'lightning/uiRecordApi' — does not exist
PLURAL_IMPORT_RE = re.compile(
    r"import\s*\{[^}]*\bupdateRecords\b[^}]*\}\s*from\s*['\"]lightning/uiRecordApi['\"]",
)

# await updateRecord(...) inside a for / for-of / for-in loop
FOR_LOOP_AWAIT_RE = re.compile(
    r"for\s*\([^)]*\)\s*\{[^}]*?await\s+(updateRecord|createRecord|deleteRecord)\s*\(",
    re.DOTALL,
)

# fields: { ...someRecord ...
SPREAD_INTO_FIELDS_RE = re.compile(
    r"fields\s*:\s*\{\s*\.\.\.",
)

# Reading the resolved value of deleteRecord (deleteRecord(...).then(x => x.foo) or const r = await deleteRecord(...); r.something)
DELETERECORD_USE_RE = re.compile(
    r"(?:const|let|var)\s+(\w+)\s*=\s*await\s+deleteRecord\s*\([^)]*\)\s*;",
)

# .fieldApiName / .objectApiName presence (used to filter false positives on COMPUTED_KEY_RE)
FIELD_API_NAME_USE_RE = re.compile(r"\.(fieldApiName|objectApiName)\b")


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []
    rel = path.as_posix()

    if ID_TOPLEVEL_RE.search(text):
        issues.append(
            f"{rel}: updateRecord called with `Id` at top level of recordInput. "
            "Move Id INSIDE `fields`: updateRecord({ fields: { Id, ... } })."
        )

    # Computed keys without .fieldApiName usage anywhere in file = likely bug
    if COMPUTED_KEY_RE.search(text) and not FIELD_API_NAME_USE_RE.search(text):
        # only flag if file also contains an LDS write call, to reduce noise
        if re.search(r"\b(updateRecord|createRecord)\b", text):
            issues.append(
                f"{rel}: file uses computed schema-import keys ([X_FIELD]:) but never "
                "dereferences `.fieldApiName`. For LDS writes, keys must be string API names."
            )

    if ERR_MESSAGE_RE.search(text):
        issues.append(
            f"{rel}: catch block near LDS write reads `err.message`. Use "
            "`err.body.output.fieldErrors` and `err.body.output.errors` for structured UI API errors."
        )

    if PLURAL_IMPORT_RE.search(text):
        issues.append(
            f"{rel}: imports `updateRecords` (plural) from lightning/uiRecordApi. "
            "That export does not exist. Use Apex DML for bulk writes."
        )

    if FOR_LOOP_AWAIT_RE.search(text):
        issues.append(
            f"{rel}: `await updateRecord/createRecord/deleteRecord` inside a `for` loop. "
            "Each iteration is a UI API round-trip. Move bulk writes to Apex DML."
        )

    if SPREAD_INTO_FIELDS_RE.search(text):
        issues.append(
            f"{rel}: spread (`...`) used inside `fields:` literal. Likely includes "
            "read-only fields (LastModifiedDate, formulas) that will reject the write. "
            "Maintain an explicit dirty-fields whitelist instead."
        )

    for match in DELETERECORD_USE_RE.finditer(text):
        var_name = match.group(1)
        # check if var_name is referenced after the assignment
        after = text[match.end():]
        if re.search(rf"\b{re.escape(var_name)}\b", after):
            issues.append(
                f"{rel}: reads the resolved value of `deleteRecord` "
                f"(variable `{var_name}`). deleteRecord resolves to undefined."
            )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists():
        print(f"WARN: manifest directory not found: {root}", file=sys.stderr)
        return 1

    js_files = list(iter_lwc_js_files(root))
    if not js_files:
        print(f"No LWC JS files under {root}/**/lwc/**/*.js — nothing to check.")
        return 0

    issues: list[str] = []
    for path in js_files:
        issues.extend(check_file(path))

    if not issues:
        print(f"OK: {len(js_files)} LWC JS files scanned, no LDS-write issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
