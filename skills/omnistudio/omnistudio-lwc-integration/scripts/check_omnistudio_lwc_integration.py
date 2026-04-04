#!/usr/bin/env python3
"""Checker script for OmniStudio LWC Integration skill (alias entry point).

This script is the scaffold-generated entry point. The full implementation
lives in check_omnistudio_lwc.py in the same directory.

Run check_omnistudio_lwc.py directly for the complete namespace, seed data,
and Integration Procedure checks.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_lwc_integration.py [--help]
    python3 check_omnistudio_lwc_integration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check OmniStudio LWC Integration configuration and metadata for common issues. "
            "Delegates to check_omnistudio_lwc.py for the full implementation."
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

    # Delegate to the full implementation in check_omnistudio_lwc.py
    impl_path = Path(__file__).parent / "check_omnistudio_lwc.py"
    spec = importlib.util.spec_from_file_location("check_omnistudio_lwc", impl_path)
    if spec is None or spec.loader is None:
        print("ERROR: Could not load check_omnistudio_lwc.py — run it directly.")
        return 1

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    from pathlib import Path as _Path
    manifest_dir = _Path(args.manifest_dir)
    issues = module.check_omnistudio_lwc(manifest_dir)

    if not issues:
        print("No OmniStudio LWC integration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
