#!/usr/bin/env python3
"""Checker script for Custom Button to Action Migration skill.

Scans a source tree (--manifest-dir; --project-dir is a kept alias) for:

- WebLink (custom button) metadata that fails to parse, or whose Required
  `linkType` / `openType` is missing or not a documented enum value
  (api_meta 264 WebLink L47926-47944)           -> ERROR (exit 1)
- WebLink with `linkType` javascript / `openType` onClickJavaScript
  (needs a Lightning replacement)                -> REVIEW
- LWC `.js` using native alert()/confirm()       -> WARN (use LightningAlert,
  LightningConfirm or ShowToastEvent; window.confirm() is not supported for
  cross-origin iframes in Chrome and Safari - LWC guide use-dialog-confirm)
- LWC `.js` using sforce.* / $A.* / window.opener -> WARN (Classic / Aura only)
- `@AuraEnabled` method returning PageReference   -> WARN (return data and
  navigate client-side)
- Apex class with `@AuraEnabled` and no sharing keyword -> WARN (API 67.0 and
  later default to `with sharing`; below 67.0 an @AuraEnabled method called
  from LWC also runs with sharing, but the class called from other Apex takes
  the caller's mode, apexdev 264 L11930-11937)

Exit codes: ERROR findings exit 1 always; WARN/REVIEW findings exit 0 unless
--strict; an empty directory prints one WARN and exits 0; a missing path is an
ERROR and exits 1. Stdlib only.

Usage:
    python3 check_custom_button_to_action_migration.py --manifest-dir path/to/project [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

LINK_TYPES = {"url", "sControl", "javascript", "page", "flow"}  # api_meta 264 L47926-47933
OPEN_TYPES = {"newWindow", "sidebar", "noSidebar", "replace", "onClickJavaScript"}  # L47938-47944


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest-dir", "--project-dir", dest="root", type=Path, default=Path.cwd())
    p.add_argument("--strict", action="store_true", help="promote WARN/REVIEW findings to exit 1")
    return p.parse_args()


def find_files(root: Path, suffix: str) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and p.name.lower().endswith(suffix)
            and ".sfdx" not in p.parts and "node_modules" not in p.parts]


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(root: ET.Element, name: str) -> str | None:
    for el in root:
        if local(el.tag) == name:
            return (el.text or "").strip()
    return None


def strip_line_comment(line: str) -> str:
    return re.sub(r"//.*$", "", line)


def scan(root: Path) -> list[tuple[str, str, Path, int, str]]:
    """Return (severity, category, file, line, message)."""
    findings: list[tuple[str, str, Path, int, str]] = []

    for f in find_files(root, ".js"):
        if "aura" in f.parts or f.name.endswith(".test.js"):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        in_block = False
        for line_no, raw in enumerate(text.splitlines(), start=1):
            line = raw
            if in_block:
                if "*/" in line:
                    line = line.split("*/", 1)[1]
                    in_block = False
                else:
                    continue
            if "/*" in line and "*/" not in line.split("/*", 1)[1]:
                line = line.split("/*", 1)[0]
                in_block = True
            line = strip_line_comment(line)
            if re.search(r"(?<![\w.])(?:window\.)?alert\s*\(", line):
                findings.append(("WARN", "native-dialog", f, line_no,
                                 "alert() - use LightningAlert or ShowToastEvent"))
            if re.search(r"(?<![\w.])(?:window\.)?confirm\s*\(", line):
                findings.append(("WARN", "native-dialog", f, line_no,
                                 "confirm() - window.confirm() is not supported for cross-origin iframes in Chrome and Safari; use LightningConfirm"))
            if re.search(r"\bsforce\.\w+", line):
                findings.append(("WARN", "classic", f, line_no, "sforce.* API - Classic JavaScript only; not available in LWC"))
            if re.search(r"\$A\.\w+", line):
                findings.append(("WARN", "classic", f, line_no, "$A.* API - Aura framework only; not available in LWC"))
            if re.search(r"\bwindow\.opener\b", line):
                findings.append(("WARN", "classic", f, line_no, "window.opener - popup pattern; re-architect as a same-window action"))

    for f in find_files(root, ".cls"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in re.finditer(r"@AuraEnabled(?:\s*\([^)]*\))?\s+(?:public|global)\s+static\s+PageReference\s+\w+", text):
            line_no = text[:m.start()].count("\n") + 1
            findings.append(("WARN", "pageref", f, line_no,
                             "@AuraEnabled method returns PageReference - return data and navigate client-side"))
        if re.search(r"@AuraEnabled", text) and not re.search(r"\b(?:with|without|inherited)\s+sharing\b", text):
            findings.append(("WARN", "sharing", f, 1,
                             "class has @AuraEnabled methods and no sharing keyword - API 67.0+ defaults to with sharing; below 67.0 an @AuraEnabled method called from LWC runs with sharing but the class called from other Apex takes the caller's mode (apexdev 264 L11930-11937); declare it"))

    for f in find_files(root, ".weblink-meta.xml") + find_files(root, ".weblink"):
        try:
            tree = ET.parse(f)
        except (ET.ParseError, OSError) as exc:
            findings.append(("ERROR", "weblink", f, 1, f"WebLink XML does not parse: {exc}"))
            continue
        el = tree.getroot()
        link_type = child_text(el, "linkType")
        open_type = child_text(el, "openType")
        if not link_type:
            findings.append(("ERROR", "weblink", f, 1, "linkType is missing (Required, api_meta 264 L47926)"))
        elif link_type not in LINK_TYPES:
            findings.append(("ERROR", "weblink", f, 1, f"linkType '{link_type}' is not one of {sorted(LINK_TYPES)}"))
        if not open_type:
            findings.append(("ERROR", "weblink", f, 1, "openType is missing (Required, api_meta 264 L47938)"))
        elif open_type not in OPEN_TYPES:
            findings.append(("ERROR", "weblink", f, 1, f"openType '{open_type}' is not one of {sorted(OPEN_TYPES)}"))
        if link_type == "javascript" or open_type == "onClickJavaScript":
            findings.append(("REVIEW", "js-button", f, 1,
                             "JavaScript custom button - plan a Lightning replacement (body is in <url>)"))

    return findings


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        sys.exit(1)
    scanned = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in (".js", ".cls", ".xml", ".weblink")]
    if not scanned:
        print(f"WARN: no .js, .cls or WebLink files under {root}; nothing to check")
        return 1 if args.strict else 0
    findings = scan(root)
    print(f"Scanned: {root}")
    print(f"Findings: {len(findings)}")
    by_sev: dict[str, list] = {}
    for sev, cat, f, ln, msg in findings:
        by_sev.setdefault(sev, []).append((cat, f, ln, msg))
    for sev in ("ERROR", "WARN", "REVIEW"):
        for cat, f, ln, msg in by_sev.get(sev, []):
            rel = f.relative_to(root) if f.is_relative_to(root) else f
            print(f"{sev}: {rel}:{ln} [{cat}] {msg}")
    if by_sev.get("ERROR"):
        return 1
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
