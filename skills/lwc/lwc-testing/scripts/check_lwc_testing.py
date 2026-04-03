#!/usr/bin/env python3
"""Check LWC project structure for common Jest testing gaps."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


APEX_IMPORT_RE = re.compile(r"""from\s+['"]@salesforce/apex/[^'"]+['"]""")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC Jest setup and component test coverage smells.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def load_package_json(manifest_dir: Path) -> dict | None:
    package_json = manifest_dir / "package.json"
    if not package_json.exists():
        return None
    try:
        return json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def component_bundle_dirs(manifest_dir: Path) -> list[Path]:
    bundles: list[Path] = []
    for meta_path in sorted(manifest_dir.rglob("*.js-meta.xml")):
        bundle_dir = meta_path.parent
        if (bundle_dir / f"{bundle_dir.name}.js").exists() or (bundle_dir / f"{bundle_dir.name}.html").exists():
            bundles.append(bundle_dir)
    return bundles


def check_lwc_testing(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    package = load_package_json(manifest_dir)
    if package is None:
        issues.append(f"{manifest_dir}: package.json not found; verify that the project includes Jest configuration for LWC.")
    else:
        dependencies = {}
        dependencies.update(package.get("dependencies", {}))
        dependencies.update(package.get("devDependencies", {}))
        scripts = package.get("scripts", {})

        if "@salesforce/sfdx-lwc-jest" not in dependencies:
            issues.append("package.json: missing `@salesforce/sfdx-lwc-jest`; LWC unit-test tooling is not declared.")

        if "test:unit" not in scripts and "test" not in scripts:
            issues.append("package.json: missing a Jest-oriented test script such as `test:unit`.")

    for bundle_dir in component_bundle_dirs(manifest_dir):
        tests_dir = bundle_dir / "__tests__"
        test_files = sorted(tests_dir.glob("*.test.js")) + sorted(tests_dir.glob("*.spec.js"))
        if not test_files:
            issues.append(f"{bundle_dir}: no Jest test file found for component bundle.")
            continue

        for test_file in test_files:
            text = test_file.read_text(encoding="utf-8", errors="ignore")
            if "createElement(" not in text:
                issues.append(f"{test_file}: test file does not appear to render an LWC with `createElement()`.")
            if "document.body.appendChild" in text and "afterEach" not in text:
                issues.append(f"{test_file}: appends elements to `document.body` without an `afterEach` cleanup block.")
            if APEX_IMPORT_RE.search(text) and "jest.mock(" not in text and "registerApexTestWireAdapter(" not in text:
                issues.append(
                    f"{test_file}: imports Apex but has no obvious imperative mock or Apex wire adapter registration."
                )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_lwc_testing(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
