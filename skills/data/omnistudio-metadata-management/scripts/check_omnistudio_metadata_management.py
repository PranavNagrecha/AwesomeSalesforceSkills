#!/usr/bin/env python3
"""Checker script for OmniStudio Metadata Management skill.

Validates a retrieved OmniStudio metadata directory for common dependency-tracking
and pipeline configuration issues:

  1. Verifies all four OmniStudio metadata type directories are present.
  2. Parses each component's base64 JSON body and extracts cross-component references.
  3. Detects dangling references — references to a component name that does not appear
     in the component inventory (possible deleted/renamed component).
  4. Detects case-mismatch references — cross-component references that match an
     inventory entry only when case is normalized (naming drift).
  5. Reports components with zero inbound references (stale candidates).
  6. Warns if any OmniStudio metadata file cannot be parsed (malformed body).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_metadata_management.py [--metadata-dir PATH]

    --metadata-dir  Root of the retrieved Salesforce metadata (default: current dir).
                    Expects the standard SFDX source format layout under
                    force-app/main/default/.

Exit codes:
    0  No issues found.
    1  One or more issues found (see stderr).
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Known OmniStudio metadata subdirectory names (SFDX source format)
# ---------------------------------------------------------------------------
OMNISTUDIO_DIRS = {
    "omniUiCards": "OmniUiCard",
    "omniProcesses": "OmniProcess",
    "omniDataTransforms": "OmniDataTransform",
    "omniInteractionConfigs": "OmniInteractionConfig",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a retrieved OmniStudio metadata directory for dependency-tracking "
            "and pipeline configuration issues."
        ),
    )
    parser.add_argument(
        "--metadata-dir",
        default=".",
        help=(
            "Root directory of the retrieved Salesforce metadata "
            "(default: current directory). Should contain force-app/main/default/."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_default_dir(root: Path) -> Path:
    """Return force-app/main/default under root if it exists, else root itself."""
    candidate = root / "force-app" / "main" / "default"
    if candidate.is_dir():
        return candidate
    return root


def decode_content_body(xml_file: Path) -> dict[str, Any] | None:
    """Parse an OmniStudio XML metadata file and return the decoded JSON body.

    OmniStudio metadata files wrap the component JSON in a base64-encoded
    <content> element. Returns None if the file cannot be parsed or has no
    content element.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError:
        return None

    # Handle namespace-prefixed or bare <content> element
    content_el = root.find(".//content")
    if content_el is None:
        # Try with namespace wildcard
        for el in root.iter():
            if el.tag.endswith("content") and el.text:
                content_el = el
                break

    if content_el is None or not content_el.text:
        return None

    try:
        raw = base64.b64decode(content_el.text.strip())
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def extract_api_name(xml_file: Path) -> str:
    """Return the component API name from the filename (strip extension suffixes)."""
    name = xml_file.stem
    # Strip known double-extension patterns: e.g. MyCard.omniUiCard-meta -> MyCard
    for suffix in [
        ".omniUiCard-meta", ".omniProcess-meta",
        ".omniDataTransform-meta", ".omniInteractionConfig-meta",
        "-meta",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name


def extract_references(body: dict[str, Any], meta_type: str) -> list[tuple[str, str]]:
    """Extract cross-component references from a component JSON body.

    Returns a list of (reference_type, referenced_api_name) tuples.
    """
    refs: list[tuple[str, str]] = []

    if meta_type == "OmniUiCard":
        # DataRaptor reference in propertySet
        dr = body.get("propertySet", {}).get("dataRaptorBundleName")
        if dr:
            refs.append(("DataRaptor", dr))
        # Integration Procedure / OmniScript references in actionList
        for action in body.get("actionList", []):
            remote = action.get("actionAttributes", {}).get("remoteClass")
            if remote:
                refs.append(("IP_or_OmniScript", remote))
        # Child FlexCard references
        for child in body.get("childElements", []):
            child_name = child.get("propertySet", {}).get("cardName")
            if child_name:
                refs.append(("FlexCard", child_name))

    elif meta_type == "OmniProcess":
        # Traverse all childElements recursively for remote references
        def walk(elements: list[dict]) -> None:
            for el in elements:
                prop = el.get("propertySet", {})
                remote = prop.get("remoteClass")
                if remote:
                    refs.append(("IP_or_OmniScript", remote))
                dr = prop.get("dataRaptorBundleName")
                if dr:
                    refs.append(("DataRaptor", dr))
                nested_proc = prop.get("procedureName")
                if nested_proc:
                    refs.append(("IP_or_OmniScript", nested_proc))
                children = el.get("childElements", [])
                if children:
                    walk(children)

        walk(body.get("childElements", []))

    # OmniDataTransform and OmniInteractionConfig typically do not carry
    # outbound component references in the same pattern; skip for now.

    return refs


# ---------------------------------------------------------------------------
# Main check function
# ---------------------------------------------------------------------------

def check_omnistudio_metadata_management(metadata_dir: Path) -> list[str]:
    """Return a list of issue strings for the given metadata directory."""
    issues: list[str] = []

    if not metadata_dir.exists():
        issues.append(f"Metadata directory not found: {metadata_dir}")
        return issues

    default_dir = find_default_dir(metadata_dir)

    # ------------------------------------------------------------------
    # Check 1: Verify all four OmniStudio metadata type directories exist
    # ------------------------------------------------------------------
    present_dirs: dict[str, Path] = {}
    for dir_name, meta_type in OMNISTUDIO_DIRS.items():
        candidate = default_dir / dir_name
        if candidate.is_dir():
            present_dirs[dir_name] = candidate
        else:
            issues.append(
                f"OmniStudio metadata directory not found: {candidate} "
                f"(expected for {meta_type}). Confirm all four types were retrieved."
            )

    if not present_dirs:
        issues.append(
            "No OmniStudio metadata directories found. "
            "Run: sf project retrieve start "
            "--metadata OmniProcess OmniDataTransform OmniUiCard OmniInteractionConfig"
        )
        return issues

    # ------------------------------------------------------------------
    # Check 2: Build component inventory and extract references
    # ------------------------------------------------------------------
    # inventory: api_name (original case) -> meta_type
    inventory: dict[str, str] = {}
    # refs: caller_api_name -> list of (ref_type, callee_api_name)
    outbound_refs: dict[str, list[tuple[str, str]]] = {}
    parse_failures: list[str] = []

    for dir_name, dir_path in present_dirs.items():
        meta_type = OMNISTUDIO_DIRS[dir_name]
        for xml_file in sorted(dir_path.glob("*.xml")):
            api_name = extract_api_name(xml_file)
            inventory[api_name] = meta_type

            body = decode_content_body(xml_file)
            if body is None:
                parse_failures.append(f"{xml_file.name} ({meta_type})")
                continue

            refs = extract_references(body, meta_type)
            if refs:
                outbound_refs[api_name] = refs

    for f in parse_failures:
        issues.append(
            f"Could not decode JSON body for: {f}. "
            "File may be malformed or not use base64-encoded <content> element."
        )

    if not inventory:
        issues.append(
            "No OmniStudio component files found in retrieved metadata directories."
        )
        return issues

    # ------------------------------------------------------------------
    # Check 3: Detect dangling references (callee not in inventory)
    # ------------------------------------------------------------------
    inventory_lower: dict[str, str] = {k.lower(): k for k in inventory}

    for caller, refs in outbound_refs.items():
        for ref_type, callee in refs:
            if callee not in inventory:
                # Check for case-mismatch before flagging as dangling
                lower = callee.lower()
                if lower in inventory_lower:
                    actual = inventory_lower[lower]
                    issues.append(
                        f"CASE MISMATCH: '{caller}' references '{callee}' "
                        f"but inventory has '{actual}'. "
                        "OmniStudio API name comparisons are case-sensitive — "
                        "rename the component or fix the reference."
                    )
                else:
                    issues.append(
                        f"DANGLING REFERENCE: '{caller}' ({inventory.get(caller, '?')}) "
                        f"references '{callee}' ({ref_type}) "
                        "which is not in the retrieved component inventory. "
                        "The called component may have been deleted or renamed."
                    )

    # ------------------------------------------------------------------
    # Check 4: Detect stale candidates (zero inbound references)
    # ------------------------------------------------------------------
    all_callees: set[str] = set()
    for refs in outbound_refs.values():
        for _, callee in refs:
            all_callees.add(callee)

    stale: list[str] = []
    for api_name, meta_type in inventory.items():
        # Only flag leaf types that are typically called by others
        if meta_type in ("OmniDataTransform",) and api_name not in all_callees:
            stale.append(f"{api_name} ({meta_type})")

    if stale:
        issues.append(
            "STALE CANDIDATES (zero inbound references from other OmniStudio components) — "
            "verify against usage logs before deletion: "
            + "; ".join(stale)
        )

    # ------------------------------------------------------------------
    # Check 5: Remind about Tooling API anti-pattern (informational)
    # ------------------------------------------------------------------
    issues.append(
        "REMINDER: Do not use Tooling API MetadataComponentDependency to map "
        "OmniStudio cross-component dependencies — it does not resolve embedded "
        "JSON references. Use retrieved metadata JSON body parsing (this script) instead."
    )

    return issues


def main() -> int:
    args = parse_args()
    metadata_dir = Path(args.metadata_dir)
    issues = check_omnistudio_metadata_management(metadata_dir)

    if not issues:
        print("No issues found.")
        return 0

    # Separate informational reminders from real issues
    real_issues = [i for i in issues if not i.startswith("REMINDER:")]
    reminders = [i for i in issues if i.startswith("REMINDER:")]

    for issue in real_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    for reminder in reminders:
        print(f"INFO: {reminder}")

    return 1 if real_issues else 0


if __name__ == "__main__":
    sys.exit(main())
