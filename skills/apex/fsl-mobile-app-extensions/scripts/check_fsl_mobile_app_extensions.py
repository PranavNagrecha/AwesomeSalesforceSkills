#!/usr/bin/env python3
"""Checker script for FSL Mobile App Extensions skill.

Scans a Salesforce metadata project directory for common FSL Mobile extension
issues described in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_mobile_app_extensions.py [--help]
    python3 check_fsl_mobile_app_extensions.py --manifest-dir path/to/metadata

Checks performed:
  - LWC module imports inside HTML5 Mobile Extension Toolkit files
  - Imperative Apex calls that bypass LDS offline cache
  - Custom Metadata Types referenced in Briefcase Builder definitions
  - LWC Quick Actions not found on any page layout (offline availability gap)
  - Deep link URI payloads exceeding 900 KB (approaching 1 MB limit)
  - Missing "Enable Lightning SDK for FSL Mobile" permission set assignment
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# LWC module imports that are invalid inside HTML5 Mobile Extension Toolkit files
INVALID_LWC_IMPORTS = re.compile(
    r"""import\s+.*?from\s+['"](?:lwc|lightning/|@salesforce/)""",
    re.MULTILINE,
)

# Apex method imported in LWC JS (candidate for imperative call check)
APEX_IMPORT = re.compile(
    r"""import\s+\w+\s+from\s+['"]@salesforce/apex/[^'"]+['"]""",
    re.MULTILINE,
)

# @wire decorator usage — if present alongside Apex import, the import may be wired
WIRE_DECORATOR = re.compile(r"@wire\s*\(", re.MULTILINE)

# Deep link payload size heuristic — URI with custom field value parameters
DEEP_LINK_URI = re.compile(
    r"""['"]fsl://[^'"]{100,}['"]""",
    re.MULTILINE,
)

# Custom Metadata Type object name in XML
CMT_OBJECT_NAME = re.compile(
    r"""<objectName>[A-Za-z0-9_]+__mdt</objectName>""",
    re.MULTILINE,
)

