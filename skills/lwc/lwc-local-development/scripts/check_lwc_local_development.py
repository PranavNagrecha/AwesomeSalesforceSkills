#!/usr/bin/env python3
"""Live Preview (LWC Local Development) readiness checker.

Statically inspects a Salesforce source tree for the things that block or
surprise an `sf lightning dev component|app|site` session:

  1. No `sfdx-project.json`  -> the sf CLI has no project to preview.
  2. Aura component bundles   -> Live Preview is LWC-only; these can't be previewed.
  3. LWC bundles missing or with an unparseable `*.js-meta.xml`
                              -> the component won't resolve for preview/targets.
  4. LWC bundles whose `js-meta.xml` has `isExposed` false
                              -> informational: not selectable on Lightning targets.

Stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_local_development.py [--project-dir path]

Exit code 0 = no blocking issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# js-meta.xml uses the Metadata API namespace.
_META_NS = "{http://soap.sforce.com/2006/04/metadata}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a Salesforce project for LWC Live Preview readiness.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


def _has_sfdx_project(project_dir: Path) -> bool:
    if (project_dir / "sfdx-project.json").is_file():
        return True
    # Also accept it anywhere beneath the given root.
    return any(project_dir.rglob("sfdx-project.json"))


def _is_lwc_bundle(bundle: Path) -> bool:
    """An LWC bundle has a JS entry file matching the folder name."""
    return (bundle / f"{bundle.name}.js").is_file() or any(bundle.glob("*.js-meta.xml"))


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _check_lwc_meta(bundle: Path, issues: list[str]) -> None:
    metas = list(bundle.glob("*.js-meta.xml"))
    if not metas:
        issues.append(
            f"{bundle}: LWC bundle has no *.js-meta.xml — the component won't resolve for preview"
        )
        return
    meta = metas[0]
    try:
        root = ET.parse(meta).getroot()
    except (OSError, ET.ParseError) as exc:
        issues.append(f"{meta}: not valid XML ({exc})")
        return
    exposed = None
    for child in root:
        if _local(child.tag) == "isExposed":
            exposed = (child.text or "").strip().lower()
            break
    if exposed == "false":
        issues.append(
            f"{meta}: isExposed is false — component won't be selectable on Lightning targets "
            f"(single-component preview still works, but app/record-page context won't)"
        )


def check(project_dir: Path) -> list[str]:
    issues: list[str] = []
    if not project_dir.exists():
        return [f"Project directory not found: {project_dir}"]

    if not _has_sfdx_project(project_dir):
        issues.append(
            "No sfdx-project.json found — Live Preview requires an authenticated SFDX project. "
            "Run `sf project generate` or point --project-dir at the project root."
        )

    # Aura bundles: not previewable via Live Preview (LWC-only).
    aura_roots = [p for p in project_dir.rglob("aura") if p.is_dir()]
    for aura_root in aura_roots:
        for bundle in sorted(p for p in aura_root.iterdir() if p.is_dir()):
            issues.append(
                f"{bundle}: Aura component — Live Preview is LWC-only and cannot preview it; "
                f"deploy and test it in the org instead"
            )

    # LWC bundles: check for a valid js-meta.xml.
    lwc_roots = [p for p in project_dir.rglob("lwc") if p.is_dir()]
    found_lwc = False
    for lwc_root in lwc_roots:
        # Skip node_modules / jest scaffolding noise.
        if "node_modules" in lwc_root.parts:
            continue
        for bundle in sorted(p for p in lwc_root.iterdir() if p.is_dir()):
            if bundle.name.startswith("__"):  # __tests__, __mocks__
                continue
            if not _is_lwc_bundle(bundle):
                continue
            found_lwc = True
            _check_lwc_meta(bundle, issues)

    if not found_lwc and not aura_roots:
        issues.append(
            f"No LWC or Aura bundles found under {project_dir} — nothing to preview."
        )

    return issues


def main() -> int:
    args = parse_args()
    issues = check(Path(args.project_dir))
    if not issues:
        print("No issues found — project looks ready for Live Preview.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
