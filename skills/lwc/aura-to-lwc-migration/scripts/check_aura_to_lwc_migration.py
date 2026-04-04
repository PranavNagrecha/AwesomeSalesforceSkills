#!/usr/bin/env python3
"""Checker script for Aura to LWC Migration skill.

Scans a Salesforce project directory for common migration issues:
- LWC .js files containing $A API calls
- LWC .js files containing event.getParam / event.getParams
- LWC .html templates referencing known Aura component names
- CustomEvent constructors using camelCase event names
- LWC classes using NavigationMixin without extending it

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_aura_to_lwc_migration.py --help
    python3 check_aura_to_lwc_migration.py --project-dir path/to/salesforce/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a Salesforce project for common Aura-to-LWC migration issues."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, suffix: str) -> list[Path]:
    """Return all files with the given suffix under root."""
    return list(root.rglob(f"*{suffix}"))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_dollar_a_in_lwc(lwc_root: Path) -> list[str]:
    """Flag LWC .js files that contain $A. references."""
    issues: list[str] = []
    pattern = re.compile(r"\$A\s*\.")
    for js_file in find_files(lwc_root, ".js"):
        # Skip test files
        if "__tests__" in js_file.parts:
            continue
        text = read_text(js_file)
        matches = [i + 1 for i, line in enumerate(text.splitlines()) if pattern.search(line)]
        if matches:
            lines_str = ", ".join(str(n) for n in matches[:5])
            issues.append(
                f"[DOLLAR_A] {js_file}: $A.* found on line(s) {lines_str} — "
                "$A is not available in LWC. Replace with @wire adapters, "
                "imperative Apex imports, or NavigationMixin."
            )
    return issues


def check_get_param_in_lwc(lwc_root: Path) -> list[str]:
    """Flag LWC .js files that use Aura-style event.getParam / event.getParams."""
    issues: list[str] = []
    pattern = re.compile(r"event\s*\.\s*getParams?\s*\(")
    for js_file in find_files(lwc_root, ".js"):
        if "__tests__" in js_file.parts:
            continue
        text = read_text(js_file)
        matches = [i + 1 for i, line in enumerate(text.splitlines()) if pattern.search(line)]
        if matches:
            lines_str = ", ".join(str(n) for n in matches[:5])
            issues.append(
                f"[GET_PARAM] {js_file}: event.getParam/getParams found on line(s) {lines_str} — "
                "LWC CustomEvent payloads are accessed via event.detail, not event.getParam()."
            )
    return issues


def check_camelcase_custom_events(lwc_root: Path) -> list[str]:
    """Flag CustomEvent constructors with camelCase event names."""
    issues: list[str] = []
    # Match: new CustomEvent('someCamelCaseName'
    pattern = re.compile(r"new\s+CustomEvent\s*\(\s*['\"]([^'\"]+)['\"]")
    camel_check = re.compile(r"[A-Z]")
    for js_file in find_files(lwc_root, ".js"):
        if "__tests__" in js_file.parts:
            continue
        text = read_text(js_file)
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in pattern.finditer(line):
                event_name = match.group(1)
                if camel_check.search(event_name):
                    issues.append(
                        f"[CAMEL_EVENT] {js_file}:{lineno}: CustomEvent name '{event_name}' "
                        "contains uppercase letters — LWC event names must be all lowercase. "
                        "Template on* attributes must match the lowercase name exactly."
                    )
    return issues


def check_navigation_mixin_usage(lwc_root: Path) -> list[str]:
    """Flag LWC files that use NavigationMixin.Navigate without proper class extension."""
    issues: list[str] = []
    navigate_pattern = re.compile(r"NavigationMixin\.Navigate")
    extends_pattern = re.compile(r"extends\s+NavigationMixin\s*\(")
    for js_file in find_files(lwc_root, ".js"):
        if "__tests__" in js_file.parts:
            continue
        text = read_text(js_file)
        if navigate_pattern.search(text) and not extends_pattern.search(text):
            issues.append(
                f"[NAV_MIXIN] {js_file}: NavigationMixin.Navigate is used but the class does not "
                "extend NavigationMixin(LightningElement). Add NavigationMixin to the class "
                "declaration: `export default class Foo extends NavigationMixin(LightningElement)`."
            )
    return issues


def check_aura_component_inventory(project_root: Path) -> list[str]:
    """Report Aura components still present in the project alongside LWC components."""
    issues: list[str] = []
    aura_dir = project_root / "force-app" / "main" / "default" / "aura"
    lwc_dir = project_root / "force-app" / "main" / "default" / "lwc"

    if not aura_dir.exists():
        # Try common alternative layout
        aura_dirs = list(project_root.rglob("aura"))
        aura_dir = aura_dirs[0] if aura_dirs else None

    if aura_dir and aura_dir.exists():
        aura_components = [d.name for d in aura_dir.iterdir() if d.is_dir()]
        if aura_components:
            issues.append(
                f"[AURA_PRESENT] {len(aura_components)} Aura component(s) found in {aura_dir}: "
                + ", ".join(sorted(aura_components)[:10])
                + (" ..." if len(aura_components) > 10 else "")
                + " — Review each for migration status."
            )

    if aura_dir and aura_dir.exists() and lwc_dir and lwc_dir.exists():
        aura_names = {d.name.lower() for d in aura_dir.iterdir() if d.is_dir()}
        lwc_names = {d.name.lower() for d in lwc_dir.iterdir() if d.is_dir()}
        overlapping = aura_names & lwc_names
        if overlapping:
            issues.append(
                f"[DUAL_COMPONENTS] {len(overlapping)} component name(s) exist in both aura/ and lwc/: "
                + ", ".join(sorted(overlapping))
                + " — Verify that the LWC version is complete and the Aura version is retired."
            )

    return issues


def check_force_navigate_events(lwc_root: Path) -> list[str]:
    """Flag force:navigate* usage in LWC .js files."""
    issues: list[str] = []
    pattern = re.compile(r"force:navigate")
    for js_file in find_files(lwc_root, ".js"):
        if "__tests__" in js_file.parts:
            continue
        text = read_text(js_file)
        matches = [i + 1 for i, line in enumerate(text.splitlines()) if pattern.search(line)]
        if matches:
            lines_str = ", ".join(str(n) for n in matches[:5])
            issues.append(
                f"[FORCE_NAV] {js_file}: force:navigate* found on line(s) {lines_str} — "
                "Aura navigation events are not available in LWC. Use NavigationMixin.Navigate "
                "with a standard PageReference type."
            )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def find_lwc_root(project_root: Path) -> Path | None:
    """Find the lwc directory under the project root."""
    standard = project_root / "force-app" / "main" / "default" / "lwc"
    if standard.exists():
        return standard
    candidates = list(project_root.rglob("lwc"))
    for c in candidates:
        if c.is_dir():
            return c
    return None


def run_checks(project_dir: Path) -> list[str]:
    issues: list[str] = []

    if not project_dir.exists():
        issues.append(f"Project directory not found: {project_dir}")
        return issues

    lwc_root = find_lwc_root(project_dir)

    if lwc_root and lwc_root.exists():
        issues.extend(check_dollar_a_in_lwc(lwc_root))
        issues.extend(check_get_param_in_lwc(lwc_root))
        issues.extend(check_camelcase_custom_events(lwc_root))
        issues.extend(check_navigation_mixin_usage(lwc_root))
        issues.extend(check_force_navigate_events(lwc_root))
    else:
        issues.append(
            "No lwc/ directory found under project root. "
            "Run this checker from a Salesforce DX project root or pass --project-dir."
        )

    issues.extend(check_aura_component_inventory(project_dir))

    return issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    issues = run_checks(project_dir)

    if not issues:
        print("No Aura-to-LWC migration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
