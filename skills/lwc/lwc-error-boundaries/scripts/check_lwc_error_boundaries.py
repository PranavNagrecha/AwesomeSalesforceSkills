#!/usr/bin/env python3
"""check_lwc_error_boundaries.py — static checks on an LWC source tree for error-boundary
and error-handling defects.

Stdlib only. Points --manifest-dir at a directory containing LWC bundles (normally
force-app/main/default/lwc) and reports per-file findings.

Rules
-----
EB001  ERROR     errorCallback() swallows: no state assignment, no dispatch, no reporting
                 call, and no rethrow. Grounding: the framework already unmounts the
                 throwing subtree (lwc_guide create-lifecycle-hooks-error L4162, L4165), so
                 a body that records nothing removes the user's only signal without
                 removing the failure.
EB002  ERROR     `throw` inside errorCallback(). An unhandled error propagates to the parent
                 and then to the enclosing app, which shows the "A Component Error has
                 occurred!" modal (lwc_guide data-error-types L7732) -- the outcome the
                 boundary exists to prevent, and the unmount has already happened (L4165).
                 The guide states no rule about rethrow specifically; see the UNVERIFIED
                 note in references/llm-anti-patterns.md, Anti-Pattern 9.
EB003  WARN      error.body.message read without an Array.isArray(...body) guard anywhere in
                 the file. UI API READ operations return error.body as an ARRAY of objects
                 (lwc_guide data-error L6568); the other three shapes are objects
                 (L6569-L6571). The guide's own snippet branches on the shape (L6555-L6557).
EB004  WARN      A .catch(...) or a wire `error` branch whose only statement is console.log
                 / console.debug / console.info. Catching without recording or rendering
                 leaves the failure invisible; console.error at least reaches the browser
                 console the guide describes for unhandled async errors (L7733).
EB005  WARN      lightning/platformShowToastEvent imported in a bundle whose .js-meta.xml
                 lists lightningCommunity__Default. That module "isn't supported in
                 environments like LWR sites for Experience Cloud or standalone apps"
                 (lwc_guide base-components-patterns L4773, use-toast L10449, L10452).
                 lightning/toast is the preferred module (use-toast L10448).
EB006  ADVISORY  A toast dispatched with error.message where the same file also reads
                 error.body. A FetchResponse carries the useful text in body, not in a
                 top-level message (lwc_guide data-error L6545-L6551).
EB007  ADVISORY  A bundle that implements errorCallback but has no __tests__ directory.

Exit codes
----------
0  no ERROR findings (WARN and ADVISORY are reported but do not fail)
1  at least one ERROR finding, or --manifest-dir is missing / not a directory
   With --strict, WARN findings are promoted to ERROR and also exit 1.

An empty or bundle-free directory is a WARN, not a failure.

Usage
-----
    python3 check_lwc_error_boundaries.py --manifest-dir force-app/main/default/lwc
    python3 check_lwc_error_boundaries.py --manifest-dir path/to/lwc --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "{http://soap.sforce.com/2006/04/metadata}"

ERROR, WARN, ADVISORY = "ERROR", "WARN", "ADVISORY"

# --- helpers ---------------------------------------------------------------------------


def strip_js(src: str) -> str:
    """Blank out string literals, template literals and comments in one left-to-right pass,
    so an apostrophe in a comment cannot open a phantom string and a '//' inside a URL
    string cannot open a phantom comment. Newlines are preserved so line numbers survive."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch in "'\"`":
            quote = ch
            out.append(" ")
            i += 1
            while i < n and src[i] != quote:
                if src[i] == "\\":
                    i += 2
                    out.append(" ")
                    continue
                out.append("\n" if src[i] == "\n" else " ")
                i += 1
            i += 1
            out.append(" ")
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join("\n" if c == "\n" else " " for c in src[i:j]))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def block_after(code: str, start: int) -> tuple[str, int]:
    """Return the brace-balanced block that begins at the first '{' at or after `start`,
    plus the index just past it. Returns ("", start) when no block is found."""
    open_at = code.find("{", start)
    if open_at == -1:
        return "", start
    depth, i, n = 0, open_at, len(code)
    while i < n:
        if code[i] == "{":
            depth += 1
        elif code[i] == "}":
            depth -= 1
            if depth == 0:
                return code[open_at : i + 1], i + 1
        i += 1
    return code[open_at:], n


def line_of(code: str, index: int) -> int:
    return code.count("\n", 0, index) + 1


