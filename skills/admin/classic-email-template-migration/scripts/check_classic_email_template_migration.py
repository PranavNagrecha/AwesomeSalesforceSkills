#!/usr/bin/env python3
"""Checker script for Classic Email Template Migration skill.

Scans retrieved metadata (email/, workflows/, classes/) for migration concerns:

- ERROR: an .email-meta.xml that does not parse
- ERROR: a template with <uiType>SFX</uiType> whose <type> is not custom
  ("If UiType is SFX, the type must be custom", api_meta 264 L59152)
- ERROR: a workflow <alerts> block with no <template> (Required, api_meta 264 L143888)
- WARN: an alert with senderType OrgWideEmailAddress but no <senderAddress>
  (api_meta 264 L143859-143886)
- REVIEW: a Lightning (uiType SFX) template body still holding IF/CASE/$Setup/System.
  merge expressions — Lightning support for them is UNVERIFIED (2026-10-20); sandbox-test
- INFO: Apex setTemplateId() with a hard-coded 00X template ID — map old to new

No template stores a sender, so there is no rule about OrgWideEmailAddress on Apex calls.
Stdlib only. Exit 1 on ERROR; WARN/REVIEW/INFO exit 0 unless --strict; empty dir one WARN.

Usage:
    python3 check_classic_email_template_migration.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MERGE_PATTERNS = [
    (r"\{!IF\s*\(", "IF() merge expression"),
    (r"\{!CASE\s*\(", "CASE() merge expression"),
    (r"\{!URLENCODE\s*\(", "URLENCODE() merge expression"),
    (r"\{!BLANKVALUE\s*\(", "BLANKVALUE() merge expression"),
    (r"\{!\$Setup\.", "$Setup merge field"),
    (r"\{!System\.", "System.* merge field"),
]
HARDCODED_ID = re.compile(r"setTemplateId\s*\(\s*'00X[A-Za-z0-9]{12}(?:[A-Za-z0-9]{3})?'")
ALERT_BLOCK = re.compile(r"<alerts>(.*?)</alerts>", re.DOTALL)


def local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(root: ET.Element, name: str) -> str | None:
    for el in root:
        if local(el.tag) == name:
            return (el.text or "").strip()
    return None


def files(root: Path, pattern: str) -> list[Path]:
    return [p for p in root.rglob(pattern) if p.is_file() and ".sfdx" not in p.parts]


def scan(root: Path) -> list[tuple[str, Path, int, str]]:
    out: list[tuple[str, Path, int, str]] = []
    for meta in files(root, "*.email-meta.xml"):
        try:
            tree = ET.parse(meta).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", meta, 0, f"does not parse: {exc}"))
            continue
        ui, typ = child_text(tree, "uiType"), child_text(tree, "type")
        if ui == "SFX" and typ is not None and typ != "custom":
            out.append(("ERROR", meta, 0, f"uiType SFX requires type custom, found '{typ}' (api_meta 264 L59152)"))
        body = meta.with_name(meta.name[: -len("-meta.xml")])
        if ui == "SFX" and body.is_file():
            for n, line in enumerate(body.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                for rx, label in MERGE_PATTERNS:
                    if re.search(rx, line):
                        out.append(("REVIEW", body, n, f"{label} in a Lightning template — support UNVERIFIED; sandbox-test or pre-compute"))
    for wf in files(root, "*.workflow-meta.xml"):
        text = wf.read_text(encoding="utf-8", errors="ignore")
        for m in ALERT_BLOCK.finditer(text):
            block, ln = m.group(1), text[: m.start()].count("\n") + 1
            if "<template>" not in block:
                out.append(("ERROR", wf, ln, "alert has no <template> (Required, api_meta 264 L143888)"))
            if "<senderType>OrgWideEmailAddress</senderType>" in block and "<senderAddress>" not in block:
                out.append(("WARN", wf, ln, "senderType OrgWideEmailAddress with no <senderAddress>"))
    for cls in files(root, "*.cls"):
        for n, line in enumerate(cls.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if HARDCODED_ID.search(line):
                out.append(("INFO", cls, n, "hard-coded template ID in setTemplateId() — resolve from the old-to-new map"))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest-dir", "--project-dir", dest="root", type=Path, default=Path.cwd())
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()
    root = args.root
    if not root.is_dir():
        print(f"ERROR: manifest dir not found: {root}")
        sys.exit(1)
    if not any(root.rglob("*")):
        print(f"WARN: {root} is empty — nothing to check")
        return 0
    findings = scan(root)
    for sev, f, ln, msg in findings:
        print(f"{sev}: {f}:{ln} — {msg}")
    if not findings:
        print("OK: no findings")
    if any(s == "ERROR" for s, *_ in findings):
        return 1
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
