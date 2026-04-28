#!/usr/bin/env python3
"""
check_lwc_public_api_hardening.py

Static checker for the LWC public-API hardening pattern documented in this
skill. Scans an LWC bundle directory (or a single `.js` file) for signals
that the public surface is fragile:

  P0  Class declares an `@api` setter that mutates a backing field in place
      (`.length = 0`, `.splice(0)`, `Object.assign(this._x, ...)`).
      Action: reassign the backing field instead.

  P0  Class extends `LightningElement` and contains an `@api` method whose
      name strongly suggests it should be a CustomEvent
      (refresh / update / notify / forceX / setX).
      Action: dispatch a CustomEvent in the other direction.

  P1  `@api` boolean-shaped property declared as a bare field with no setter
      (heuristic: name starts with `is`, `has`, `disabled`, `enabled`,
      `required`, `readonly`, `visible`, `loading`).
      Action: add a setter that coerces string `"true"`/`"false"`.

  P1  Class declares `@api recordId;` (or any property named recordId/Id-like)
      with no defensive `connectedCallback` guard and no setter.
      Action: validate in `connectedCallback` or coerce in a setter.

  P1  `connectedCallback` is missing entirely from a class that declares
      `@api` properties (not necessarily required, but flag for review).

  P0  Design property block in `.js-meta.xml` uses `propertyType` outside
      a `<lightning__FlowScreen>` `<targetConfig>`.
      Action: `propertyType` is Flow-only.

  P1  Design property block declares `name="<kebab-case>"` (contains `-`).
      Action: design property names must be camelCase.

stdlib only. Exits 1 on any P0 or P1 finding, 0 otherwise.

Usage:
    python3 check_lwc_public_api_hardening.py <path> [<path> ...]

Each <path> may be a `.js` file, a `.js-meta.xml` file, or a directory
(recursively scanned for both file types).
"""

from __future__ import annotations

import os
import re
import sys
from typing import Iterable, List, Tuple

# ---------------------------------------------------------------------------
# JS-side regexes
# ---------------------------------------------------------------------------