def find_child(elem, tag: str):
    """ElementTree leaf elements are falsy, so `a.find(x) or a.find(y)` is a trap.
    Always test `is not None`."""
    node = elem.find(f"{MDAPI_NS}{tag}")
    if node is None:
        node = elem.find(tag)
    return node


def meta_targets(meta_path: Path) -> set[str]:
    try:
        root = ET.parse(meta_path).getroot()
    except (ET.ParseError, OSError):
        return set()
    targets = set()
    holder = find_child(root, "targets")
    if holder is not None:
        for t in list(holder):
            if t.text:
                targets.add(t.text.strip())
    return targets


# --- rules -----------------------------------------------------------------------------

ERRCB_RE = re.compile(r"\berrorCallback\s*\(")
BODY_MESSAGE_RE = re.compile(r"\b[A-Za-z_$][\w$]*\s*(?:\?)?\.\s*body\s*(?:\?)?\.\s*message\b")
IS_ARRAY_BODY_RE = re.compile(r"Array\s*\.\s*isArray\s*\(\s*[A-Za-z_$][\w$]*\s*(?:\?)?\.\s*body")
CATCH_ARROW_RE = re.compile(r"\.catch\s*\(")
CATCH_KW_RE = re.compile(r"\bcatch\s*\([^)]*\)\s*\{")
WIRE_ERROR_RE = re.compile(r"\bif\s*\(\s*error\s*\)\s*\{")
CONSOLE_QUIET_RE = re.compile(r"\bconsole\s*\.\s*(log|debug|info)\s*\(")
STATE_WRITE_RE = re.compile(r"\bthis\s*\.\s*[\w$]+\s*(?:=|\+=|\.push\s*\()")
DISPATCH_RE = re.compile(r"\b(dispatchEvent|Toast\s*\.\s*show|ShowToastEvent)\b")
REPORT_CALL_RE = re.compile(
    r"(?<![\w$.])(?:this\s*\.\s*)?(log|report|track|record|capture|telemetry|notify)\w*\s*\(", re.I
)
THROW_RE = re.compile(r"\bthrow\b")
TOAST_RAW_MESSAGE_RE = re.compile(r"message\s*:\s*[A-Za-z_$][\w$]*\s*(?:\?)?\.\s*message\b")
PLATFORM_TOAST_RE = re.compile(r"from\s+['\"]lightning/platformShowToastEvent['\"]")


