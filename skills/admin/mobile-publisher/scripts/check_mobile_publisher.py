#!/usr/bin/env python3
"""Checker for Mobile Publisher readiness against repo metadata.

Most of Mobile Publisher is configured outside the Metadata API (in Setup +
the customer's developer accounts); the site's ExperienceBundle
nativeConfig.json carries its app-update flags (api_meta 264 L62894-62917).
This checker inspects the source Experience Cloud site, custom notification
types and any External Client App push settings.

  M1  WARN   No Experience Cloud site (Network) found — Mobile Publisher
             needs a source experience to wrap.
  M2  ERROR  A Network, CustomNotificationType or ExtlClntAppPushSettings
             file does not parse as XML.
  M3  WARN   No account-deletion page found by name (deleteaccount /
             accountdeletion / deletemyaccount) — a store-policy heuristic.
  M4  WARN   A CustomNotificationType has `<mobile>false</mobile>`; the
             Required `mobile` field is the mobile delivery channel
             (api_meta 264 L43964), so the branded app never receives it.
  M5  ERROR  An ExtlClntAppPushSettings record carries both
             androidPushConfig and applePushConfig — the guide allows one,
             "but not both" (api_meta 264 L68402-68406).
  M6  WARN   An ExtlClntAppPushSettings record carries an inline
             androidPushConfig/applePushConfig — those credentials "can't be
             packaged or added to source control" (pkg2_dev 264 L9467-9469).

Removed rules (false premises): a `<scopes>Mobile</scopes>` OAuth scope does
not exist in ConnectedAppOauthAccessScope (api_meta 264 L37584-37723); the
Network type has no privacy-policy URL field; LoginConfig is not a
metadata type.

Exit codes: 0 = no ERROR (WARN findings exit 0 unless --strict); 1 = an
ERROR finding, a WARN under --strict, or a missing --manifest-dir. An empty
directory prints one WARN and exits 0. Stdlib only.

Usage:
    python3 check_mobile_publisher.py --manifest-dir force-app [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple


def _files(root: Path, *suffixes: str) -> List[Path]:
    out: List[Path] = []
    for suffix in suffixes:
        out.extend(root.rglob(f"*{suffix}"))
    return sorted(set(out))


def _parse(path: Path) -> Optional[ET.Element]:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(elem: ET.Element, name: str) -> Optional[ET.Element]:
    for c in elem:
        if _local(c.tag) == name:
            return c
    return None


def _scan(root: Path) -> List[Tuple[str, str]]:
    findings: List[Tuple[str, str]] = []

    networks = _files(root, ".network-meta.xml", ".network")
    if not networks:
        findings.append(("WARN", f"{root}: M1  no Experience Cloud Network found — Mobile Publisher requires a source experience"))
    for n in networks:
        if _parse(n) is None:
            findings.append(("ERROR", f"{n}: M2  Network file does not parse as XML"))

    names = ["".join(ch for ch in p.name.lower() if ch.isalnum()) for p in root.rglob("*")]
    if networks and not any(t in nm for nm in names for t in ("deleteaccount", "accountdeletion", "deletemyaccount")):
        findings.append(("WARN", f"{root}: M3  no account-deletion page found by name — the stores expect an in-app deletion path (store policy)"))

    for nt in _files(root, ".notiftype-meta.xml", ".notiftype"):
        doc = _parse(nt)
        if doc is None:
            findings.append(("ERROR", f"{nt}: M2  CustomNotificationType does not parse as XML"))
            continue
        mobile = _child(doc, "mobile")
        if mobile is not None and (mobile.text or "").strip().lower() == "false":
            findings.append(("WARN", f"{nt}: M4  mobile delivery channel is false — the branded app will not receive this notification"))

    for ps in _files(root, ".ecaPush-meta.xml", ".ecaPush"):
        doc = _parse(ps)
        if doc is None:
            findings.append(("ERROR", f"{ps}: M2  ExtlClntAppPushSettings does not parse as XML"))
            continue
        android = _child(doc, "androidPushConfig")
        apple = _child(doc, "applePushConfig")
        if android is not None and apple is not None:
            findings.append(("ERROR", f"{ps}: M5  both androidPushConfig and applePushConfig in one record — the type allows one"))
        elif android is not None or apple is not None:
            findings.append(("WARN", f"{ps}: M6  inline push credentials in source — keep only pushConfigLink in source control"))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Flag Mobile Publisher readiness gaps in repo metadata.")
    parser.add_argument("--manifest-dir", default="force-app", help="Root directory of Salesforce metadata (default: force-app).")
    parser.add_argument("--strict", action="store_true", help="Treat WARN findings as failures (exit 1).")
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    if not any(p.is_file() for p in root.rglob("*")):
        print(f"WARN: {root} is empty — nothing to check")
        return 0

    findings = _scan(root)
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = len(findings) - errors
    if not findings:
        print(f"OK: scanned {root}, no Mobile Publisher readiness gaps found.")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
