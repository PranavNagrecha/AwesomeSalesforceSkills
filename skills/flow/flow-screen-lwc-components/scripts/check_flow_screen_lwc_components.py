#!/usr/bin/env python3
"""Checker for Flow screen LWC bundles (lightning__FlowScreen).

Scans ``*.js-meta.xml`` and the sibling ``.js`` files under ``--manifest-dir``.
Stdlib only.

Rules (each premise is documented in the LWC guide, cited as lwcguide <slug>;
Metadata API guide cited as api_meta 264 L<n>):

  ERROR  js-meta.xml is not well-formed XML.
  ERROR  ``validate`` declared as an arrow-function property
         (lwcguide use-flow-validate-user-input-for-custom-components:
         "Arrow function expressions don't work for validation").
  WARN   FlowScreen bundle with isExposed not true (api_meta 264 L86762-86765).
  WARN   <property> without a type, or with a type outside the documented list
         (lwcguide targets-lightning-flow-screen): Boolean, Integer, String,
         Double, Date, DateTime, apex://..., @salesforce/schema/..., {Generic};
         a trailing [] marks a collection.
  WARN   outputOnly property with no FlowAttributeChangeEvent naming it in
         the bundle's JS (lwcguide use-best-practices-reactivity).
  WARN   FlowNavigation*Event dispatched inside connectedCallback or
         renderedCallback (lwcguide use-flow-screen-navigate).
  WARN   FlowAttributeChangeEvent and a FlowNavigation*Event dispatched in the
         same method (lwcguide use-flow-screen-navigate: race conditions).
  WARN   ``async validate`` (the guide documents only the plain method).

Exit codes: ERROR findings exit 1 always; WARN findings exit 0 unless
``--strict``; an empty directory prints one WARN and exits 0; a missing
directory is an ERROR and exits 1.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TYPE_RE = re.compile(
    r"^(Boolean|Integer|String|Double|Date|DateTime)(\[\])?$"
    r"|^apex://[\w.]+(\[\])?$|^@salesforce/schema/[\w.]+(\[\])?$|^\{\w+(\[\])?\}$"
)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def descend(root: ET.Element, name: str) -> list[ET.Element]:
    return [e for e in root.iter() if local(e.tag) == name]


def method_body(src: str, name: str) -> str | None:
    """Return the brace-balanced body of method ``name`` or None."""
    m = re.search(r"(?m)^\s*(?:async\s+)?(?:get\s+|set\s+)?" + re.escape(name) + r"\s*\([^)]*\)\s*\{", src)
    if not m:
        return None
    depth, i = 1, m.end()
    while i < len(src) and depth:
        depth += {"{": 1, "}": -1}.get(src[i], 0)
        i += 1
    return src[m.end():i]


def check_bundle(meta: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    try:
        root = ET.parse(meta).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"{meta}: not well-formed XML ({exc})")]
    targets = [(t.text or "").strip() for t in descend(root, "target")]
    if "lightning__FlowScreen" not in targets:
        return out
    exposed = descend(root, "isExposed")
    if not exposed or (exposed[0].text or "").strip().lower() != "true":
        out.append(("WARN", f"{meta}: lightning__FlowScreen bundle without <isExposed>true</isExposed>; builders will not list it"))
    outputs = []
    for cfg in descend(root, "targetConfig"):
        if "lightning__FlowScreen" not in (cfg.get("targets") or ""):
            continue
        for prop in descend(cfg, "property"):
            name, ptype = prop.get("name") or "?", (prop.get("type") or "").strip()
            if not ptype:
                out.append(("WARN", f"{meta}: property '{name}' has no type (type is required)"))
            elif not TYPE_RE.match(ptype):
                out.append(("WARN", f"{meta}: property '{name}' type '{ptype}' is not one of the documented types"))
            if prop.get("role") == "outputOnly":
                outputs.append(name)
    js_files = sorted(meta.parent.glob("*.js"))
    src = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in js_files)
    for name in outputs:
        if not re.search(r"FlowAttributeChangeEvent\(\s*['\"]" + re.escape(name) + r"['\"]", src):
            out.append(("WARN", f"{meta}: outputOnly property '{name}' has no FlowAttributeChangeEvent dispatch in the bundle JS"))
    if re.search(r"(?m)^\s*(?:@api\s+)?validate\s*=\s*(?:async\s*)?\(", src):
        out.append(("ERROR", f"{meta.parent}: validate declared as an arrow function; the LWC guide says it does not work for lightning__FlowScreen"))
    if re.search(r"async\s+validate\s*\(", src):
        out.append(("WARN", f"{meta.parent}: async validate(); the guide documents only a plain method returning {{ isValid, errorMessage }}"))
    for hook in ("connectedCallback", "renderedCallback"):
        body = method_body(src, hook)
        if body and re.search(r"FlowNavigation\w+Event", body):
            out.append(("WARN", f"{meta.parent}: FlowNavigation event dispatched inside {hook}; fire navigation only from event handlers"))
    for m in re.finditer(r"(?m)^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{", src):
        if m.group(1) in {"if", "for", "while", "switch", "catch", "function"}:
            continue
        body = method_body(src, m.group(1)) or ""
        if "FlowAttributeChangeEvent" in body and re.search(r"FlowNavigation\w+Event\(", body):
            out.append(("WARN", f"{meta.parent}: {m.group(1)}() fires FlowAttributeChangeEvent and a FlowNavigation event together; the guide warns of race conditions"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Flow screen LWC bundles.")
    ap.add_argument("--manifest-dir", default=".", help="Directory holding the LWC bundles (default: .).")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as failures.")
    args = ap.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    metas = sorted(root.rglob("*.js-meta.xml"))
    if not metas:
        print(f"WARN: no *.js-meta.xml files under {root}; nothing to check")
        return 0
    findings: list[tuple[str, str]] = []
    for meta in metas:
        findings.extend(check_bundle(meta))
    for level, msg in findings:
        print(f"{level}: {msg}")
    errors = [f for f in findings if f[0] == "ERROR"]
    warns = [f for f in findings if f[0] == "WARN"]
    if errors or (args.strict and warns):
        return 1
    if not findings:
        print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