def check_bundle(bundle: Path) -> list[tuple[str, str, str, int, str]]:
    """Return (severity, rule, relative-file, line, message) findings for one bundle."""
    findings: list[tuple[str, str, str, int, str]] = []
    js_files = sorted(p for p in bundle.glob("*.js") if not p.name.endswith(".test.js"))
    if not js_files:
        return findings

    meta = bundle / f"{bundle.name}.js-meta.xml"
    targets = meta_targets(meta) if meta.exists() else set()
    has_tests = (bundle / "__tests__").is_dir()
    bundle_has_errcb = False

    for js in js_files:
        try:
            raw = js.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        code = strip_js(raw)
        rel = str(js)

        # --- EB005: platformShowToastEvent on an Experience Builder target -------------
        # Matched against the RAW source: strip_js blanks string literals, and the module
        # path we are looking for IS a string literal.
        m = PLATFORM_TOAST_RE.search(raw)
        if m and "lightningCommunity__Default" in targets:
            findings.append((
                WARN, "EB005", rel, line_of(raw, m.start()),
                "imports lightning/platformShowToastEvent but the bundle targets "
                "lightningCommunity__Default; that module is unsupported on LWR "
                "Experience Cloud sites (lwc_guide base-components-patterns L4773). "
                "Use lightning/toast.",
            ))

        # --- EB003: error.body.message without an Array.isArray(...body) guard ---------
        bm = BODY_MESSAGE_RE.search(code)
        if bm and not IS_ARRAY_BODY_RE.search(code):
            findings.append((
                WARN, "EB003", rel, line_of(code, bm.start()),
                "reads error.body.message with no Array.isArray(error.body) guard in the "
                "file; a UI API read returns error.body as an ARRAY "
                "(lwc_guide data-error L6568) and .message is undefined on it.",
            ))

        # --- EB006: toast built from a raw Error .message while body is available ------
        tm = TOAST_RAW_MESSAGE_RE.search(code)
        if tm and re.search(r"\.\s*body\b", code) and DISPATCH_RE.search(code):
            findings.append((
                ADVISORY, "EB006", rel, line_of(code, tm.start()),
                "toast message reads a raw .message while the file also reads .body; a "
                "FetchResponse carries the useful text in body "
                "(lwc_guide data-error L6545-L6551).",
            ))

        # --- EB001 / EB002: errorCallback body ----------------------------------------
        for m in ERRCB_RE.finditer(code):
            bundle_has_errcb = True
            body, _ = block_after(code, m.end())
            if not body:
                continue
            ln = line_of(code, m.start())
            if THROW_RE.search(body):
                findings.append((
                    ERROR, "EB002", rel, ln,
                    "errorCallback() rethrows; the error then reaches the enclosing app "
                    "and produces the component-error modal "
                    "(lwc_guide data-error-types L7732). Set state and report instead.",
                ))
            handled = (
                STATE_WRITE_RE.search(body)
                or DISPATCH_RE.search(body)
                or REPORT_CALL_RE.search(body)
                or THROW_RE.search(body)
            )
            if not handled:
                findings.append((
                    ERROR, "EB001", rel, ln,
                    "errorCallback() swallows the error: it sets no state, dispatches "
                    "nothing and reports nothing. The subtree is already unmounted "
                    "(lwc_guide create-lifecycle-hooks-error L4162), so this is a silent "
                    "failure.",
                ))

        # --- EB004: catch / wire-error branch whose only statement is a quiet console --
        for rx in (CATCH_ARROW_RE, CATCH_KW_RE, WIRE_ERROR_RE):
            for m in rx.finditer(code):
                body, _ = block_after(code, m.end() - 1)
                if not body:
                    continue
                inner = body[1:-1].strip()
                if not inner:
                    continue
                if CONSOLE_QUIET_RE.search(inner) and not (
                    STATE_WRITE_RE.search(inner)
                    or DISPATCH_RE.search(inner)
                    or REPORT_CALL_RE.search(inner)
                    or THROW_RE.search(inner)
                    or re.search(r"\bconsole\s*\.\s*error\s*\(", inner)
                ):
                    findings.append((
                        WARN, "EB004", rel, line_of(code, m.start()),
                        "error branch only console.log/debug/info's; nothing reaches the "
                        "user or telemetry. Set an error state or report it.",
                    ))

    if bundle_has_errcb and not has_tests:
        findings.append((
            ADVISORY, "EB007", str(bundle), 1,
            "bundle implements errorCallback but has no __tests__ directory; the guide's "
            "test layout is a __tests__ folder inside the bundle "
            "(lwc_guide unit-testing-using-jest-create-tests L12328).",
        ))
    return findings


def bundles_under(root: Path) -> list[Path]:
    """A bundle is a directory containing <dirname>.js."""
    found = []
    if (root / f"{root.name}.js").exists():
        found.append(root)
    for d in sorted(p for p in root.rglob("*") if p.is_dir()):
        if d.name == "__tests__":
            continue
        if (d / f"{d.name}.js").exists():
            found.append(d)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Static error-boundary checks over an LWC source tree.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--manifest-dir",
        required=True,
        help="directory holding LWC bundles, e.g. force-app/main/default/lwc",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="promote WARN findings to ERROR (ADVISORY still does not fail)",
    )
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR [lwc-error-boundaries] --manifest-dir not found: {root}", file=sys.stderr)
        return 1

    bundles = bundles_under(root)
    if not bundles:
        print(f"WARN  [lwc-error-boundaries] no LWC bundles found under {root}")
        return 0

    findings: list[tuple[str, str, str, int, str]] = []
    for b in bundles:
        findings.extend(check_bundle(b))

    order = {ERROR: 0, WARN: 1, ADVISORY: 2}
    findings.sort(key=lambda f: (order[f[0]], f[2], f[3]))

    for sev, rule, path, ln, msg in findings:
        effective = ERROR if (args.strict and sev == WARN) else sev
        print(f"{effective:<8} {rule} {path}:{ln}: {msg}")

    n_err = sum(1 for f in findings if f[0] == ERROR)
    n_warn = sum(1 for f in findings if f[0] == WARN)
    n_adv = sum(1 for f in findings if f[0] == ADVISORY)
    print(
        f"[lwc-error-boundaries] {len(bundles)} bundle(s); "
        f"{n_err} ERROR, {n_warn} WARN, {n_adv} ADVISORY"
    )
    if n_err or (args.strict and n_warn):
        return 1
    if not findings:
        print("OK    [lwc-error-boundaries] no findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
