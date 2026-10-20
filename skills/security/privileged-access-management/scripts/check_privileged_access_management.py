#!/usr/bin/env python3
"""Checker for privileged-access-management (stdlib only).

Reads permission sets (*.permissionset-meta.xml / *.permissionset) and
permission set groups (*.permissionsetgroup-meta.xml / *.permissionsetgroup)
under --manifest-dir and reports:

  ERROR  a file that does not parse, or one missing the Required <label>
         (PermissionSet api_meta 264 L97525; PermissionSetGroup L98037)
  WARN   a permission set granting ModifyAllData, ViewAllData,
         CustomizeApplication or ManageUsers with no <hasActivationRequired>true
         — a standing grant (hasActivationRequired: api_meta 264 L97521-97523)
  WARN   a group with hasActivationRequired false that contains a session-based
         permission set — inside a group "the permissions in them don't require
         session-based activation" (obj 264 L264383-264384)
  INFO   a group whose committed <status> is not Updated (L98046-98051)

Exit 1 on any ERROR, or on WARN with --strict; otherwise 0. A missing
--manifest-dir is an ERROR; a tree with no permission set files is one WARN, exit 0.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
PRIVILEGED = {"ModifyAllData", "ViewAllData", "CustomizeApplication", "ManageUsers"}


def text(el: ET.Element, tag: str) -> str:
    found = el.find(NS + tag)
    if found is None:
        found = el.find(tag)
    return (found.text or "").strip() if found is not None else ""


def files(root: Path, kind: str) -> list[Path]:
    return sorted(set(root.rglob(f"*.{kind}-meta.xml")) | set(root.rglob(f"*.{kind}")))


def stem(path: Path) -> str:
    return path.name.split(".")[0]


def run(root: Path) -> list:
    out: list = []
    session_sets: set[str] = set()
    for path in files(root, "permissionset"):
        try:
            el = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: XML does not parse ({exc})"))
            continue
        if not text(el, "label"):
            out.append(("ERROR", f"{path}: missing Required <label> (api_meta 264 L97525)"))
        session = text(el, "hasActivationRequired").lower() == "true"
        if session:
            session_sets.add(stem(path))
        granted = set()
        for up in list(el.iter(NS + "userPermissions")) + list(el.iter("userPermissions")):
            if text(up, "enabled").lower() == "true" and text(up, "name") in PRIVILEGED:
                granted.add(text(up, "name"))
        if granted and not session:
            out.append(("WARN", f"{path}: standing grant of {sorted(granted)} with no hasActivationRequired — use session activation or an ExpirationDate on the assignment"))
    for path in files(root, "permissionsetgroup"):
        try:
            el = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: XML does not parse ({exc})"))
            continue
        if not text(el, "label"):
            out.append(("ERROR", f"{path}: missing Required <label> (api_meta 264 L98037)"))
        members = [m.text.strip() for m in list(el.iter(NS + "permissionSets")) + list(el.iter("permissionSets")) if m.text]
        if text(el, "hasActivationRequired").lower() != "true":
            for m in members:
                if m in session_sets:
                    out.append(("WARN", f"{path}: contains session-based permission set '{m}' but the group has no hasActivationRequired — its permissions apply without activation (obj 264 L264383-264384)"))
        status = text(el, "status")
        if status and status != "Updated":
            out.append(("INFO", f"{path}: committed status '{status}' — re-check Status in the org before granting (obj 264 L220011-220015)"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag standing privileged grants and session-activation gaps in permission set metadata.")
    ap.add_argument("--manifest-dir", default=".", help="Root of the source-format metadata tree.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings as well as ERROR.")
    args = ap.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    if not files(root, "permissionset") and not files(root, "permissionsetgroup"):
        print(f"WARN: no permission set or permission set group files under {root}; nothing to check")
        return 0
    findings = run(root)
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = sum(1 for s, _ in findings if s == "WARN")
    print(f"Summary: {errors} error(s), {warns} warning(s)")
    if errors or (args.strict and warns):
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
