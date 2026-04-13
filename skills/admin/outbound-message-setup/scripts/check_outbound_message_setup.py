#!/usr/bin/env python3
"""Checker script for Outbound Message Setup skill.

Checks Workflow Outbound Message metadata for common configuration issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_outbound_message_setup.py [--help]
    python3 check_outbound_message_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Workflow Outbound Message metadata for configuration issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_workflow_files(manifest_dir: Path) -> list[str]:
    """Check Workflow metadata for Outbound Message configuration issues."""
    issues: list[str] = []

    workflow_dir = manifest_dir / "workflows"
    if not workflow_dir.exists():
        return issues

    for workflow_file in workflow_dir.glob("*.workflow"):
        try:
            tree = ET.parse(workflow_file)
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            obj_name = workflow_file.stem

            # Check for Outbound Message actions
            for outbound_msg in root.findall(f".//{ns}outboundMessage"):
                msg_name_elem = outbound_msg.find(f"{ns}fullName")
                msg_name = msg_name_elem.text if msg_name_elem is not None else "unknown"

                endpoint_elem = outbound_msg.find(f"{ns}endpointUrl")
                if endpoint_elem is not None and endpoint_elem.text:
                    endpoint_url = endpoint_elem.text

                    # Check for HTTP (non-HTTPS) endpoints in production context
                    if endpoint_url.startswith("http://"):
                        issues.append(
                            f"Workflow '{obj_name}', Outbound Message '{msg_name}': "
                            f"Endpoint URL uses HTTP (not HTTPS): '{endpoint_url}'. "
                            "Production Outbound Messages should use HTTPS to encrypt the payload."
                        )

                    # Check for localhost or test URLs (potential sandbox-only config)
                    if "localhost" in endpoint_url or "127.0.0.1" in endpoint_url:
                        issues.append(
                            f"Workflow '{obj_name}', Outbound Message '{msg_name}': "
                            f"Endpoint URL appears to be a localhost URL: '{endpoint_url}'. "
                            "Verify this is not a sandbox-only configuration deployed to production."
                        )

                # Check for fields — warn if no fields are selected
                fields = outbound_msg.findall(f"{ns}fields")
                if not fields:
                    issues.append(
                        f"Workflow '{obj_name}', Outbound Message '{msg_name}': "
                        "No fields selected in the Outbound Message payload. "
                        "The payload will only include the record ID. "
                        "Consider selecting relevant fields for the external system."
                    )

        except (ET.ParseError, OSError):
            pass

    return issues


def check_outbound_message_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_workflow_files(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_outbound_message_setup(manifest_dir)

    if not issues:
        print("No Outbound Message configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