# LWC Quick Action type marker in quickAction XML
LWC_ACTION_TYPE = re.compile(
    r"""<type>LightningWebComponent</type>""",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def find_files(root: Path, suffix: str) -> list[Path]:
    return list(root.rglob(f"*{suffix}"))


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_lwc_in_html5_extensions(manifest_dir: Path) -> list[str]:
    """Flag LWC module imports inside files in HTML5 Mobile Extension directories."""
    issues: list[str] = []
    for js_file in manifest_dir.rglob("*.js"):
        parts_str = "/".join(js_file.parts)
        if "mobileExtension" in parts_str or "mobile_extension" in parts_str:
            content = read_text(js_file)
            if INVALID_LWC_IMPORTS.search(content):
                issues.append(
                    f"[HTML5-EXTENSION] LWC module import in HTML5 Extension file: "
                    f"{js_file}. HTML5 Toolkit files cannot import lwc, lightning/, "
                    f"or @salesforce/ modules. Use REST API for Apex calls."
                )
    return issues


def check_imperative_apex_offline(manifest_dir: Path) -> list[str]:
    """Warn when Apex is imported but no @wire decorator is present (imperative call risk)."""
    issues: list[str] = []
    for js_file in find_files(manifest_dir, ".js"):
        if "test" in js_file.name.lower() or "meta" in js_file.name.lower():
            continue
        content = read_text(js_file)
        if APEX_IMPORT.search(content) and not WIRE_DECORATOR.search(content):
            issues.append(
                f"[OFFLINE-RISK] {js_file}: Apex method imported without @wire. "
                f"Imperative Apex calls fail when the device is offline in FSL Mobile. "
                f"Use @wire(apexMethod, {{recordId: '$recordId'}}) to enable LDS caching."
            )
    return issues


def check_cmt_in_briefcase(manifest_dir: Path) -> list[str]:
    """Flag Custom Metadata Types in Briefcase Builder definitions."""
    issues: list[str] = []
    for xml_file in find_files(manifest_dir, ".briefcaseDefinition-meta.xml"):
        content = read_text(xml_file)
        if CMT_OBJECT_NAME.search(content):
            issues.append(
                f"[CMT-PRIMING] {xml_file}: __mdt object in Briefcase Builder definition. "
                f"Custom Metadata Types cannot be primed via Briefcase Builder. "
                f"Cache CMT values in a Custom Object (primed via Briefcase Builder) "
                f"populated by an Apex wire adapter when online."
            )
    return issues


def check_lwc_action_on_layout(manifest_dir: Path) -> list[str]:
    """Warn if a LWC Quick Action is not found in any page layout."""
    issues: list[str] = []
    lwc_action_names: list[str] = []

    for qa_file in find_files(manifest_dir, ".quickAction-meta.xml"):
        content = read_text(qa_file)
        if LWC_ACTION_TYPE.search(content):
            # e.g. WorkOrder.Complete_Work.quickAction-meta.xml → Complete_Work
            stem = qa_file.name.replace(".quickAction-meta.xml", "")
            # The action name after the dot (e.g., "Complete_Work" from "WorkOrder.Complete_Work")
            action_name = stem.split(".")[-1] if "." in stem else stem
            lwc_action_names.append(action_name)

    layout_files = find_files(manifest_dir, ".layout-meta.xml")
    if not layout_files:
        return issues  # Cannot check without layout files present

    for action_name in lwc_action_names:
        found = any(action_name in read_text(lf) for lf in layout_files)
        if not found:
            issues.append(
                f"[OFFLINE-LAYOUT] LWC Quick Action '{action_name}' not found in any "
                f"page layout. For offline availability in FSL Mobile, the action MUST "
                f"be added to the object's main page layout — App Builder placement alone "
                f"is not sufficient."
            )
    return issues


def check_deep_link_size(manifest_dir: Path) -> list[str]:
    """Warn about long deep link URI strings that may approach the 1 MB limit."""
    issues: list[str] = []
    for js_file in find_files(manifest_dir, ".js"):
        content = read_text(js_file)
        for match in DEEP_LINK_URI.finditer(content):
            uri = match.group(0)
            size = len(uri.encode("utf-8"))
            if size > 900_000:
                issues.append(
                    f"[DEEP-LINK-SIZE] {js_file}: Deep link URI string is {size} bytes "
                    f"(FSL limit: 1 MB). Reduce payload by passing record IDs instead "
                    f"of full field values."
                )
    return issues


def check_permission_set_assignment(manifest_dir: Path) -> list[str]:
    """Info: remind that Enable Lightning SDK permission set must be assigned."""
    issues: list[str] = []
    lwc_action_found = any(
        LWC_ACTION_TYPE.search(read_text(qa))
        for qa in find_files(manifest_dir, ".quickAction-meta.xml")
    )
    if not lwc_action_found:
        return issues

    ps_files = find_files(manifest_dir, ".permissionset-meta.xml")
    sdk_ps_found = any(
        "EnableLightningSDK" in read_text(ps) or "Lightning_SDK" in read_text(ps)
        for ps in ps_files
    )
    if not sdk_ps_found:
        issues.append(
            "[PERMISSION-SET] LWC Quick Action found but 'Enable Lightning SDK for FSL "
            "Mobile' permission set not detected in metadata. Confirm it is assigned to "
            "all FSL Mobile users — it is NOT included in standard Field Service Mobile "
            "license assignments."
        )
    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def check_fsl_mobile_app_extensions(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_lwc_in_html5_extensions(manifest_dir))
    issues.extend(check_imperative_apex_offline(manifest_dir))
    issues.extend(check_cmt_in_briefcase(manifest_dir))
    issues.extend(check_lwc_action_on_layout(manifest_dir))
    issues.extend(check_deep_link_size(manifest_dir))
    issues.extend(check_permission_set_assignment(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for FSL Mobile App Extension issues. "
            "See skills/apex/fsl-mobile-app-extensions/references/gotchas.md for details."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_mobile_app_extensions(manifest_dir)

    if not issues:
        print("No FSL Mobile extension issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
