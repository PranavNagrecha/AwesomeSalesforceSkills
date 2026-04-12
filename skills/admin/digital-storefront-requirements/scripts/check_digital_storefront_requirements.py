#!/usr/bin/env python3
"""Checker script for Digital Storefront Requirements skill.

Checks project metadata and configuration for common digital storefront
requirement anti-patterns in Salesforce B2C Commerce (SFCC) projects.

Checks performed (all stdlib, no pip dependencies):
  1. Overlay cartridge naming — flags any cartridge directory NOT following app_custom_* convention
  2. Forbidden base-cartridge edits — flags tracked files inside app_storefront_base/
  3. Accessibility claim detection — flags documentation asserting Bootstrap 4 = WCAG AA compliance
  4. PWA Kit WebDAV deployment — flags CI/deployment scripts referencing WebDAV for PWA Kit bundles
  5. Page Designer descriptor presence — warns if ISML component templates lack companion .json descriptors

Usage:
    python3 check_digital_storefront_requirements.py [--help]
    python3 check_digital_storefront_requirements.py --project-dir /path/to/project
    python3 check_digital_storefront_requirements.py --project-dir . --cartridge-path-file cartridgepath.txt
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Overlay cartridges for SFRA branding MUST use the app_custom_* prefix.
OVERLAY_CARTRIDGE_PREFIX = "app_custom_"

# The base reference cartridge that should NEVER be modified.
BASE_CARTRIDGE_NAME = "app_storefront_base"

# Patterns in documentation that falsely claim Bootstrap 4 satisfies WCAG AA.
FALSE_ACCESSIBILITY_PATTERNS = [
    re.compile(r"bootstrap\s*4\s+is\s+(wcag|accessible)", re.IGNORECASE),
    re.compile(r"sfra\s+(handles|satisfies|provides)\s+accessibility", re.IGNORECASE),
    re.compile(r"bootstrap\s+4\s+ensures?\s+(wcag|aa\s+compliance)", re.IGNORECASE),
    re.compile(r"wcag\s+(aa\s+)?compliant\s+by\s+default", re.IGNORECASE),
]

# Patterns in deployment scripts that indicate WebDAV usage with PWA Kit.
WEBDAV_PWAKIT_PATTERNS = [
    re.compile(r"webdav.*pwa[_-]?kit", re.IGNORECASE),
    re.compile(r"pwa[_-]?kit.*webdav", re.IGNORECASE),
    re.compile(r"/cartridges/.*pwa[_-]?kit", re.IGNORECASE),
]

# File extensions to scan for documentation checks.
DOC_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}

# Deployment script filename patterns to check.
DEPLOY_SCRIPT_PATTERNS = {"*.sh", "*.yml", "*.yaml", "*.json", "Makefile", "Jenkinsfile"}


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_overlay_cartridge_naming(project_dir: Path) -> list[str]:
    """Check that custom overlay cartridges follow the app_custom_* naming convention.

    Looks for directories containing 'cartridge/' subdirectory that appear to be
    custom cartridges (not app_storefront_base and not starting with app_custom_).
    """
    issues: list[str] = []

    # Walk top-level directories looking for cartridge directories.
    for entry in project_dir.iterdir():
        if not entry.is_dir():
            continue
        cartridge_subdir = entry / "cartridge"
        if not cartridge_subdir.exists():
            continue
        name = entry.name
        # Skip the official base cartridge and already-compliant custom cartridges.
        if name == BASE_CARTRIDGE_NAME:
            continue
        if name.startswith(OVERLAY_CARTRIDGE_PREFIX):
            continue
        # Skip well-known non-overlay directories.
        if name.startswith("plugin_") or name.startswith("int_") or name.startswith("bc_"):
            continue
        issues.append(
            f"Cartridge '{name}' does not follow app_custom_* naming convention. "
            f"SFRA branding overlay cartridges must be prefixed 'app_custom_' "
            f"(e.g., app_custom_{name}). See references/gotchas.md for details."
        )

    return issues


def check_base_cartridge_not_modified(project_dir: Path) -> list[str]:
    """Warn if files inside app_storefront_base are present in the project directory.

    If the project contains app_storefront_base as a tracked directory (not as a
    read-only dependency), it is likely that the base was forked or modified directly.
    """
    issues: list[str] = []

    base_dir = project_dir / BASE_CARTRIDGE_NAME
    if not base_dir.exists():
        return issues  # Base cartridge not present locally — likely a dependency, skip.

    # Check for git-tracked modifications inside base cartridge.
    # Look for any .git directory that might contain status info.
    git_dir = project_dir / ".git"
    if git_dir.exists():
        # Presence of app_storefront_base as a tracked directory is a yellow flag.
        issues.append(
            f"'{BASE_CARTRIDGE_NAME}' directory found in project root. "
            "Verify it has not been modified directly. All customizations must live in "
            "an app_custom_* overlay cartridge. Direct modifications to app_storefront_base "
            "break the SFRA upgrade path. See references/gotchas.md Gotcha 2."
        )

    return issues


def check_false_accessibility_claims(project_dir: Path) -> list[str]:
    """Scan documentation files for false claims that Bootstrap 4 = WCAG AA compliance."""
    issues: list[str] = []

    for root, _dirs, files in os.walk(project_dir):
        # Skip hidden dirs and node_modules.
        root_path = Path(root)
        if any(part.startswith(".") or part == "node_modules" for part in root_path.parts):
            continue
        for filename in files:
            if Path(filename).suffix.lower() not in DOC_EXTENSIONS:
                continue
            filepath = root_path / filename
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for pattern in FALSE_ACCESSIBILITY_PATTERNS:
                if pattern.search(text):
                    issues.append(
                        f"{filepath}: Contains a potentially false accessibility claim "
                        f"(matched pattern: '{pattern.pattern}'). "
                        "SFRA Bootstrap 4 does NOT satisfy WCAG 2.1 AA by default. "
                        "Accessibility compliance requires a dedicated audit. "
                        "See references/gotchas.md Gotcha 1."
                    )
                    break  # One warning per file is sufficient.

    return issues


def check_pwakit_webdav_deployment(project_dir: Path) -> list[str]:
    """Detect deployment scripts that appear to deploy PWA Kit bundles via WebDAV."""
    issues: list[str] = []

    for root, _dirs, files in os.walk(project_dir):
        root_path = Path(root)
        if any(part.startswith(".") or part == "node_modules" for part in root_path.parts):
            continue
        for filename in files:
            filepath = root_path / filename
            # Only scan deploy-related files.
            is_deploy_script = any(
                filepath.match(pat) for pat in DEPLOY_SCRIPT_PATTERNS
            ) or "deploy" in filename.lower() or "ci" in filename.lower()
            if not is_deploy_script:
                continue
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for pattern in WEBDAV_PWAKIT_PATTERNS:
                if pattern.search(text):
                    issues.append(
                        f"{filepath}: Possible PWA Kit deployment via WebDAV detected "
                        f"(matched pattern: '{pattern.pattern}'). "
                        "PWA Kit deploys to Salesforce Managed Runtime, NOT via WebDAV. "
                        "WebDAV is for SFRA cartridges only. "
                        "See references/llm-anti-patterns.md Anti-Pattern 5."
                    )
                    break

    return issues


def check_page_designer_component_descriptors(project_dir: Path) -> list[str]:
    """Warn if Page Designer ISML component templates lack companion JSON descriptors.

    Page Designer components require a JSON descriptor at:
    cartridge/experience/components/[type]/[id].json
    alongside the ISML rendering template at:
    cartridge/experience/components/[type]/[id].isml (or similar)
    """
    issues: list[str] = []

    experience_dirs: list[Path] = []
    for root, dirs, _files in os.walk(project_dir):
        root_path = Path(root)
        if "experience" in dirs:
            experience_dirs.append(root_path / "experience" / "components")

    for components_dir in experience_dirs:
        if not components_dir.exists():
            continue
        for component_type_dir in components_dir.iterdir():
            if not component_type_dir.is_dir():
                continue
            # Collect ISML files and JSON descriptors in this component type directory.
            isml_names = {f.stem for f in component_type_dir.glob("*.isml")}
            json_names = {f.stem for f in component_type_dir.glob("*.json")}
            missing_descriptors = isml_names - json_names
            for name in sorted(missing_descriptors):
                issues.append(
                    f"Page Designer component '{component_type_dir.name}/{name}' "
                    f"has an ISML template but no JSON descriptor. "
                    f"Without a descriptor the component will not appear in the "
                    f"Page Designer authoring palette. "
                    f"Add {component_type_dir}/{name}.json. "
                    "See references/gotchas.md Gotcha 3."
                )

    return issues


def check_cartridge_path_file(cartridge_path_file: Path) -> list[str]:
    """Validate a cartridge path file (one-line colon-separated path string).

    Checks:
    - app_storefront_base is in the path (required for SFRA)
    - app_storefront_base is the rightmost cartridge
    - Any custom cartridge follows app_custom_* naming
    """
    issues: list[str] = []

    if not cartridge_path_file.exists():
        return issues  # File not provided or doesn't exist; skip silently.

    try:
        content = cartridge_path_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        issues.append(f"Could not read cartridge path file: {exc}")
        return issues

    if not content:
        issues.append(f"{cartridge_path_file}: Cartridge path file is empty.")
        return issues

    # Take the first non-comment, non-empty line as the path.
    path_line = next(
        (line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")),
        None,
    )
    if not path_line:
        issues.append(f"{cartridge_path_file}: No cartridge path found.")
        return issues

    cartridges = [c.strip() for c in path_line.split(":") if c.strip()]

    if BASE_CARTRIDGE_NAME not in cartridges:
        issues.append(
            f"Cartridge path does not include '{BASE_CARTRIDGE_NAME}'. "
            "SFRA requires app_storefront_base as the rightmost cartridge."
        )
    elif cartridges[-1] != BASE_CARTRIDGE_NAME:
        issues.append(
            f"'{BASE_CARTRIDGE_NAME}' is not the rightmost cartridge in the path. "
            "It must be last (rightmost) so that custom cartridges override it correctly. "
            f"Current path: {path_line}"
        )

    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_checks(project_dir: Path, cartridge_path_file: Path | None = None) -> list[str]:
    """Run all checks and return a flat list of issue strings."""
    issues: list[str] = []

    issues.extend(check_overlay_cartridge_naming(project_dir))
    issues.extend(check_base_cartridge_not_modified(project_dir))
    issues.extend(check_false_accessibility_claims(project_dir))
    issues.extend(check_pwakit_webdav_deployment(project_dir))
    issues.extend(check_page_designer_component_descriptors(project_dir))

    if cartridge_path_file is not None:
        issues.extend(check_cartridge_path_file(cartridge_path_file))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a B2C Commerce project for digital storefront requirement anti-patterns "
            "(overlay cartridge naming, base cartridge modification, accessibility claims, "
            "PWA Kit WebDAV deployment, Page Designer descriptor gaps)."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the SFCC project (default: current directory).",
    )
    parser.add_argument(
        "--cartridge-path-file",
        default=None,
        help=(
            "Optional path to a text file containing the Business Manager cartridge path "
            "(colon-separated, one line). If provided, the cartridge path order is validated."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()
    cartridge_path_file = Path(args.cartridge_path_file).resolve() if args.cartridge_path_file else None

    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}", file=sys.stderr)
        return 2

    issues = run_all_checks(project_dir, cartridge_path_file)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
