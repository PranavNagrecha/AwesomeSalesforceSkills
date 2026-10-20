#!/usr/bin/env python3
"""Check Flow screen metadata and related LWCs for common UX issues.

Rules (premises from api_meta 264 and the LWC guide, cited as lwcguide <slug>):

  ERROR  flow XML that does not parse.
  ERROR  a custom screen component whose ``validate`` is an arrow-function
         property (lwcguide use-flow-validate-user-input-for-custom-components:
         "Arrow function expressions don't work for validation").
  WARN   more than 7 screens (a rule of thumb from SKILL.md, not a limit).
  WARN   a record create/update/delete element whose connector leads to a screen
         that itself continues to another element: a commit in the middle of the
         interview. A terminal confirmation screen (no connector) is Pattern 1.
  WARN   a ComponentInstance field (``extensionName`` names the Lightning
         component, FlowScreenField api_meta 264 L74393-74395) whose JS has
         no ``validate(`` method, or no ``reportValidity(``.
  WARN   a referenced component whose JS cannot be found under --manifest-dir.
         Only un-namespaced or ``c:`` components are checked; standard ones such
         as ``flowruntime:name`` (api_meta 264 L76231) are skipped.

Exit codes: ERROR findings exit 1 always; WARN findings exit 0 unless
``--strict``; no screen flows prints one WARN and exits 0; a missing directory
is an ERROR and exits 1. Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

VALIDATE_RE = re.compile(r"(?m)^\s*(?:@api\s+)?validate\s*\(")
VALIDATE_ARROW_RE = re.compile(r"(?m)^\s*(?:@api\s+)?validate\s*=\s*(?:async\s*)?\(")
REPORT_VALIDITY_RE = re.compile(r"\breportValidity\s*\(")
DML_TAGS = {"recordCreates", "recordUpdates", "recordDeletes"}
MAX_SCREENS = 7


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check screen flows and related custom components for common UX issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or source tree (default: current directory).",
    )
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def kids(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in element if local_name(c.tag) == name]


def text_of(element: ET.Element, name: str) -> str:
    for c in kids(element, name):
        if c.text:
            return c.text.strip()
    return ""


def component_names(screen: ET.Element) -> list[str]:
    """extensionName values of ComponentInstance fields (nested fields included)."""
    names = []
    for field in screen.iter():
        if local_name(field.tag) == "fields" and text_of(field, "fieldType") == "ComponentInstance":
            ext = text_of(field, "extensionName")
            if ext:
                names.append(ext)
    return names


def find_lwc_js(root: Path, component_name: str) -> Path | None:
    bare = component_name.split(":")[-1]
    for candidate in sorted(root.rglob(f"{bare}.js")):
        return candidate
    return None


def check_flow(path: Path, root_dir: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    try:
        flow = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"{path}: unable to parse flow metadata ({exc})")]
    screens = kids(flow, "screens")
    if not screens:
        return out
    if len(screens) > MAX_SCREENS:
        out.append(("WARN", f"{path}: {len(screens)} screens; review whether the interview has become too fragmented (rule of thumb: more than {MAX_SCREENS} is a maze)"))
    continuing = {text_of(s, "name") for s in screens if kids(s, "connector")}
    for dml in (e for e in flow if local_name(e.tag) in DML_TAGS):
        for conn in kids(dml, "connector"):
            if text_of(conn, "targetReference") in continuing:
                out.append(("WARN", f"{path}: `{text_of(dml, 'name')}` commits records and then shows screen `{text_of(conn, 'targetReference')}`, which continues the interview; confirm the commit is not mid-interview"))
    for screen in screens:
        for name in component_names(screen):
            ns = name.split(":")[0] if ":" in name else ""
            if ns not in ("", "c"):
                # Standard (flowruntime:name, flowruntime:toggle -- the guide's own
                # example, api_meta 264 L76231, L76263) or packaged components are
                # not this org's custom LWCs; their source is not in the project.
                continue
            js = find_lwc_js(root_dir, name)
            if js is None:
                out.append(("WARN", f"{path}: custom screen component `{name}` was referenced but no matching JS file was found under the manifest dir"))
                continue
            src = js.read_text(encoding="utf-8", errors="ignore")
            if VALIDATE_ARROW_RE.search(src):
                out.append(("ERROR", f"{js}: validate is an arrow function; the LWC guide says it does not work for flow screen validation"))
            elif not VALIDATE_RE.search(src):
                out.append(("WARN", f"{js}: custom Flow screen component has no validate() method"))
            if not REPORT_VALIDITY_RE.search(src):
                out.append(("WARN", f"{js}: custom Flow screen component has no reportValidity() to render internal and external errors"))
    return out


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    flows = sorted(root.rglob("*.flow-meta.xml"))
    if not flows:
        print(f"WARN: no *.flow-meta.xml files under {root}; nothing to check")
        return 0
    findings: list[tuple[str, str]] = []
    for flow_path in flows:
        findings.extend(check_flow(flow_path, root))
    for level, msg in findings:
        print(f"{level}: {msg}")
    if not findings:
        print("No issues found.")
    has_error = any(lv == "ERROR" for lv, _ in findings)
    has_warn = any(lv == "WARN" for lv, _ in findings)
    return 1 if has_error or (args.strict and has_warn) else 0


if __name__ == "__main__":
    sys.exit(main())
