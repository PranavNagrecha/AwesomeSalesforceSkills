#!/usr/bin/env python3
"""Checker script for OmniStudio Remote Actions skill.

Scans OmniScript metadata (JSON exports or XML) for common Remote Action
misconfigurations: missing JSON paths, risky invoke modes, and namespace issues
in referenced Apex classes.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_remote_actions.py [--help]
    python3 check_omnistudio_remote_actions.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check OmniStudio Remote Action configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_apex_classes(manifest_dir: Path) -> list[str]:
    """Check Apex classes implementing VlocityOpenInterface2 for common issues."""
    issues: list[str] = []
    cls_files = list(manifest_dir.rglob("*.cls"))

    for cls_file in cls_files:
        try:
            content = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only check files that implement VlocityOpenInterface2
        if "VlocityOpenInterface2" not in content:
            continue

        filename = cls_file.name

        # Check for missing namespace prefix
        if re.search(
            r"implements\s+VlocityOpenInterface2(?!\s*\{)",
            content,
        ) and not re.search(
            r"implements\s+(vlocity_cmt|omnistudio)\.VlocityOpenInterface2",
            content,
        ):
            issues.append(
                f"{filename}: implements VlocityOpenInterface2 without namespace prefix. "
                "Use omnistudio.VlocityOpenInterface2 (native) or "
                "vlocity_cmt.VlocityOpenInterface2 (managed package)."
            )

        # Check for public instead of global
        if re.search(r"public\s+class\s+\w+\s+implements", content):
            issues.append(
                f"{filename}: class is 'public' but VlocityOpenInterface2 "
                "implementations must be 'global'."
            )

        if re.search(r"public\s+Object\s+invokeMethod", content):
            issues.append(
                f"{filename}: invokeMethod is 'public' but must be 'global' "
                "for the OmniStudio framework to bind at runtime."
            )

        # Check for returning data instead of using outputMap
        invoke_match = re.search(
            r"invokeMethod\s*\([^)]*\)\s*\{(.*?)(?:^\s*\})",
            content,
            re.DOTALL | re.MULTILINE,
        )
        if invoke_match:
            method_body = invoke_match.group(1)
            # Look for return statements that return something other than null
            returns = re.findall(r"return\s+(?!null\b)(\w+)", method_body)
            if returns and "outputMap" not in method_body:
                issues.append(
                    f"{filename}: invokeMethod returns a value but does not populate "
                    "outputMap. The OmniStudio framework reads from outputMap, not "
                    "the return value."
                )

        # Check for hardcoded endpoints
        if re.search(r'setEndpoint\s*\(\s*[\'"]https?://', content):
            issues.append(
                f"{filename}: contains hardcoded HTTP endpoint. "
                "Use Named Credentials (callout:NamedCred) instead."
            )

        # Check for hardcoded auth headers
        if re.search(r'setHeader\s*\(\s*[\'"]Authorization[\'"]', content):
            issues.append(
                f"{filename}: sets Authorization header manually. "
                "Use Named Credentials to manage authentication."
            )

    return issues


def check_omniscript_json(manifest_dir: Path) -> list[str]:
    """Check exported OmniScript JSON for Remote Action misconfigurations."""
    issues: list[str] = []
    json_files = list(manifest_dir.rglob("*.json"))

    for json_file in json_files:
        try:
            content = json_file.read_text(encoding="utf-8", errors="replace")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError):
            continue

        # Look for OmniScript action elements in various export formats
        elements = []
        if isinstance(data, dict):
            elements = data.get("children", data.get("elements", []))
            if isinstance(elements, dict):
                elements = list(elements.values())
        elif isinstance(data, list):
            elements = data

        for elem in _flatten_elements(elements):
            if not isinstance(elem, dict):
                continue

            props = elem.get("propSetMap", elem.get("propertySet", {}))
            if not isinstance(props, dict):
                continue

            elem_type = props.get("Type", props.get("type", ""))
            elem_name = props.get("name", props.get("Name", json_file.name))

            # Check Remote Action and Integration Procedure action elements
            if elem_type not in (
                "Remote Action",
                "Integration Procedure Action",
                "Apex Remote Action",
                "REST Action",
                "DataRaptor Action",
            ):
                continue

            # Check for missing Send JSON Path
            send_path = props.get("sendJsonPath", props.get("SendJsonPath", ""))
            if not send_path or send_path.strip() == "":
                issues.append(
                    f"{json_file.name} [{elem_name}]: Send JSON Path is blank. "
                    "This sends the entire step node (including framework keys) "
                    "to the backend. Set an explicit path."
                )

            # Check for missing Response JSON Path
            resp_path = props.get("responseJsonPath", props.get("ResponseJsonPath", ""))
            if not resp_path or resp_path.strip() == "":
                issues.append(
                    f"{json_file.name} [{elem_name}]: Response JSON Path is blank. "
                    "This overwrites the entire step node with the response. "
                    "Set an explicit path to prevent sibling data loss."
                )

            # Check for Fire and Forget invoke mode
            invoke_mode = props.get("invokeMode", props.get("InvokeMode", ""))
            if invoke_mode and "fire" in invoke_mode.lower():
                issues.append(
                    f"{json_file.name} [{elem_name}]: Uses Fire and Forget invoke mode. "
                    "Verify no downstream step reads this action's output. "
                    "Data loss occurs if the user navigates before the response arrives."
                )

    return issues


def _flatten_elements(elements: list | dict) -> list:
    """Recursively flatten nested OmniScript element structures."""
    if isinstance(elements, dict):
        elements = [elements]
    if not isinstance(elements, list):
        return []

    result = []
    for elem in elements:
        if not isinstance(elem, dict):
            continue
        result.append(elem)
        children = elem.get("children", elem.get("elements", []))
        result.extend(_flatten_elements(children))
    return result


def check_omnistudio_remote_actions(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Apex classes for VlocityOpenInterface2 issues
    issues.extend(check_apex_classes(manifest_dir))

    # Check OmniScript JSON exports for action configuration issues
    issues.extend(check_omniscript_json(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_omnistudio_remote_actions(manifest_dir)

    if not issues:
        print("No Remote Action issues found.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for issue in issues:
        print(f"  ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
