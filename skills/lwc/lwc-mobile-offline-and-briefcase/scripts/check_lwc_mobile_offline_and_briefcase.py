#!/usr/bin/env python3
"""Detect LWC offline / Briefcase configuration issues in retrieved metadata.

Walks an SFDX-style metadata tree (force-app/) and reports:

1. Briefcase definitions present in the project.
2. LWC bundles that import `@salesforce/apex/...` (imperative Apex) without
   appearing to handle offline error cases.
3. LWC bundles that use `@salesforce/client/formFactor` (reasonable hint that
   the component is mobile-aware).
4. LWC bundles that write `localStorage.setItem` (potential PII-via-draft
   pattern that should be hand-reviewed).
5. LWC bundles that include `lightning-record-edit-form` or `getRecord`
   (LDS path — generally good for offline) for cross-reference.

Stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_mobile_offline_and_briefcase.py [--root force-app/main/default]

Exit codes:
    0  no findings worth flagging
    1  findings present (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"s": "http://soap.sforce.com/2006/04/metadata"}

IMPORT_APEX_RE = re.compile(
    r"""import\s+\w+\s+from\s+['"]@salesforce/apex/[^'"]+['"]""", re.MULTILINE
)
TRY_CATCH_RE = re.compile(r"\btry\s*{", re.MULTILINE)
NAVIGATOR_ONLINE_RE = re.compile(r"\bnavigator\.onLine\b")
FORM_FACTOR_RE = re.compile(
    r"""['"]@salesforce/client/formFactor['"]"""
)
LOCAL_STORAGE_RE = re.compile(r"\blocalStorage\.setItem\b")
LDS_GETRECORD_RE = re.compile(r"\bgetRecord\b|\bgetRecords\b|\bupdateRecord\b|\bcreateRecord\b")
RECORD_EDIT_FORM_RE = re.compile(r"<lightning-record-edit-form\b|lightning-record-form\b")


def find_briefcase_definitions(root: Path) -> list[Path]:
    """Locate Briefcase Definition metadata files.

    Briefcase metadata typically lives under a `briefcaseDefinitions/` folder
    with a *.briefcaseDefinition-meta.xml suffix. Naming has shifted over
    releases; we glob both patterns defensively.
    """
    findings: list[Path] = []
    for pattern in (
        "briefcaseDefinitions/**/*.briefcaseDefinition-meta.xml",
        "briefcaseDefinitions/**/*.briefcase-meta.xml",
    ):
        findings.extend(root.glob(pattern))
    return sorted(set(findings))


def walk_lwc_bundles(root: Path) -> list[Path]:
    """Return every LWC bundle directory under the given root."""
    lwc_root = root / "lwc"
    if not lwc_root.exists():
        return []
    return [p for p in lwc_root.iterdir() if p.is_dir()]


def analyze_lwc_bundle(bundle: Path) -> dict:
    """Inspect a single LWC bundle for offline-relevant signals."""
    summary = {
        "bundle": bundle.name,
        "apex_imports": [],
        "has_try_catch": False,
        "checks_navigator_online": False,
        "uses_form_factor": False,
        "writes_localstorage": False,
        "uses_lds": False,
        "uses_record_edit_form": False,
    }
    js_files = list(bundle.glob("*.js"))
    html_files = list(bundle.glob("*.html"))

    for fp in js_files:
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in IMPORT_APEX_RE.finditer(text):
            summary["apex_imports"].append((fp.name, m.group(0).strip()))
        if TRY_CATCH_RE.search(text):
            summary["has_try_catch"] = True
        if NAVIGATOR_ONLINE_RE.search(text):
            summary["checks_navigator_online"] = True
        if FORM_FACTOR_RE.search(text):
            summary["uses_form_factor"] = True
        if LOCAL_STORAGE_RE.search(text):
            summary["writes_localstorage"] = True
        if LDS_GETRECORD_RE.search(text):
            summary["uses_lds"] = True

    for fp in html_files:
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if RECORD_EDIT_FORM_RE.search(text):
            summary["uses_record_edit_form"] = True

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit LWC bundles and Briefcase definitions for offline patterns."
    )
    parser.add_argument(
        "--root",
        default="force-app/main/default",
        help="Root directory of the SFDX metadata (default: force-app/main/default).",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"metadata root not found: {root}", file=sys.stderr)
        return 0

    findings_count = 0

    # 1. Briefcase definitions
    briefcase_files = find_briefcase_definitions(root)
    if briefcase_files:
        print("\n## Briefcase Definitions present in this project")
        for fp in briefcase_files:
            print(f"  - {fp.relative_to(root)}")
    else:
        print("\n## No Briefcase Definitions found in this metadata tree.")
        print("   If offline access is required, design and add a Briefcase rule")
        print("   under Setup -> Briefcase Builder, then retrieve the metadata.")

    # 2. LWC bundles — offline-relevant signals
    bundles = walk_lwc_bundles(root)
    if not bundles:
        print("\n## No LWC bundles found under force-app/.../lwc/")
        return 0

    bundles_with_apex_no_offline = []
    bundles_with_localstorage = []
    bundles_form_factor = []
    bundles_using_lds = []

    for bundle in bundles:
        info = analyze_lwc_bundle(bundle)
        if info["apex_imports"] and not info["has_try_catch"] and not info["checks_navigator_online"]:
            bundles_with_apex_no_offline.append(info)
        if info["writes_localstorage"]:
            bundles_with_localstorage.append(info)
        if info["uses_form_factor"]:
            bundles_form_factor.append(info)
        if info["uses_lds"] or info["uses_record_edit_form"]:
            bundles_using_lds.append(info)

    if bundles_with_apex_no_offline:
        print("\n## LWC bundles importing imperative Apex with no visible offline handling")
        print("   (no try/catch and no navigator.onLine reference — review for offline UX)")
        for info in bundles_with_apex_no_offline:
            print(f"  - {info['bundle']}")
            for src, imp in info["apex_imports"][:3]:
                print(f"      {src}: {imp}")
            if len(info["apex_imports"]) > 3:
                print(f"      ... and {len(info['apex_imports']) - 3} more")
        findings_count += len(bundles_with_apex_no_offline)

    if bundles_with_localstorage:
        print("\n## LWC bundles writing to localStorage")
        print("   (review for sensitive data — localStorage is unencrypted and not FLS-controlled)")
        for info in bundles_with_localstorage:
            print(f"  - {info['bundle']}")
        findings_count += len(bundles_with_localstorage)

    if bundles_form_factor:
        print("\n## LWC bundles using @salesforce/client/formFactor (mobile-aware)")
        for info in bundles_form_factor:
            print(f"  - {info['bundle']}")

    if bundles_using_lds:
        print("\n## LWC bundles using LDS (offline-friendly read/write paths)")
        for info in bundles_using_lds[:20]:
            print(f"  - {info['bundle']}")
        if len(bundles_using_lds) > 20:
            print(f"  ... and {len(bundles_using_lds) - 20} more")

    if findings_count == 0:
        print("\nNo offline-readiness concerns flagged.")
        return 0

    print(f"\nTotal flagged bundles: {findings_count}")
    print("Refer to the skill workflow for review steps.")
    print(f"ERROR: {findings_count} offline-readiness concern(s); see report above.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
