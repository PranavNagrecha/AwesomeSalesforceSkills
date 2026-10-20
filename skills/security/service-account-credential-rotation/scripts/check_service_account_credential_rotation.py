#!/usr/bin/env python3
"""Checker for service-account-credential-rotation (stdlib only).

Reads profiles, permission sets and connected apps under --manifest-dir:

  ERROR  a profile, permission set or connected app file that does not parse
  WARN   the Password Never Expires user permission enabled on a profile or
         permission set (<userPermissions><name>PasswordNeverExpires</name>;
         a permission, not a User field — secguide 262 L6398)
  WARN   a connected app whose source carries a <consumerSecret> — the value
         "isn't returned in Metadata API requests" (api_meta 264 L37443-37444),
         so a committed one was put there by hand and is a secret in source control
  INFO   a connected app with a <certificate> — one certificate per app
         (api_meta 264 L37419), so plan JWT rotation as a cutover

Earlier versions read per-user XML files and
flagged files by modification time (a checkout resets it); both rules are gone.

Exit 1 on any ERROR, or on WARN with --strict; otherwise 0. A missing
--manifest-dir is an ERROR; a tree with nothing to check is one WARN, exit 0.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"


def text(el: ET.Element, tag: str) -> str:
    found = el.find(NS + tag)
    if found is None:
        found = el.find(tag)
    return (found.text or "").strip() if found is not None else ""


def find(el: ET.Element, tag: str) -> list:
    return list(el.iter(NS + tag)) + list(el.iter(tag))


def collect(root: Path) -> tuple[list[Path], list[Path]]:
    perms = sorted(set(root.rglob("*.profile-meta.xml")) | set(root.rglob("*.permissionset-meta.xml")))
    apps = sorted(root.rglob("*.connectedApp-meta.xml"))
    return perms, apps


def run(perms: list[Path], apps: list[Path]) -> list:
    out: list = []
    for path in perms:
        try:
            el = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: XML does not parse ({exc})"))
            continue
        for up in find(el, "userPermissions"):
            if text(up, "name") == "PasswordNeverExpires" and text(up, "enabled").lower() == "true":
                out.append(("WARN", f"{path}: grants Password Never Expires — service-account passwords never rotate (secguide 262 L6398)"))
    for path in apps:
        try:
            el = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: XML does not parse ({exc})"))
            continue
        for cfg in find(el, "oauthConfig"):
            if text(cfg, "consumerSecret"):
                out.append(("WARN", f"{path}: consumerSecret committed to source — Metadata API does not return it (api_meta 264 L37443-37444); move it to a vault"))
            if text(cfg, "certificate"):
                out.append(("INFO", f"{path}: JWT certificate present — one certificate per app (api_meta 264 L37419); rotate as a cutover"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag credential-rotation anti-patterns in profile, permission set and connected app metadata.")
    ap.add_argument("--manifest-dir", "--project-dir", dest="manifest_dir", default=".", help="Root of the source-format metadata tree.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings as well as ERROR.")
    args = ap.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    perms, apps = collect(root)
    if not perms and not apps:
        print(f"WARN: no profile, permission set or connected app files under {root}; nothing to check")
        return 0
    findings = run(perms, apps)
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
