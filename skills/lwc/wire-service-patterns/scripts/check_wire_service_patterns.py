#!/usr/bin/env python3
"""check_wire_service_patterns.py — static checks for LWC bundles that use @wire.

Reads a Salesforce source tree (``--manifest-dir``) and reports wire-service
defects that the LWC compiler does not catch. Stdlib only; no org connection.

Rules
-----
ERROR
  W001  ``@wire(apexMethod)`` where the imported Apex method's class is present
        in the tree and the method is not annotated ``cacheable=true``.
        "To use @wire to call an Apex method, you must set cacheable=true."
        (lwc_guide apex-result-caching L7256)
  W002  A wired result is mutated in place — ``this.x.data.push(...)`` or an
        assignment into a wired result field. Provisioned objects are read-only
        (lwc_guide data-wire-service-about L6401).

WARN
  W003  ``refreshApex(arg)`` where ``arg`` is not a property that holds a
        provisioned wire result. "The parameter you refresh with refreshApex()
        must be an object that was previously emitted by an Apex @wire."
        (lwc_guide apex-result-caching L7264)
  W004  Imperative DML (createRecord / updateRecord / deleteRecord, or a
        non-cacheable Apex import) with a @wire in the same file and no
        refreshApex / notifyRecordUpdateAvailable / refreshGraphQL call
        (lwc_guide data-guidelines L5354).
  W005  A wired FUNCTION that destructures or reads ``data`` but never ``error``
        (lwc_guide data-error L6544).
  W006  A ``$``-prefixed config value nested inside an array or object literal,
        which the platform treats as a literal string
        (lwc_guide data-wire-service-about L6443).
  W007  A reactive config property assigned inside ``renderedCallback`` — the
        documented infinite-loop shape (lwc_guide data-wire-service-about L6408).

ADVISORY
  W008  A ``@wire`` config passes a string literal for a parameter while the
        component declares an ``@api`` property of the same name — the reactive
        ``$prop`` form was probably intended.

Usage
-----
    python3 check_wire_service_patterns.py --manifest-dir force-app
    python3 check_wire_service_patterns.py --manifest-dir force-app --strict

Exit codes: 0 clean (or WARN/ADVISORY only), 1 on ERROR, on a missing
--manifest-dir, or on any WARN when --strict is passed. An empty tree is a WARN.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ERROR, WARN, ADVISORY = "ERROR", "WARN", "ADVISORY"

# ---------------------------------------------------------------- regexes

WIRE_BLOCK_RE = re.compile(r"@wire\s*\(", re.M)
APEX_IMPORT_RE = re.compile(
    r"^\s*import\s+(\w+)\s+from\s+['\"]@salesforce/apex/([\w.]+)['\"]", re.M
)
WIRE_TARGET_RE = re.compile(r"@wire\s*\(\s*(\w+)")
LDS_WRITE_RE = re.compile(r"\b(createRecord|updateRecord|deleteRecord)\s*\(")
REFRESH_RE = re.compile(r"\b(refreshApex|notifyRecordUpdateAvailable|refreshGraphQL)\s*\(")
REFRESH_APEX_ARG_RE = re.compile(r"refreshApex\s*\(\s*([^)]*?)\s*\)")
API_PROP_RE = re.compile(r"@api\s+(?:get\s+)?(\w+)")
NESTED_DOLLAR_RE = re.compile(r":\s*[\[{][^\]}]*(['\"]\$\w+['\"])")
APEX_METHOD_RE = re.compile(
    r"@AuraEnabled\s*(\([^)]*\))?\s*(?:public|global)\s+static\s+[\w<>,\[\].\s]+?\s+(\w+)\s*\(",
    re.I,
)



def _strip_js_comments(src: str) -> str:
    """Blank // and /* */ comments (newlines preserved) without touching string
    literals, so that a '//' inside a URL never opens a phantom comment and an
    example in a JSDoc block never registers as real code."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch in "'\"`":
            quote = ch
            out.append(ch)
            i += 1
            while i < n and src[i] != quote:
                if src[i] == "\\" and i + 1 < n:
                    out.append(src[i])
                    out.append(src[i + 1])
                    i += 2
                    continue
                out.append(src[i])
                i += 1
            if i < n:
                out.append(src[i])
                i += 1
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
            out.append("".join(c if c == "\n" else " " for c in src[i:j]))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _balanced_slice(text: str, open_idx: int) -> str:
    """Return the text from ``open_idx`` through the matching close paren."""
    depth, i, n = 0, open_idx, len(text)
    while i < n:
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_idx : i + 1]
        i += 1
    return text[open_idx:]


