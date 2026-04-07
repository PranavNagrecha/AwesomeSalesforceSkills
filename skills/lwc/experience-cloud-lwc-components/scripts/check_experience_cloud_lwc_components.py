#!/usr/bin/env python3
"""Checker script for Experience Cloud LWC Components skill.

Validates LWC component metadata and associated Apex classes for common
Experience Cloud configuration issues:

  1. JS-meta.xml — checks for lightningCommunity targets and isExposed flag
  2. Apex classes — checks for 'with sharing' on @AuraEnabled classes
  3. Cross-check — flags community context imports used alongside internal targets

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_lwc_components.py --manifest-dir path/to/metadata
    python3 check_experience_cloud_lwc_components.py --lwc-dir path/to/lwc
    python3 check_experience_cloud_lwc_components.py --apex-dir path/to/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMMUNITY_TARGETS = {
    "lightningCommunity__Default",
    "lightningCommunity__Page",
}

INTERNAL_TARGETS = {
    "lightning__AppPage",
    "lightning__RecordPage",
    "lightning__HomePage",
    "lightning__Tab",
}

COMMUNITY_IMPORTS = [
    "@salesforce/community/Id",
    "@salesforce/community/basePath",
    "@salesforce/user/isGuest",
]

AURA_ENABLED_PATTERN = re.compile(r"@AuraEnabled", re.IGNORECASE)
WITH_SHARING_PATTERN = re.compile(r"\bwith\s+sharing\b", re.IGNORECASE)
WITHOUT_SHARING_PATTERN = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
CLASS_DECL_PATTERN = re.compile(
    r"^\s*public\s+(?:(?:with|without|inherited)\s+sharing\s+)?class\s+\w+",
    re.MULTILINE | re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# JS-meta.xml checks
# ---------------------------------------------------------------------------

def check_jsmeta_file(path: Path) -> list[str]:
    """Check a single JS-meta.xml file for Experience Cloud configuration issues."""
    issues: list[str] = []
    rel = path.name

    try:
        tree = ElementTree.parse(path)
    except ElementTree.ParseError as exc:
        issues.append(f"{rel}: XML parse error — {exc}")
        return issues

    root = tree.getroot()
    ns = ""
    # Handle namespace prefix if present
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    is_exposed_el = root.find(f"{ns}isExposed")
    is_exposed = is_exposed_el is not None and is_exposed_el.text and is_exposed_el.text.strip().lower() == "true"

    targets_el = root.find(f"{ns}targets")
    declared_targets: set[str] = set()
    if targets_el is not None:
        for t in targets_el.findall(f"{ns}target"):
            if t.text:
                declared_targets.add(t.text.strip())

    has_community_target = bool(declared_targets & COMMUNITY_TARGETS)
    has_internal_target = bool(declared_targets & INTERNAL_TARGETS)

    if not has_community_target:
        # Only flag if this appears to be an Experience Cloud component
        # (can't know for sure — report as informational)
        return issues  # skip — not an Experience Cloud component by declaration

    # Component has a community target — validate it
    if not is_exposed:
        issues.append(
            f"{path}: isExposed is false or missing — component will not appear "
            "in the Experience Builder component palette"
        )

    # Check for community imports in the corresponding JS file
    js_file = path.parent / (path.parent.name + ".js")
    if js_file.exists():
        js_text = js_file.read_text(encoding="utf-8", errors="replace")
        uses_community_imports = any(imp in js_text for imp in COMMUNITY_IMPORTS)
        if uses_community_imports and has_internal_target:
            issues.append(
                f"{path}: component imports @salesforce/community/* or "
                "@salesforce/user/isGuest but also declares internal Lightning "
                f"targets {declared_targets & INTERNAL_TARGETS}. Community context "
                "modules will throw a runtime error when the component is rendered "
                "on an internal Lightning page."
            )

    return issues


def check_lwc_dir(lwc_dir: Path) -> list[str]:
    """Walk an LWC metadata directory and check all JS-meta.xml files."""
    issues: list[str] = []
    meta_files = list(lwc_dir.rglob("*.js-meta.xml"))
    if not meta_files:
        issues.append(
            f"No *.js-meta.xml files found under {lwc_dir} — "
            "verify the path is correct"
        )
        return issues

    for meta_file in sorted(meta_files):
        issues.extend(check_jsmeta_file(meta_file))

    return issues


# ---------------------------------------------------------------------------
# Apex class checks
# ---------------------------------------------------------------------------

def check_apex_file(path: Path) -> list[str]:
    """Check a single Apex class file for sharing model issues."""
    issues: list[str] = []

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    if not AURA_ENABLED_PATTERN.search(text):
        return issues  # Not an @AuraEnabled class — skip

    has_with_sharing = WITH_SHARING_PATTERN.search(text)
    has_without_sharing = WITHOUT_SHARING_PATTERN.search(text)

    if has_without_sharing:
        issues.append(
            f"{path}: class uses 'without sharing' but contains @AuraEnabled "
            "methods. If this class is called from a guest-accessible Experience "
            "Cloud component, it will bypass record-level security for guest users. "
            "Change to 'with sharing' unless explicitly reviewed and documented."
        )
    elif not has_with_sharing:
        issues.append(
            f"{path}: class contains @AuraEnabled methods but has no explicit "
            "sharing declaration. Add 'with sharing' to enforce OWD and sharing "
            "rules for guest and portal users."
        )

    return issues


def check_apex_dir(apex_dir: Path) -> list[str]:
    """Walk an Apex classes directory and check all .cls files."""
    issues: list[str] = []
    cls_files = list(apex_dir.rglob("*.cls"))
    if not cls_files:
        issues.append(
            f"No *.cls files found under {apex_dir} — "
            "verify the path is correct"
        )
        return issues

    for cls_file in sorted(cls_files):
        issues.extend(check_apex_file(cls_file))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC metadata and Apex classes for Experience Cloud "
            "configuration issues (community targets, isExposed flag, "
            "sharing model on @AuraEnabled classes)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help=(
            "Root directory of a Salesforce SFDX project or metadata directory. "
            "The script will look for LWC components under force-app/main/default/lwc "
            "and Apex classes under force-app/main/default/classes."
        ),
    )
    parser.add_argument(
        "--lwc-dir",
        default=None,
        help="Path to the LWC components directory (overrides --manifest-dir for LWC).",
    )
    parser.add_argument(
        "--apex-dir",
        default=None,
        help="Path to the Apex classes directory (overrides --manifest-dir for Apex).",
    )
    return parser.parse_args()


def resolve_dirs(args: argparse.Namespace) -> tuple[Path | None, Path | None]:
    """Resolve LWC and Apex directories from args."""
    lwc_dir: Path | None = None
    apex_dir: Path | None = None

    if args.lwc_dir:
        lwc_dir = Path(args.lwc_dir)
    elif args.manifest_dir:
        candidate = Path(args.manifest_dir) / "force-app" / "main" / "default" / "lwc"
        if candidate.exists():
            lwc_dir = candidate
        else:
            # Fallback: maybe the user pointed directly at the metadata root
            candidate2 = Path(args.manifest_dir) / "lwc"
            if candidate2.exists():
                lwc_dir = candidate2

    if args.apex_dir:
        apex_dir = Path(args.apex_dir)
    elif args.manifest_dir:
        candidate = Path(args.manifest_dir) / "force-app" / "main" / "default" / "classes"
        if candidate.exists():
            apex_dir = candidate
        else:
            candidate2 = Path(args.manifest_dir) / "classes"
            if candidate2.exists():
                apex_dir = candidate2

    return lwc_dir, apex_dir


def main() -> int:
    args = parse_args()

    if not any([args.manifest_dir, args.lwc_dir, args.apex_dir]):
        print(
            "Usage: python3 check_experience_cloud_lwc_components.py "
            "--manifest-dir path/to/project  (or --lwc-dir / --apex-dir)",
            file=sys.stderr,
        )
        return 2

    lwc_dir, apex_dir = resolve_dirs(args)

    all_issues: list[str] = []

    if lwc_dir:
        if not lwc_dir.exists():
            all_issues.append(f"LWC directory not found: {lwc_dir}")
        else:
            all_issues.extend(check_lwc_dir(lwc_dir))
    else:
        print("INFO: No LWC directory resolved — skipping JS-meta.xml checks.", file=sys.stderr)

    if apex_dir:
        if not apex_dir.exists():
            all_issues.append(f"Apex directory not found: {apex_dir}")
        else:
            all_issues.extend(check_apex_dir(apex_dir))
    else:
        print("INFO: No Apex directory resolved — skipping Apex sharing checks.", file=sys.stderr)

    if not all_issues:
        print("No Experience Cloud LWC issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(all_issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