CLASS_DECL_RE = re.compile(r"\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+extends\s+LightningElement\b")
API_BARE_FIELD_RE = re.compile(
    r"@api\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:=\s*[^;\n]+)?\s*;"
)
API_GETTER_RE = re.compile(r"@api\s*\n?\s*get\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
API_SETTER_RE = re.compile(r"\bset\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
API_METHOD_RE = re.compile(
    r"@api\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*\{"
)
CONNECTED_CALLBACK_RE = re.compile(r"\bconnectedCallback\s*\(\s*\)\s*\{")

# Setter body in-place mutation hints (looked up only inside @api setter bodies).
INPLACE_PATTERNS = [
    re.compile(r"\.length\s*=\s*0\b"),
    re.compile(r"\.splice\s*\(\s*0\b"),
    re.compile(r"Object\.assign\s*\(\s*this\."),
    re.compile(r"\.push\s*\(\s*\.\.\."),  # rebuild-via-push pattern
]

# Method names that are almost always better as CustomEvents.
SUSPECT_METHOD_NAMES = {
    "refresh",
    "update",
    "notify",
    "reload",
    "rebuild",
    "broadcast",
    "emit",
    "trigger",
    "save",
    "submit",
    "cancel",
    "fire",
    "publish",
}

# Boolean-shaped property name prefixes/exact names.
BOOLEAN_NAMES = {
    "disabled", "enabled", "required", "readonly", "visible",
    "hidden", "loading", "open", "closed", "active", "selected",
}
BOOLEAN_PREFIXES = ("is", "has", "should", "can")

# Id-shaped property names that almost always need defensive handling.
ID_LIKE_NAMES = {"recordId", "objectApiName", "topicId", "userId", "accountId"}

# ---------------------------------------------------------------------------
# js-meta.xml regexes
# ---------------------------------------------------------------------------

TARGETCONFIG_BLOCK_RE = re.compile(
    r"<targetConfig\b[^>]*targets\s*=\s*\"([^\"]+)\"[^>]*>(.*?)</targetConfig>",
    re.DOTALL | re.IGNORECASE,
)
PROPERTY_RE = re.compile(
    r"<property\b([^/>]*?)(?:/>|>.*?</property>)",
    re.DOTALL | re.IGNORECASE,
)
PROPERTYTYPE_RE = re.compile(
    r"<propertyType\b",
    re.IGNORECASE,
)
PROPERTY_NAME_ATTR_RE = re.compile(r"\bname\s*=\s*\"([^\"]+)\"")


# ---------------------------------------------------------------------------
# File walking
# ---------------------------------------------------------------------------

def iter_target_files(paths: Iterable[str]) -> Iterable[str]:
    for raw in paths:
        if os.path.isfile(raw) and (raw.endswith(".js") or raw.endswith(".js-meta.xml")):
            yield raw
        elif os.path.isdir(raw):
            for root, _dirs, files in os.walk(raw):
                # Skip __tests__ and node_modules to avoid noise from test scaffolding.
                if "__tests__" in root or "node_modules" in root:
                    continue
                for name in files:
                    if name.endswith(".js") or name.endswith(".js-meta.xml"):
                        yield os.path.join(root, name)
        else:
            print(f"WARN: skipping non-LWC or missing path: {raw}", file=sys.stderr)


# ---------------------------------------------------------------------------
# JS file analysis
# ---------------------------------------------------------------------------

def _setter_bodies(text: str) -> List[Tuple[str, str]]:
    """Return list of (setter_name, setter_body_text) for each `set name(...) { ... }`.

    Brace-matched extraction (tolerates nested objects in the body).
    """
    results: List[Tuple[str, str]] = []
    for match in API_SETTER_RE.finditer(text):
        name = match.group(1)
        # Find the opening `{` after the parameter list.
        open_idx = text.find("{", match.end())
        if open_idx < 0:
            continue
        depth = 0
        i = open_idx
        while i < len(text):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    body = text[open_idx + 1: i]
                    results.append((name, body))
                    break
            i += 1
    return results


def analyse_js(path: str) -> List[Tuple[str, str]]:
    findings: List[Tuple[str, str]] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [("P0", f"{path}: could not read file ({exc})")]

    if not CLASS_DECL_RE.search(text):
        # Not an LWC main file (could be a helper module). Skip silently.
        return findings

    bare_fields = {m.group(1) for m in API_BARE_FIELD_RE.finditer(text)}
    getters = {m.group(1) for m in API_GETTER_RE.finditer(text)}
    api_methods = [m.group(1) for m in API_METHOD_RE.finditer(text)]
    has_connected_callback = bool(CONNECTED_CALLBACK_RE.search(text))

    # P0 — @api setter that mutates a backing field in place
    for name, body in _setter_bodies(text):
        if name not in getters:
            # Only flag setters paired with an @api getter. Bare `set foo(...)`
            # without a corresponding `@api get foo()` is private code.
            continue
        for pat in INPLACE_PATTERNS:
            if pat.search(body):
                findings.append((
                    "P0",
                    f"{path}: @api setter for `{name}` mutates the backing field in place "
                    f"(matched `{pat.pattern}`). Reassign the backing field instead so LWC "
                    f"reactivity fires a re-render.",
                ))
                break

    # P0 — @api method whose name suggests a CustomEvent would be better
    for name in api_methods:
        if name.lower() in SUSPECT_METHOD_NAMES:
            findings.append((
                "P0",
                f"{path}: @api method `{name}()` looks like it should be a CustomEvent. "
                f"Imperative methods couple parent to child internals and break under "
                f"async DOM removal. Consider dispatching `CustomEvent('{name.lower()}')` "
                f"from the child instead and listening from the parent.",
            ))

    # P1 — boolean-shaped @api property as a bare field with no setter
    for name in bare_fields:
        is_boolean_named = (
            name.lower() in BOOLEAN_NAMES
            or any(name.startswith(prefix) and len(name) > len(prefix) and name[len(prefix)].isupper()
                   for prefix in BOOLEAN_PREFIXES)
        )
        if is_boolean_named:
            findings.append((
                "P1",
                f"{path}: @api boolean-shaped property `{name}` declared as a bare field "
                f"with no setter. HTML attribute parsing produces strings, so "
                f"`<c-foo {_kebab(name)}=\"false\">` results in a truthy value. "
                f"Add a setter that coerces with `v === true || v === 'true'`.",
            ))

    # P1 — id-shaped property with neither setter nor connectedCallback guard
    for name in bare_fields:
        if name in ID_LIKE_NAMES and name not in getters:
            if not has_connected_callback:
                findings.append((
                    "P1",
                    f"{path}: @api `{name}` declared with no setter and no "
                    f"`connectedCallback` guard. Id-shaped properties almost always need "
                    f"either a setter that validates the string shape or a guard in "
                    f"`connectedCallback` that fails fast when missing.",
                ))

    # P1 — class declares @api properties but has no connectedCallback at all
    has_any_api = bool(bare_fields or getters)
    if has_any_api and not has_connected_callback:
        findings.append((
            "P1",
            f"{path}: class extends LightningElement and declares @api properties "
            f"but has no `connectedCallback`. Add one (even an empty one is a "
            f"signal for future hardening) and use it to validate any required "
            f"public inputs.",
        ))

    return findings


def _kebab(camel: str) -> str:
    """Convert camelCase to kebab-case for diagnostic strings."""
    out = []
    for i, ch in enumerate(camel):
        if ch.isupper() and i > 0:
            out.append("-")
        out.append(ch.lower())
    return "".join(out)


# ---------------------------------------------------------------------------
# js-meta.xml analysis
# ---------------------------------------------------------------------------

def analyse_meta_xml(path: str) -> List[Tuple[str, str]]:
    findings: List[Tuple[str, str]] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [("P0", f"{path}: could not read file ({exc})")]

    for block_match in TARGETCONFIG_BLOCK_RE.finditer(text):
        targets_attr = block_match.group(1)
        block_body = block_match.group(2)

        # P0 — propertyType outside lightning__FlowScreen
        if PROPERTYTYPE_RE.search(block_body):
            if "lightning__FlowScreen" not in targets_attr:
                findings.append((
                    "P0",
                    f"{path}: `<propertyType>` declared inside a non-Flow targetConfig "
                    f"(targets=\"{targets_attr}\"). `propertyType` is Flow-only; remove "
                    f"or move to a `<lightning__FlowScreen>` targetConfig.",
                ))

        # P1 — kebab-case in <property name="...">
        for prop_match in PROPERTY_RE.finditer(block_body):
            attrs = prop_match.group(1)
            name_match = PROPERTY_NAME_ATTR_RE.search(attrs)
            if name_match:
                name = name_match.group(1)
                if "-" in name:
                    findings.append((
                        "P1",
                        f"{path}: `<property name=\"{name}\">` uses kebab-case. Design "
                        f"property names must be camelCase to match the JS @api property; "
                        f"only HTML markup uses kebab-case.",
                    ))

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def analyse(path: str) -> List[Tuple[str, str]]:
    if path.endswith(".js"):
        return analyse_js(path)
    if path.endswith(".js-meta.xml"):
        return analyse_meta_xml(path)
    return []


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    files = list(iter_target_files(argv[1:]))
    if not files:
        print("No .js or .js-meta.xml files found in the supplied paths.", file=sys.stderr)
        return 0

    all_findings: List[Tuple[str, str]] = []
    for path in files:
        all_findings.extend(analyse(path))

    if not all_findings:
        print(f"OK - scanned {len(files)} file(s); no public-API hardening violations found.")
        return 0

    p0 = [f for f in all_findings if f[0] == "P0"]
    p1 = [f for f in all_findings if f[0] == "P1"]

    for severity, message in all_findings:
        print(f"[{severity}] {message}")

    print("")
    print(f"Summary: {len(p0)} P0, {len(p1)} P1, scanned {len(files)} file(s).")

    if p0 or p1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
