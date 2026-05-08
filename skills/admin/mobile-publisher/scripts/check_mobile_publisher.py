#!/usr/bin/env python3
"""Checker for Mobile Publisher readiness against repo metadata.

Mobile Publisher itself is configured outside the metadata API (in Setup +
the customer's developer accounts). This checker focuses on what *is*
inspectable in `force-app/`: the source Experience Cloud or Field Service
configuration that becomes the branded app. It flags concrete readiness
gaps:

  M1  No Experience Cloud site or FSL configuration found — Mobile
      Publisher needs a source experience to wrap
  M2  Experience Cloud site exists but no `LoginPage` Experience
      Cloud login configuration is detected — App Store reviewers cannot
      complete review without a documented login flow
  M3  No `AccountDeletion` / "delete my account" page found in the
      Experience Cloud network metadata — Apple + Google require an
      in-app account-deletion path
  M4  Connected App for mobile push is missing the `mobile` scope — push
      notifications won't work
  M5  No privacy-policy URL configured on the network — App Store
      submission will be rejected

Stdlib only.

Usage:
    python3 check_mobile_publisher.py
    python3 check_mobile_publisher.py --manifest-dir force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List


def _scan(root: Path) -> List[str]:
    findings: List[str] = []

    # M1 — at least one Experience Cloud site (Network) or FSL config?
    networks = list(root.rglob("*.network-meta.xml")) + list(root.rglob("*.site-meta.xml"))
    fsl_configs = list(root.rglob("*FieldService*.fieldServiceMobileSettings-meta.xml"))
    if not networks and not fsl_configs:
        findings.append(
            f"{root}: M1  no Experience Cloud network/site or Field Service mobile settings found — Mobile Publisher requires a source experience"
        )

    # M2 — login configuration: experience cloud login flow / loginConfig
    login_pages = list(root.rglob("*.loginConfig-meta.xml")) + list(root.rglob("LoginFlow*.flow-meta.xml"))
    if networks and not login_pages:
        findings.append(
            f"{root}: M2  Experience Cloud network present but no LoginConfig / LoginFlow detected — document a fallback test account for App Store review"
        )

    # M3 — account-deletion page
    pages = list(root.rglob("*.flexipage-meta.xml")) + list(root.rglob("*.aura-meta.xml")) + list(root.rglob("*.lwc-meta.xml"))
    has_deletion = False
    for p in pages:
        name = p.stem.lower()
        if any(token in name for token in ("deleteaccount", "accountdeletion", "deletemyaccount")):
            has_deletion = True
            break
    if networks and not has_deletion:
        findings.append(
            f"{root}: M3  no account-deletion page found (search: deleteaccount/accountdeletion) — required by Apple iOS 16+ and Google 2024+"
        )

    # M4 — connected app with mobile / push scope
    push_ok = False
    for ca in root.rglob("*.connectedApp-meta.xml"):
        try:
            text = ca.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(r"<scopes>\s*Mobile\s*</scopes>", text, re.I) or "MobilePushNotification" in text or "<mobileSessionTimeout>" in text:
            push_ok = True
            break
    if networks and not push_ok:
        findings.append(
            f"{root}: M4  no Connected App with Mobile/Push scope detected — required for Mobile Publisher push notifications"
        )

    # M5 — privacy policy URL configured on a network
    privacy_ok = False
    for n in networks:
        try:
            text = n.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(r"<privacyPolicyUrl>\s*https?://", text, re.I) or re.search(r"<privacyPolicy>\s*https?://", text, re.I):
            privacy_ok = True
            break
    if networks and not privacy_ok:
        findings.append(
            f"{root}: M5  no privacy policy URL detected in any network metadata — App Store and Play Store submissions require it"
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Flag Mobile Publisher readiness gaps in repo metadata.",
    )
    parser.add_argument(
        "--manifest-dir",
        default="force-app",
        help="Root directory of Salesforce metadata (default: force-app).",
    )
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"Manifest directory not found: {root}", file=sys.stderr)
        return 2

    findings = _scan(root)

    if not findings:
        print(f"OK: scanned {root}, no Mobile Publisher readiness gaps found.")
        return 0

    for line in findings:
        print(f"WARN: {line}", file=sys.stderr)
    print(
        f"\nWARN: found {len(findings)} Mobile Publisher readiness gap(s).",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
