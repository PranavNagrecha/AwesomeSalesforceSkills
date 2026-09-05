#!/usr/bin/env python3
"""check_lwc_lifecycle.py — static audit of LWC lifecycle-hook usage.

Scans the .js files of one or more Lightning Web Component bundles and reports
lifecycle contract violations. Every rule maps to a statement in the Lightning
Web Components Developer Guide; the guide page id is printed with each finding
so a reviewer can check the claim rather than trust the checker.

Rules
-----
  L1  ERROR     DOM access inside constructor()            (create-lifecycle-hooks-created)
  L2  ERROR     super() is not the first statement          (create-lifecycle-hooks-created)
  L3  WARN      asynchronous work inside constructor()      (create-lifecycle-hooks-created / -dom)
  L4  WARN      reactive assignment in renderedCallback()   (create-lifecycle-hooks-rendered)
                with no early-return guard
  L5  WARN      setup in connectedCallback() with no        (create-lifecycle-hooks-dom /
                matching teardown in disconnectedCallback()  events-handling)
  L6  ADVISORY  disconnectedCallback() present but empty    (create-lifecycle-hooks-dom)
  L7  WARN      lifecycle hook declared async               (create-lifecycle-hooks-dom)
  L8  WARN      document.* DOM query in component JS        (js-third-party-library)

Exit codes
----------
  0  no ERROR findings (WARN and ADVISORY do not fail the run)
  1  at least one ERROR, or --manifest-dir does not exist
  With --strict, every WARN is promoted to ERROR (ADVISORY is never promoted).

Usage
-----
    python3 check_lwc_lifecycle.py --manifest-dir force-app/main/default/lwc
    python3 check_lwc_lifecycle.py --manifest-dir force-app/main/default/lwc --strict
    python3 check_lwc_lifecycle.py --manifest-dir force-app --json

Stdlib only. This is a text-level audit: it does not parse JavaScript and it
never claims a bundle compiles or deploys.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HOOKS = ("constructor", "connectedCallback", "renderedCallback", "disconnectedCallback", "errorCallback", "render")

# setup call in connectedCallback -> teardown call expected in disconnectedCallback
TEARDOWN_PAIRS = {
    "addEventListener": "removeEventListener",
    "setInterval": "clearInterval",
    "setTimeout": "clearTimeout",
    "subscribe": "unsubscribe",
    "registerRefreshHandler": "unregisterRefreshHandler",
}

DOM_IN_CONSTRUCTOR = (
    "this.template",
    "this.refs",
    "this.querySelector",
    "this.hostElement",
    "this.appendChild",
    "this.setAttribute",
    "document.",
)

ASYNC_IN_CONSTRUCTOR = ("await ", ".then(", "setTimeout(", "setInterval(", "fetch(", "Promise.")

# `if (this.hasRendered) return;` / `if (!this._init) { return; }` and friends
GUARD_RE = re.compile(r"if\s*\((?:[^()]|\([^()]*\))*\)\s*\{?\s*(?:\n\s*)?return\b")
ASSIGN_RE = re.compile(r"this\.([A-Za-z_$][\w$]*)\s*=(?!=)")
DOC_QUERY_RE = re.compile(r"\bdocument\.(querySelector|querySelectorAll|getElementById|getElementsBy\w+)\s*\(")
SKIP_FILES = {"jest.config.js", "jest.setup.js", "babel.config.js"}


def mask(src: str) -> str:
    """Blank the *contents* of strings, template literals and comments, preserving
    length and every character position, so brace matching and identifier searches
    never trip over a `{` inside a string or a hook name inside a comment."""
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch in "'\"`":
            quote = ch
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == quote:
                    break
                if src[j] != "\n":
                    out[j] = " "
                j += 1
            i = j + 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if src[k] != "\n":
                    out[k] = " "
            i = j
            continue
        i += 1
    return "".join(out)


def find_hook(masked: str, name: str) -> tuple[int, int, bool] | None:
    """Return (body_start, body_end, is_async) for a class method `name`, or None.

    body_start/body_end bracket the text *inside* the outermost braces.
    """
    for m in re.finditer(r"(^|\n)([ \t]*)(async\s+)?" + re.escape(name) + r"\s*\(", masked):
        is_async = bool(m.group(3))
        # walk to the closing paren of the parameter list
        depth, i = 0, m.end() - 1
        while i < len(masked):
            if masked[i] == "(":
                depth += 1
            elif masked[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        brace = masked.find("{", i)
        if brace < 0:
            continue
        depth, j = 0, brace
        while j < len(masked):
            if masked[j] == "{":
                depth += 1
            elif masked[j] == "}":
                depth -= 1
                if depth == 0:
                    return brace + 1, j, is_async
            j += 1
    return None


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def audit_file(path: Path, rel: str) -> list[dict]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if "extends" not in raw and "LightningElement" not in raw:
        return []
    masked = mask(raw)
    findings: list[dict] = []

    def add(severity: str, rule: str, index: int, message: str, page: str) -> None:
        findings.append(
            {
                "severity": severity,
                "rule": rule,
                "file": rel,
                "line": line_of(raw, index),
                "message": message,
                "guide_page": page,
            }
        )

    bodies: dict[str, tuple[str, int, bool]] = {}
    for hook in HOOKS:
        found = find_hook(masked, hook)
        if found:
            start, end, is_async = found
            bodies[hook] = (masked[start:end], start, is_async)

    # L1 / L2 / L3 — constructor
    if "constructor" in bodies:
        body, start, is_async = bodies["constructor"]
        for token in DOM_IN_CONSTRUCTOR:
            pos = body.find(token)
            if pos >= 0:
                add(
                    "ERROR",
                    "L1",
                    start + pos,
                    f"`{token}` in constructor(): the element's children and attributes do not "
                    "exist yet and querySelector returns nothing. Move it to connectedCallback() "
                    "(environment work) or renderedCallback() (DOM work).",
                    "create-lifecycle-hooks-created",
                )
                break
        stripped = body.strip()
        if stripped and not stripped.startswith("super("):
            add(
                "ERROR",
                "L2",
                start,
                "super() is not the first statement in constructor(). The custom-elements spec "
                "requires `super()` with no parameters before anything touches `this`.",
                "create-lifecycle-hooks-created",
            )
        if is_async or any(token in body for token in ASYNC_IN_CONSTRUCTOR):
            add(
                "WARN",
                "L3",
                start,
                "asynchronous work in constructor(): public properties are assigned after "
                "construction and before connectedCallback(), so anything awaited here reads "
                "undefined inputs. Call an async method from connectedCallback() instead.",
                "create-lifecycle-hooks-created",
            )

    # L4 — renderedCallback reactive assignment without a guard
    if "renderedCallback" in bodies:
        body, start, _ = bodies["renderedCallback"]
        assigns = [m for m in ASSIGN_RE.finditer(body)]
        if assigns and not GUARD_RE.search(body):
            names = sorted({m.group(1) for m in assigns})
            add(
                "WARN",
                "L4",
                start + assigns[0].start(),
                "renderedCallback() assigns to "
                + ", ".join(f"this.{n}" for n in names[:4])
                + " with no early-return guard. Fields are reactive, so the assignment marks the "
                "component dirty and renderedCallback() runs again — the documented infinite-loop "
                "shape. Add `if (this.hasRendered) return;` and set the flag.",
                "create-lifecycle-hooks-rendered",
            )

    # L5 — setup without teardown
    if "connectedCallback" in bodies:
        body, start, _ = bodies["connectedCallback"]
        teardown = bodies.get("disconnectedCallback", ("", 0, False))[0]
        whole_file_teardown = masked  # a teardown helper may live outside the hook
        for setup, undo in TEARDOWN_PAIRS.items():
            pos = body.find(setup + "(")
            if pos < 0:
                continue
            if "disconnectedCallback" not in bodies:
                add(
                    "WARN",
                    "L5",
                    start + pos,
                    f"`{setup}(` in connectedCallback() and no disconnectedCallback() at all. "
                    f"Add one that calls `{undo}(`.",
                    "create-lifecycle-hooks-dom",
                )
                continue
            calls_undo = undo + "(" in teardown or (
                re.search(r"this\.\w+\s*\(", teardown) and undo + "(" in whole_file_teardown
            )
            if not calls_undo:
                add(
                    "WARN",
                    "L5",
                    start + pos,
                    f"`{setup}(` in connectedCallback() with no `{undo}(` reachable from "
                    "disconnectedCallback(). connectedCallback() can fire more than once, so each "
                    "re-insertion adds another listener, timer, or subscription.",
                    "create-lifecycle-hooks-dom",
                )

    # L6 — empty disconnectedCallback
    if "disconnectedCallback" in bodies:
        body, start, _ = bodies["disconnectedCallback"]
        if not body.strip():
            add(
                "ADVISORY",
                "L6",
                start,
                "disconnectedCallback() is empty. Either remove it or move the teardown for "
                "everything connectedCallback() set up into it.",
                "create-lifecycle-hooks-dom",
            )

    # L7 — async lifecycle hook
    for hook in ("connectedCallback", "disconnectedCallback", "renderedCallback", "errorCallback"):
        if hook in bodies and bodies[hook][2]:
            add(
                "WARN",
                "L7",
                bodies[hook][1],
                f"`async {hook}()`: lifecycle hooks are synchronous and the framework does not "
                "await a returned promise, so code after the first await runs at an unpredictable "
                "point relative to rendering and to parent/child hooks. Call a separate async "
                "method from the synchronous hook.",
                "create-lifecycle-hooks-dom",
            )

    # L8 — document.* query
    for m in DOC_QUERY_RE.finditer(masked):
        add(
            "WARN",
            "L8",
            m.start(),
            f"`document.{m.group(1)}` in component JavaScript. Query the component's own tree with "
            "this.template (shadow DOM), this (light DOM), or this.refs.",
            "js-third-party-library",
        )

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest-dir", required=True, help="directory holding the LWC bundles to scan")
    ap.add_argument("--strict", action="store_true", help="promote every WARN to ERROR")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR --manifest-dir not found: {root}", file=sys.stderr)
        return 1

    files = sorted(
        p
        for p in root.rglob("*.js")
        if p.name not in SKIP_FILES and "__tests__" not in p.parts and "node_modules" not in p.parts
    )
    if not files:
        print(f"WARN no LWC .js files under {root} — nothing to check")
        return 0

    findings: list[dict] = []
    for path in files:
        try:
            rel = str(path.relative_to(root))
        except ValueError:  # pragma: no cover - defensive
            rel = str(path)
        findings.extend(audit_file(path, rel))

    if args.strict:
        for f in findings:
            if f["severity"] == "WARN":
                f["severity"] = "ERROR"

    errors = sum(1 for f in findings if f["severity"] == "ERROR")
    warns = sum(1 for f in findings if f["severity"] == "WARN")
    advisories = sum(1 for f in findings if f["severity"] == "ADVISORY")

    if args.json:
        print(
            json.dumps(
                {
                    "manifest_dir": str(root),
                    "files_scanned": len(files),
                    "errors": errors,
                    "warnings": warns,
                    "advisories": advisories,
                    "findings": findings,
                },
                indent=2,
            )
        )
    else:
        order = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}
        for f in sorted(findings, key=lambda x: (order[x["severity"]], x["file"], x["line"])):
            print(f"{f['severity']} [{f['rule']}] {f['file']}:{f['line']}: {f['message']} "
                  f"(guide: {f['guide_page']})")
        print(
            f"\nScanned {len(files)} file(s) under {root}: "
            f"{errors} error(s), {warns} warning(s), {advisories} advisory(ies)."
        )

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
