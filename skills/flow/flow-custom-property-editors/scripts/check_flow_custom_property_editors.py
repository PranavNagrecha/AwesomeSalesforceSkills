#!/usr/bin/env python3
"""Checker script for Flow Custom Property Editors skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FLOW_TARGET_MARKERS = ("lightning__FlowScreen", "lightning__FlowAction")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow Custom Property Editors configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_lwc_bundle(manifest_dir: Path, bundle_name: str) -> Path | None:
    for candidate in manifest_dir.rglob(bundle_name):
        if candidate.is_dir():
            return candidate
    return None


def check_flow_custom_property_editors(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for meta_path in sorted(manifest_dir.rglob("*.js-meta.xml")):
        text = meta_path.read_text(encoding="utf-8", errors="ignore")
        if not any(marker in text for marker in FLOW_TARGET_MARKERS):
            continue

        property_count = len(re.findall(r"<property\b", text))
        match = re.search(r"<configurationEditor>([^<]+)</configurationEditor>", text)
        if match:
            editor_ref = match.group(1).strip()
            bundle_name = editor_ref.split("/")[-1].split(":")[-1]
            bundle_dir = find_lwc_bundle(manifest_dir, bundle_name)
            if bundle_dir is None:
                issues.append(f"{meta_path}: configurationEditor `{editor_ref}` does not resolve to an LWC bundle in the manifest directory.")
                continue

            js_files = list(bundle_dir.glob("*.js"))
            if not js_files:
                issues.append(f"{meta_path}: configurationEditor bundle `{bundle_name}` has no JavaScript controller file.")
                continue

            js_text = js_files[0].read_text(encoding="utf-8", errors="ignore")
            if "configuration_editor_input_value_changed" not in js_text and "configuration_editor_generic_type_mapping_changed" not in js_text:
                issues.append(
                    f"{meta_path}: configurationEditor bundle `{bundle_name}` does not appear to dispatch documented Flow Builder change events."
                )
        elif property_count > 5:
            issues.append(
                f"{meta_path}: Flow target exposes {property_count} properties without a configurationEditor; review whether admins need a guided builder experience."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_flow_custom_property_editors(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
