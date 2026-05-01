#!/usr/bin/env python3
"""Static checks for LWC reactive-state anti-patterns in a project tree.

Scans `force-app/**/*.js` and the matching `*.js-meta.xml` for the
high-confidence anti-patterns documented in this skill's
references/llm-anti-patterns.md and references/gotchas.md. Stdlib only.

What this script catches:

  1. `@track` decorator on a primitive-initialized field
     (`@track count = 0`, `@track name = ''`, etc.) — the post–Spring '20
     reactivity contract makes this redundant.
  2. `@track` decorator on a Date/Set/Map-initialized field — the
     decorator does NOT make those reactive (gotcha #1).
  3. `renderedCallback` whose body assigns `this.<field> =` without an
     early-return guard or a compare-then-set pattern (gotcha-style
     infinite-loop trap).
  4. `<componentName>.js-meta.xml` missing an explicit `<apiVersion>`
     (gotcha #6 — implicit api version is a long-lived-org footgun).
  5. `@api` and `@track` on the same field (gotcha #2).

Signal tool, not a gate. Prints findings; exits 1 if any are found.

Usage:
    python3 check_lwc_reactive_state_patterns.py --src-root .
    python3 check_lwc_reactive_state_patterns.py --src-root force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# `@track countOrName = 0|''|false|true|null;` — primitive initializer.
_TRACK_PRIMITIVE_RE = re.compile(
    r"@track\s+(\w+)\s*=\s*(0|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|false|true|null|undefined)\s*;",
)
# `@track x = new Date()` / `new Set(...)` / `new Map(...)`
_TRACK_NONREACTIVE_TYPE_RE = re.compile(
    r"@track\s+(\w+)\s*=\s*new\s+(Date|Set|Map)\b",
)
# `@api` and `@track` on the same field. Match a stretch up to the next `;`
# or newline-end-of-decl that includes both decorators on one declaration.
_API_TRACK_SAME_FIELD_RE = re.compile(
    r"(?:@api\s+@track|@track\s+@api)\s+\w+",
)
# `renderedCallback() { ... }` — naive but precise enough for a smell check.
_RENDERED_CALLBACK_RE = re.compile(
    r"renderedCallback\s*\(\s*\)\s*\{(?P<body>(?:[^{}]|\{[^{}]*\})*)\}",
)
# `this.x = ` inside renderedCallback body.
_THIS_ASSIGN_RE = re.compile(r"\bthis\.\w+\s*=")
# Guard patterns that make a write inside renderedCallback safe-ish.
_GUARD_RE = re.compile(
    r"(if\s*\(\s*this\._?has(?:Rendered|Init|Setup)\w*\s*\)\s*return"
    r"|if\s*\(\s*[^)]+!==[^)]+\)|if\s*\(\s*[^)]+!=[^)]+\))",
)

_API_VERSION_RE = re.compile(r"<apiVersion>")


def _scan_js_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    for match in _TRACK_PRIMITIVE_RE.finditer(text):
        line_no = text[: match.start()].count("\n") + 1
        findings.append(
            f"{path}:{line_no}: `@track {match.group(1)}` on a primitive — "
            "the post–Spring '20 reactivity contract makes this redundant "
            "(see references/llm-anti-patterns.md § 1)"
        )

    for match in _TRACK_NONREACTIVE_TYPE_RE.finditer(text):
        line_no = text[: match.start()].count("\n") + 1
        findings.append(
            f"{path}:{line_no}: `@track {match.group(1)}` initialized to "
            f"`new {match.group(2)}()` — Date/Set/Map are NOT reactive even "
            "with @track. Use re-create-and-reassign "
            "(see references/gotchas.md § 1)"
        )

    for match in _API_TRACK_SAME_FIELD_RE.finditer(text):
        line_no = text[: match.start()].count("\n") + 1
        findings.append(
            f"{path}:{line_no}: `@api` and `@track` on the same field is "
            "unsupported behavior (see references/gotchas.md § 2)"
        )

    for cb_match in _RENDERED_CALLBACK_RE.finditer(text):
        body = cb_match.group("body")
        if _THIS_ASSIGN_RE.search(body) and not _GUARD_RE.search(body):
            line_no = text[: cb_match.start()].count("\n") + 1
            findings.append(
                f"{path}:{line_no}: renderedCallback writes a reactive "
                "property without a `_hasRenderedOnce` guard or compare-then-set "
                "pattern — likely infinite re-render "
                "(see references/llm-anti-patterns.md § 3)"
            )

    return findings


def _scan_meta_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]
    if not _API_VERSION_RE.search(text):
        findings.append(
            f"{path}: <apiVersion> not declared — pin it explicitly. "
            "Reactivity behavior depends on API version "
            "(see references/gotchas.md § 6)"
        )
    return findings


def scan_tree(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    js_files = list(root.rglob("*.js"))
    # Only the LWC components, not Node tooling. The convention is that LWC
    # files sit beside a `<name>.js-meta.xml`.
    lwc_js_files = [p for p in js_files if (p.with_suffix(".js-meta.xml")).exists()]
    meta_files = [p.with_suffix(".js-meta.xml") for p in lwc_js_files]

    for jf in lwc_js_files:
        findings.extend(_scan_js_file(jf))
    for mf in meta_files:
        findings.extend(_scan_meta_file(mf))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC source for reactive-state anti-patterns: "
            "redundant @track, Date/Set/Map under @track, unguarded "
            "renderedCallback writes, and missing apiVersion."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the source tree to scan (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no LWC reactive-state anti-patterns detected.")
        return 0

    for finding in findings:
        print(f"WARN: {finding}", file=sys.stderr)
    print(
        f"\n{len(findings)} finding(s). See references/llm-anti-patterns.md "
        "and references/gotchas.md for rationale and the correct pattern.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
