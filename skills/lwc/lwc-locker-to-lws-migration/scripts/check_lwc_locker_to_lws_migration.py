#!/usr/bin/env python3
"""
check_lwc_locker_to_lws_migration.py

Static checker for the Locker -> Lightning Web Security (LWS) migration.

Scans LWC bundle source files (.js, .html, .js-meta.xml) for patterns that
either (a) actively break under LWS, or (b) are Locker-era workarounds that
should be removed once the org switches to LWS.

Severity model:

  P0  Direct reference to a Locker-only global (SecureElement, SecureWindow,
      SecureDocument, SecureObject) or to Locker-only proxy escape APIs
      (unwrap(), getRawNode()). These produce silent fallback behaviour or
      ReferenceErrors after LWS is enabled.

  P0  A per-bundle / per-component opt-out flag in *.js-meta.xml such as
      <lwsDisabled>, <disableLws>, or 'lws.disabled' at component scope.
      No such flag exists in the Salesforce metadata schema; finding one
      indicates an LLM hallucination or a copy-paste from incorrect docs.

  P1  Use of eval() / new Function('...') / Function('...').
      Off-limits under both Locker and LWS (page CSP). Often introduced as
      a (mistaken) "LWS allows it now" workaround when removing Locker
      pre-compiled-template shims.

  P1  Static-resource load of a known-suspect library name fragment
      (e.g., 'chartjs_locker', 'jspdf_locker', 'd3_locker_fork') that
      indicates a Locker-era patched fork. Should be replaced with an
      upstream build under LWS.

  P2  JSON.parse(JSON.stringify(...)) inside a file that also calls
      loadScript / loadStyle. Often a Locker-era deep-clone-on-input shim
      that becomes harmful under LWS (see references/gotchas.md item 3).

stdlib only. Exits 1 on any P0 or P1 finding, 0 otherwise.

Usage:
    python3 check_lwc_locker_to_lws_migration.py <path> [<path> ...]

Each <path> may be a file (.js / .html / .xml) or a directory (recursively
scanned for LWC bundle files). Designed to be pointed at
`force-app/main/default/lwc` or a single bundle directory.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Iterable, List, Tuple

# --- Patterns -----------------------------------------------------------------

LOCKER_GLOBAL_RE = re.compile(
    r"\b(SecureElement|SecureWindow|SecureDocument|SecureObject)\b"
)
LOCKER_UNWRAP_RE = re.compile(r"\b(unwrap|getRawNode)\s*\(")
EVAL_RE = re.compile(r"(?<![A-Za-z0-9_$])eval\s*\(")
NEW_FUNCTION_RE = re.compile(r"\bnew\s+Function\s*\(")
# Bare `Function('...')` constructor form. Skip when preceded by `new ` (already
# caught by NEW_FUNCTION_RE) or when part of a property access like `.Function(`.
BARE_FUNCTION_CTOR_RE = re.compile(
    r"(?<![A-Za-z0-9_$.])(?<!new\s)Function\s*\(\s*['\"]"
)
DEEP_CLONE_RE = re.compile(r"JSON\.parse\s*\(\s*JSON\.stringify\s*\(")
LOAD_SCRIPT_RE = re.compile(r"\bload(?:Script|Style)\s*\(")
SUSPECT_FORK_RE = re.compile(
    r"@salesforce/resourceUrl/[A-Za-z0-9_]*"
    r"(?:locker|locker_fork|_locker|lockerfork|lockercompat|lockershim)",
    re.IGNORECASE,
)

# Per-component LWS opt-out hallucinations (no such flags exist in metadata schema).
META_LWS_FLAG_RE = re.compile(
    r"<\s*(?:lwsDisabled|disableLws|useLocker|lockerEnabled)\s*>",
    re.IGNORECASE,
)
META_LWS_DOTTED_RE = re.compile(
    r"\blws\.disabled\b",
    re.IGNORECASE,
)

# Files we consider in scope.
JS_EXTS = (".js",)
HTML_EXTS = (".html",)
META_EXTS = (".xml",)


def iter_files(paths: Iterable[str]) -> Iterable[str]:
    for raw in paths:
        if os.path.isfile(raw):
            yield raw
        elif os.path.isdir(raw):
            for root, _dirs, files in os.walk(raw):
                # skip generated and dependency dirs
                if any(skip in root for skip in (
                    os.sep + "node_modules" + os.sep,
                    os.sep + ".sfdx" + os.sep,
                    os.sep + ".sf" + os.sep,
                    os.sep + "__pycache__" + os.sep,
                )):
                    continue
                for name in files:
                    if name.endswith(JS_EXTS + HTML_EXTS + META_EXTS):
                        yield os.path.join(root, name)
        else:
            print(f"WARN: skipping non-file / missing path: {raw}", file=sys.stderr)


def line_of(text: str, idx: int) -> int:
    """1-based line number for character offset idx in text."""
    return text.count("\n", 0, idx) + 1


def analyse(path: str) -> List[Tuple[str, str]]:
    """Return a list of (severity, message) findings for one file."""
    findings: List[Tuple[str, str]] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [("P0", f"{path}: could not read file ({exc})")]

    is_js = path.endswith(JS_EXTS)
    is_meta = path.endswith(".js-meta.xml") or path.endswith(META_EXTS)

    # P0 — Locker-only globals
    for m in LOCKER_GLOBAL_RE.finditer(text):
        findings.append((
            "P0",
            f"{path}:{line_of(text, m.start())}: references Locker-only global "
            f"'{m.group(1)}'. Under LWS this name is undefined; guards using it "
            f"silently take the fallback branch. Delete the reference.",
        ))

    # P0 — unwrap() / getRawNode() in JS files (Locker proxy escape APIs)
    if is_js:
        for m in LOCKER_UNWRAP_RE.finditer(text):
            findings.append((
                "P0",
                f"{path}:{line_of(text, m.start())}: calls Locker-only proxy escape "
                f"API '{m.group(1)}()'. Not available under LWS; remove the call "
                f"and use the DOM node directly.",
            ))

    # P0 — bogus per-component LWS opt-out flag in *.js-meta.xml
    if is_meta:
        for m in META_LWS_FLAG_RE.finditer(text):
            findings.append((
                "P0",
                f"{path}:{line_of(text, m.start())}: per-component LWS opt-out flag "
                f"'{m.group(0)}' is not part of the Salesforce metadata schema. "
                f"There is no per-bundle LWS toggle; remove this element. The only "
                f"valid control is org-level Session Settings.",
            ))
        for m in META_LWS_DOTTED_RE.finditer(text):
            findings.append((
                "P0",
                f"{path}:{line_of(text, m.start())}: 'lws.disabled' is not a valid "
                f"per-component metadata flag. Remove. Use Session Settings at the "
                f"org level instead.",
            ))

    # P1 — eval / new Function / Function('...')
    if is_js:
        for m in EVAL_RE.finditer(text):
            findings.append((
                "P1",
                f"{path}:{line_of(text, m.start())}: uses eval(). Disallowed by "
                f"page CSP under both Locker and LWS. Refactor to a non-eval pattern.",
            ))
        for m in NEW_FUNCTION_RE.finditer(text):
            findings.append((
                "P1",
                f"{path}:{line_of(text, m.start())}: uses 'new Function(...)'. "
                f"Disallowed by page CSP under both Locker and LWS. Refactor.",
            ))
        for m in BARE_FUNCTION_CTOR_RE.finditer(text):
            findings.append((
                "P1",
                f"{path}:{line_of(text, m.start())}: uses 'Function(\"...\")' "
                f"(constructor form). Disallowed by page CSP under both Locker "
                f"and LWS. Refactor.",
            ))

    # P1 — suspect Locker-era patched library fork referenced via @salesforce/resourceUrl
    if is_js:
        for m in SUSPECT_FORK_RE.finditer(text):
            findings.append((
                "P1",
                f"{path}:{line_of(text, m.start())}: imports a static resource "
                f"whose name suggests a Locker-era patched fork "
                f"('{m.group(0)}'). Under LWS, prefer the upstream library build.",
            ))

    # P2 — deep-clone-on-input pattern co-located with loadScript/loadStyle
    if is_js and LOAD_SCRIPT_RE.search(text):
        for m in DEEP_CLONE_RE.finditer(text):
            findings.append((
                "P2",
                f"{path}:{line_of(text, m.start())}: 'JSON.parse(JSON.stringify(...))' "
                f"in a file that also calls loadScript/loadStyle. Likely a Locker-era "
                f"proxy-escape shim. Under LWS this strips functions/dates/class "
                f"identity from the third-party library's input — review and remove.",
            ))

    return findings


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    files = list(iter_files(argv[1:]))
    if not files:
        print("No LWC source files found in the supplied paths.", file=sys.stderr)
        return 0

    all_findings: List[Tuple[str, str]] = []
    for path in files:
        all_findings.extend(analyse(path))

    if not all_findings:
        print(f"OK - scanned {len(files)} file(s); no Locker-only patterns found.")
        return 0

    p0 = [f for f in all_findings if f[0] == "P0"]
    p1 = [f for f in all_findings if f[0] == "P1"]
    p2 = [f for f in all_findings if f[0] == "P2"]

    for severity, message in all_findings:
        print(f"[{severity}] {message}")

    print("")
    print(
        f"Summary: {len(p0)} P0, {len(p1)} P1, {len(p2)} P2, "
        f"scanned {len(files)} file(s)."
    )

    if p0 or p1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
