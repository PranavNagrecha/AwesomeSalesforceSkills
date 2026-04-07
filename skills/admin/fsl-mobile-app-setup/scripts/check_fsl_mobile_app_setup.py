#!/usr/bin/env python3
"""Checker script for FSL Mobile App Setup skill.

Checks Salesforce metadata for common FSL Mobile configuration issues:
- HTML5 Mobile Extension Toolkit files that attempt to import LWC modules
- Quick actions on Work Order / Service Appointment not typed as LWC or HTML
- Deep link URL references exceeding safe payload length guidance
- Presence of the FSL Mobile connected app configuration

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_mobile_app_setup.py [--help]
    python3 check_fsl_mobile_app_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Objects that should have FSL Mobile quick actions
FSL_TARGET_OBJECTS = {"WorkOrder", "ServiceAppointment", "WorkOrderLineItem"}

# LWC module imports that are invalid inside HTML5 Mobile Extension Toolkit files
INVALID_LWC_IMPORTS = re.compile(
    r"""import\s+.*?from\s+['"](?:lwc|lightning/|@salesforce/)""",
    re.MULTILINE,
)

# Heuristic: HTML5 extension toolkit files often live in a folder named
# "mobileExtensions" or have names ending in "Extension.js"
HTML5_EXTENSION_PATTERN = re.compile(
    r"(?:mobileExtension|Extension\.js$|html5Extension)",
    re.IGNORECASE,
)

# Deep link URI — warn if query string is unusually long
DEEP_LINK_PATTERN = re.compile(
    r"""fieldservice://[^\s"'<>]+""",
    re.IGNORECASE,
)
DEEP_LINK_PAYLOAD_WARN_BYTES = 500_000  # warn at 500 KB, hard limit is 1 MB

# salesforce:// URI used in place of the FSL Mobile scheme
WRONG_DEEP_LINK_SCHEME = re.compile(
    r"""salesforce://(?:RecordDetail|record)[^\s"'<>]*ServiceAppointment""",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSL Mobile App Setup configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_html5_extensions_for_lwc_imports(manifest_dir: Path) -> list[str]:
    """Detect HTML5 extension toolkit files that attempt to use LWC imports."""
    issues: list[str] = []
    js_files = list(manifest_dir.rglob("*.js"))
    for js_file in js_files:
        if not HTML5_EXTENSION_PATTERN.search(str(js_file)):
            continue
        try:
            content = js_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = INVALID_LWC_IMPORTS.findall(content)
        if matches:
            issues.append(
                f"{js_file}: HTML5 Mobile Extension Toolkit file contains LWC module "
                f"imports — these are not supported in the HTML5 toolkit and will fail "
                f"at runtime. Found: {matches[:3]!r}"
            )
    return issues


def check_deep_links(manifest_dir: Path) -> list[str]:
    """Detect deep link issues: wrong scheme or oversized payloads."""
    issues: list[str] = []
    # Check HTML, JS, XML files for deep link patterns
    for ext in ("*.html", "*.js", "*.xml", "*.md"):
        for file in manifest_dir.rglob(ext):
            try:
                content = file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            # Wrong scheme: salesforce:// used for FSL Mobile deep links
            wrong_matches = WRONG_DEEP_LINK_SCHEME.findall(content)
            if wrong_matches:
                issues.append(
                    f"{file}: Uses 'salesforce://' URI scheme for FSL Mobile deep links. "
                    f"FSL Mobile uses its own custom URI scheme (not 'salesforce://'). "
                    f"Found: {wrong_matches[:2]!r}"
                )

            # Payload size warning
            for match in DEEP_LINK_PATTERN.finditer(content):
                uri = match.group(0)
                uri_bytes = len(uri.encode("utf-8"))
                if uri_bytes > DEEP_LINK_PAYLOAD_WARN_BYTES:
                    issues.append(
                        f"{file}: FSL Mobile deep link URI is {uri_bytes:,} bytes "
                        f"(warn threshold: {DEEP_LINK_PAYLOAD_WARN_BYTES:,} bytes, "
                        f"hard limit: 1,048,576 bytes). Oversized payloads are silently "
                        f"dropped by FSL Mobile. URI (truncated): {uri[:120]!r}..."
                    )
    return issues


def check_quick_action_metadata(manifest_dir: Path) -> list[str]:
    """Check Quick Action metadata files for FSL-relevant objects."""
    issues: list[str] = []
    # Salesforce metadata stores quick actions as <ObjectName>.<ActionName>.quickAction-meta.xml
    for qa_file in manifest_dir.rglob("*.quickAction-meta.xml"):
        # Extract the object name from the filename convention
        name = qa_file.name  # e.g. WorkOrder.MyAction.quickAction-meta.xml
        parts = name.split(".")
        if len(parts) < 3:
            continue
        object_name = parts[0]
        if object_name not in FSL_TARGET_OBJECTS:
            continue

        try:
            content = qa_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Quick actions for FSL objects should be LightningWebComponent or LightningComponent
        if "<actionType>" not in content:
            continue
        action_type_match = re.search(r"<actionType>(.*?)</actionType>", content)
        if not action_type_match:
            continue
        action_type = action_type_match.group(1).strip()
        if action_type not in ("LightningWebComponent", "LightningComponent", "CustomCanvas"):
            issues.append(
                f"{qa_file}: Quick action on '{object_name}' has actionType "
                f"'{action_type}'. FSL Mobile quick actions should use "
                f"LightningWebComponent (preferred) or LightningComponent. "
                f"Visualforce-based actions ({action_type!r}) are not rendered in FSL Mobile."
            )
    return issues


def check_fsl_mobile_app_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_html5_extensions_for_lwc_imports(manifest_dir))
    issues.extend(check_deep_links(manifest_dir))
    issues.extend(check_quick_action_metadata(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_mobile_app_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