def _member_after(text: str, end_idx: int, limit: int = 400) -> str:
    """The snippet that follows a @wire(...) call — the property or function it decorates."""
    return text[end_idx : end_idx + limit]


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


# ------------------------------------------------------- Apex method index


def index_apex_methods(root: Path) -> dict[str, dict[str, bool]]:
    """{ClassName: {methodName: is_cacheable}} for every .cls in the tree."""
    index: dict[str, dict[str, bool]] = {}
    for cls in sorted(root.rglob("*.cls")):
        try:
            src = cls.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        methods: dict[str, bool] = {}
        for m in APEX_METHOD_RE.finditer(src):
            args = m.group(1) or ""
            methods[m.group(2)] = "cacheable" in args.lower() and "true" in args.lower()
        if methods:
            index[cls.stem] = methods
    return index


# ------------------------------------------------------------ file checks


def check_js(path: Path, text: str, apex_index: dict[str, dict[str, bool]]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    if "@wire" not in text:
        return findings
    text = _strip_js_comments(text)

    def add(sev: str, line: int, msg: str) -> None:
        findings.append((sev, f"{path}:{line}: {msg}"))

    # symbol -> (Class, method) for every Apex import in this file
    apex_imports = {m.group(1): m.group(2) for m in APEX_IMPORT_RE.finditer(text)}
    api_props = set(API_PROP_RE.findall(text))

    wired_props: set[str] = set()
    non_cacheable_wired: list[str] = []

    for m in WIRE_BLOCK_RE.finditer(text):
        call = _balanced_slice(text, m.end() - 1)
        end_idx = m.end() - 1 + len(call)
        line = _line_of(text, m.start())
        target_m = WIRE_TARGET_RE.match(text[m.start():])
        target = target_m.group(1) if target_m else ""
        tail = _member_after(text, end_idx)

        # the decorated member name: `foo;` (property) or `foo(result) {` (function)
        member_m = re.search(r"\s*(\w+)\s*(\(|;|=)", tail)
        member = member_m.group(1) if member_m else ""
        is_function = bool(member_m and member_m.group(2) == "(")
        if member:
            wired_props.add(member)

        # ---- W001 cacheable=true on the wired Apex method
        if target in apex_imports:
            qualified = apex_imports[target]
            parts = qualified.split(".")
            cls_name, method = (parts[-2], parts[-1]) if len(parts) >= 2 else ("", parts[-1])
            known = apex_index.get(cls_name)
            if known is not None and method in known and not known[method]:
                add(
                    ERROR,
                    line,
                    f"@wire({target}) targets {cls_name}.{method}, which is not "
                    f"@AuraEnabled(cacheable=true); a wired Apex method must be cacheable "
                    f"(lwc_guide apex-result-caching L7256)",
                )
                non_cacheable_wired.append(target)

        # ---- W006 nested $ inside an array/object literal
        for nested in NESTED_DOLLAR_RE.finditer(call):
            add(
                WARN,
                line,
                f"reactive value {nested.group(1)} is nested inside a collection in "
                f"the @wire config; a nested $ is passed as a literal string, not a reactive "
                f"reference (lwc_guide data-wire-service-about L6443)",
            )

        # ---- W008 string literal where a matching @api prop exists
        for key, value in re.findall(r"(\w+)\s*:\s*'([^'$][^']*)'", call):
            if key in api_props:
                add(
                    ADVISORY,
                    line,
                    f"@wire config passes the literal '{value}' for `{key}` while the class "
                    f"declares `@api {key}`; '$'+'{key}' was probably intended",
                )

        # ---- W005 wired function that handles data but never error
        if is_function:
            body_start = text.find("{", end_idx)
            if body_start != -1:
                depth, i, n = 0, body_start, len(text)
                while i < n:
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    i += 1
                body = text[body_start : i + 1]
                header = text[end_idx:body_start]
                scope = header + body
                # A wired function may hand the provisioned object to a field
                # (`this.wiredXResult = result`). That field is then a legal
                # refreshApex() argument, so treat it as provisioned too.
                param_m = re.match(r"\s*\w+\s*\(\s*(?:\{[^}]*\}|(\w+))", header)
                param = param_m.group(1) if param_m and param_m.group(1) else None
                if param:
                    for hold in re.findall(
                        rf"this\.(\w+)\s*=\s*{re.escape(param)}\s*[;,)]", body
                    ):
                        wired_props.add(hold)
                if re.search(r"\bdata\b", scope) and not re.search(r"\berror\b", scope):
                    add(
                        WARN,
                        line,
                        f"wired function `{member}` reads `data` but never `error`; both are "
                        f"hardcoded properties of every wire result "
                        f"(lwc_guide data-error L6544)",
                    )

    # ---- W002 in-place mutation of a wired result
    for m in re.finditer(
        r"this\.(\w+)\.data(?:\.[\w.\[\]]+)?\s*(?:=[^=]|\.(?:push|pop|shift|unshift|splice|sort|reverse)\s*\()",
        text,
    ):
        if m.group(1) in wired_props:
            add(
                ERROR,
                _line_of(text, m.start()),
                f"`this.{m.group(1)}.data` is mutated in place; provisioned objects are "
                f"read-only — shallow-copy before transforming "
                f"(lwc_guide data-wire-service-about L6401)",
            )

    # ---- W003 refreshApex on something that is not a provisioned wire result
    for m in REFRESH_APEX_ARG_RE.finditer(text):
        arg = m.group(1).strip()
        prop = arg[5:] if arg.startswith("this.") else arg
        base = prop.split(".")[0]
        if "." in prop or base not in wired_props:
            add(
                WARN,
                _line_of(text, m.start()),
                f"refreshApex({arg}) does not receive a bare @wire-provisioned result; the "
                f"argument must be the object emitted by an Apex @wire, not its `.data` "
                f"(lwc_guide apex-result-caching L7264)",
            )

    # ---- W004 imperative write with a wire present and no refresh
    non_cacheable_calls = [
        sym
        for sym in apex_imports
        if re.search(rf"(?<![\w.]){re.escape(sym)}\s*\(\s*\{{", text)
        and sym not in [t for t in re.findall(r"@wire\s*\(\s*(\w+)", text)]
    ]
    writes = LDS_WRITE_RE.search(text) or non_cacheable_calls
    if writes and not REFRESH_RE.search(text):
        what = "an LDS write" if LDS_WRITE_RE.search(text) else "imperative Apex"
        add(
            WARN,
            _line_of(text, LDS_WRITE_RE.search(text).start()) if LDS_WRITE_RE.search(text) else 1,
            f"component performs {what} and holds a @wire, but never calls refreshApex(), "
            f"notifyRecordUpdateAvailable(), or refreshGraphQL(); Apex data is not managed "
            f"by LDS and must be refreshed explicitly (lwc_guide data-guidelines L5354)",
        )

    # ---- W007 reactive config property assigned in renderedCallback
    reactive = set(re.findall(r"['\"]\$(\w+)['\"]", text))
    rc = re.search(r"renderedCallback\s*\([^)]*\)\s*\{", text)
    if rc and reactive:
        depth, i, n = 0, rc.end() - 1, len(text)
        while i < n:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = text[rc.end() - 1 : i + 1]
        for prop in sorted(reactive):
            if re.search(rf"this\.{re.escape(prop)}\s*=[^=]", body):
                add(
                    WARN,
                    _line_of(text, rc.start()),
                    f"reactive wire config property `{prop}` is assigned inside "
                    f"renderedCallback(); this is the documented infinite-loop shape "
                    f"(lwc_guide data-wire-service-about L6408)",
                )

    return findings


# ------------------------------------------------------------------- main


def run(manifest_dir: Path) -> tuple[list[tuple[str, str]], int]:
    apex_index = index_apex_methods(manifest_dir)
    findings: list[tuple[str, str]] = []
    scanned = 0
    for js in sorted(manifest_dir.rglob("*.js")):
        parts = set(js.parts)
        if "node_modules" in parts or "__tests__" in parts:
            continue
        try:
            text = js.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        scanned += 1
        findings.extend(check_js(js, text, apex_index))
    return findings, scanned


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest-dir", default=".", help="Root of the Salesforce source tree.")
    ap.add_argument("--strict", action="store_true", help="Promote WARN to a failing exit code.")
    args = ap.parse_args()

    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        return 1

    findings, scanned = run(manifest_dir)
    if scanned == 0:
        print(f"WARN: no .js files found under {manifest_dir} — nothing to check.")
        return 1 if args.strict else 0

    for sev in (ERROR, WARN, ADVISORY):
        for level, msg in findings:
            if level == sev:
                print(f"{sev}: {msg}")

    errors = sum(1 for level, _ in findings if level == ERROR)
    warns = sum(1 for level, _ in findings if level == WARN)
    advisories = len(findings) - errors - warns
    print(
        f"\n{scanned} JavaScript file(s) scanned — "
        f"{errors} ERROR, {warns} WARN, {advisories} ADVISORY."
    )
    if errors:
        return 1
    if args.strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
