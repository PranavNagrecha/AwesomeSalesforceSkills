#!/usr/bin/env python3
"""Checker script for the lwc-light-dom skill.

Scans a Salesforce project for Lightning Web Components that opt into light DOM
(`static renderMode = 'light'`) and flags common mistakes:

  1. No sibling `<name>.scoped.css` file -> component styles will bleed globally.
  2. `:host` / `:host-context` selectors inside the component's CSS -> invalid
     in light DOM.
  3. The project's `sfdx-project.json` declares any `packageDirectories[]` entry
     with `"type": "managed"` while light-DOM components exist anywhere in the
     tree -> Salesforce guidance warns against shipping light-DOM components in
     managed packages (style leak into consumer orgs).

Stdlib only. Findings are emitted with file paths and line numbers. Exit code
is 0 when nothing is found and 1 when any finding is reported.

Usage:
    python3 check_lwc_light_dom.py [--manifest-dir path/to/project]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable


RENDER_MODE_LIGHT_RE = re.compile(
    r"""static\s+renderMode\s*=\s*['"]light['"]""",
    re.IGNORECASE,
)
HOST_SELECTOR_RE = re.compile(r":host(?:-context)?\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Lightning Web Components using light DOM for common "
            "issues (missing *.scoped.css, :host selectors, managed-package "
            "conflicts)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current dir).",
    )
    return parser.parse_args()


def find_lwc_js_files(root: Path) -> list[Path]:
    """Return every `<bundle>/<bundle>.js` file under `lwc/` folders."""
    results: list[Path] = []
    for js_file in root.rglob("lwc/*/*.js"):
        # Skip test files, controllers, helpers unrelated to the bundle entry.
        if js_file.parent.name != js_file.stem:
            continue
        results.append(js_file)
    return results


def find_light_dom_lines(js_path: Path) -> list[tuple[int, str]]:
    """Return (line_number, line_text) pairs where light DOM is enabled."""
    hits: list[tuple[int, str]] = []
    try:
        text = js_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return hits
    for lineno, line in enumerate(text.splitlines(), start=1):
        if RENDER_MODE_LIGHT_RE.search(line):
            hits.append((lineno, line.strip()))
    return hits


def sibling(js_path: Path, suffix: str) -> Path:
    return js_path.with_name(js_path.stem + suffix)


def find_host_selectors(css_path: Path) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    if not css_path.exists():
        return hits
    try:
        text = css_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return hits
    for lineno, line in enumerate(text.splitlines(), start=1):
        if HOST_SELECTOR_RE.search(line):
            hits.append((lineno, line.strip()))
    return hits


def project_has_managed_package(root: Path) -> tuple[bool, Path | None]:
    """Return (is_managed, project_file) based on sfdx-project.json."""
    project_file = root / "sfdx-project.json"
    if not project_file.exists():
        # Try to find it one level down (monorepo shape).
        candidates = list(root.glob("*/sfdx-project.json"))
        if not candidates:
            return False, None
        project_file = candidates[0]
    try:
        data = json.loads(project_file.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return False, project_file
    for entry in data.get("packageDirectories", []) or []:
        if str(entry.get("type", "")).lower() == "managed":
            return True, project_file
    # Some projects put the flag at packageAliases or packaging section;
    # look for "packaging": "managed" as a secondary signal.
    if str(data.get("packaging", "")).lower() == "managed":
        return True, project_file
    return False, project_file


def format_finding(path: Path, lineno: int | None, message: str) -> str:
    if lineno is None:
        return f"{path}: {message}"
    return f"{path}:{lineno}: {message}"


def check(root: Path) -> list[str]:
    findings: list[str] = []

    if not root.exists():
        findings.append(f"Manifest directory not found: {root}")
        return findings

    js_files = find_lwc_js_files(root)
    light_bundles: list[Path] = []

    for js_file in js_files:
        light_hits = find_light_dom_lines(js_file)
        if not light_hits:
            continue
        light_bundles.append(js_file)

        bundle_dir = js_file.parent
        bundle_name = js_file.stem

        # Check 1: companion *.scoped.css file.
        scoped_css = bundle_dir / f"{bundle_name}.scoped.css"
        plain_css = bundle_dir / f"{bundle_name}.css"
        if not scoped_css.exists():
            for lineno, _ in light_hits:
                findings.append(
                    format_finding(
                        js_file,
                        lineno,
                        (
                            f"light DOM component has no sibling "
                            f"`{bundle_name}.scoped.css`; component styles "
                            f"will bleed globally. Rename `{bundle_name}.css` "
                            f"to `{bundle_name}.scoped.css` or add one."
                        ),
                    )
                )
                break  # one finding per bundle is enough

        # Check 2: `:host` / `:host-context` in the component's CSS files.
        for css_path in (scoped_css, plain_css):
            for lineno, text in find_host_selectors(css_path):
                findings.append(
                    format_finding(
                        css_path,
                        lineno,
                        (
                            f":host selector is invalid in a light DOM "
                            f"component (`{bundle_name}`). Replace with a "
                            f"wrapper element and a class selector. Found: "
                            f"`{text}`"
                        ),
                    )
                )

    # Check 3: managed-package distribution with light DOM anywhere.
    if light_bundles:
        is_managed, project_file = project_has_managed_package(root)
        if is_managed:
            for js_file in light_bundles:
                findings.append(
                    format_finding(
                        js_file,
                        None,
                        (
                            f"light DOM component in a managed-package "
                            f"project (see `{project_file}`). Salesforce "
                            f"recommends against shipping light-DOM "
                            f"components through managed packages; styles "
                            f"leak into consumer orgs."
                        ),
                    )
                )

    return findings


def emit(findings: Iterable[str]) -> int:
    findings = list(findings)
    if not findings:
        print("No issues found.")
        return 0
    for issue in findings:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir).resolve()
    return emit(check(root))


if __name__ == "__main__":
    sys.exit(main())
