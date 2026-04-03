#!/usr/bin/env python3
"""Check Flow metadata for obvious gaps in test companion assets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


FLOW_SUFFIX = ".flow-meta.xml"
FLOW_TEST_SUFFIXES = (".flowtest-meta.xml", ".flowtest", ".flowtest-meta", ".flowtest-meta.XML", ".flowTest-meta.xml")
RISKY_MARKERS = ("<recordCreates>", "<recordUpdates>", "<recordDeletes>", "<actionCalls>", "<subflows>", "<screens>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether flows have nearby test companion assets or likely missing coverage.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or source tree (default: current directory).",
    )
    return parser.parse_args()


def flow_base_name(path: Path) -> str:
    name = path.name
    return name[:-len(FLOW_SUFFIX)].lower() if name.endswith(FLOW_SUFFIX) else path.stem.lower()


def looks_like_flow_test(path: Path) -> bool:
    lower_name = path.name.lower()
    return "flowtest" in lower_name or "flowtests" in (part.lower() for part in path.parts)


def test_base_name(path: Path) -> str:
    lower_name = path.name.lower()
    for suffix in FLOW_TEST_SUFFIXES:
        if lower_name.endswith(suffix.lower()):
            return lower_name[:-len(suffix.lower())]
    return path.stem.lower()


def check_flow_testing(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    flow_files = sorted(manifest_dir.rglob(f"*{FLOW_SUFFIX}"))
    test_files = [path for path in manifest_dir.rglob("*") if path.is_file() and looks_like_flow_test(path)]
    test_bases = {test_base_name(path): path for path in test_files}

    for flow_path in flow_files:
        text = flow_path.read_text(encoding="utf-8", errors="ignore")
        base = flow_base_name(flow_path)
        matching_tests = [path for test_base, path in test_bases.items() if base in test_base or test_base in base]
        high_risk = any(marker in text for marker in RISKY_MARKERS)

        if high_risk and not matching_tests:
            issues.append(
                f"{flow_path}: flow appears to have branching, mutation, or screen behavior but no obvious FlowTest companion file was found."
            )
            continue

        if ("<faultConnector>" in text or "<screens>" in text) and matching_tests:
            for test_path in matching_tests:
                test_text = test_path.read_text(encoding="utf-8", errors="ignore").lower()
                if "fault" not in test_text and "error" not in test_text and "exception" not in test_text:
                    issues.append(
                        f"{test_path}: matching test asset found for `{flow_path.name}`, but no obvious fault or error assertions were detected; review negative-path coverage."
                    )
                    break

    return issues


def main() -> int:
    args = parse_args()
    issues = check_flow_testing(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
