#!/usr/bin/env python3
"""Checker for Salesforce Multi-Framework UI bundles (UIBundle metadata).

Validates a source-format metadata tree for the common mistakes documented in
references/gotchas.md and references/llm-anti-patterns.md. Stdlib only — no pip deps.

Usage:
    python3 check_multi_framework_ui_bundles.py [--manifest-dir path]

It looks for `uiBundles/<app>/` folders and their `.uibundle-meta.xml` descriptors,
plus any `package.xml` referencing UIBundle, and reports concrete, actionable issues.
Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REQUIRED_FIELDS = ("masterLabel", "version", "isActive")
VALID_TARGETS = {"AppLauncher", "CustomApplication", "Experience"}
DEPRECATED_TARGETS = {"AppLauncher"}  # deprecated in API v67.0 — use CustomApplication
MAX_BUNDLE_FILES = 2500              # documented UIBundle file cap
FILE_COUNT_WARN_RATIO = 0.9          # warn when a bundle nears the cap
MIN_API_VERSION = 66.0               # UIBundle available from API v66.0
CUSTOM_APP_TARGET_MIN_API = 67.0     # CustomApplication target available from v67.0
FORBIDDEN_DIR_NAMES = {"node_modules", ".git"}
SECRETY_FILE_RE = re.compile(r"^\.env(\..+)?$")
TOKEN_SMELL_RE = re.compile(
    r"(refresh_token|client_secret|Authorization:\s*Bearer|jsforce)", re.IGNORECASE
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check UIBundle (Salesforce Multi-Framework) metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source metadata (looks for uiBundles/ folders anywhere beneath it).",
    )
    return parser.parse_args()


def _local_name(tag: str) -> str:
    """Strip an XML namespace from a tag name."""
    return tag.rsplit("}", 1)[-1]


def _parse_xml(path: Path) -> tuple[ET.Element | None, str | None]:
    try:
        return ET.parse(path).getroot(), None
    except (OSError, ET.ParseError) as exc:
        return None, str(exc)


def _check_meta_xml(meta_path: Path, issues: list[str]) -> None:
    root, err = _parse_xml(meta_path)
    if err is not None:
        issues.append(f"{meta_path}: not valid XML ({err})")
        return
    if _local_name(root.tag) != "UIBundle":
        issues.append(
            f"{meta_path}: root element is <{_local_name(root.tag)}>, expected <UIBundle>"
        )
        return

    fields = {_local_name(child.tag): (child.text or "").strip() for child in root}

    for required in REQUIRED_FIELDS:
        if not fields.get(required):
            issues.append(
                f"{meta_path}: required field <{required}> is missing or empty "
                f"(UIBundle requires masterLabel, version, and isActive)"
            )

    is_active = fields.get("isActive", "")
    if is_active and is_active.lower() not in {"true", "false"}:
        issues.append(f"{meta_path}: <isActive> is '{is_active}', expected 'true' or 'false'")

    target = fields.get("target", "")
    if target:
        if target not in VALID_TARGETS:
            issues.append(
                f"{meta_path}: unrecognized <target> '{target}'. "
                f"Expected one of: {', '.join(sorted(VALID_TARGETS))}"
            )
        elif target in DEPRECATED_TARGETS:
            issues.append(
                f"{meta_path}: <target>AppLauncher</target> is deprecated in API v67.0 — "
                f"use CustomApplication (the default) instead"
            )


def _check_bundle_contents(bundle_dir: Path, issues: list[str]) -> None:
    file_count = 0
    for path in bundle_dir.rglob("*"):
        rel_parts = path.relative_to(bundle_dir).parts
        if any(part in FORBIDDEN_DIR_NAMES for part in rel_parts):
            if path.is_dir() and path.name in FORBIDDEN_DIR_NAMES:
                issues.append(
                    f"{path}: '{path.name}/' inside a UIBundle — deploy built output only "
                    f"(the bundle is capped at {MAX_BUNDLE_FILES} files)"
                )
            continue
        if path.is_file():
            file_count += 1
            if SECRETY_FILE_RE.match(path.name):
                issues.append(
                    f"{path}: dotenv file inside a UIBundle — never ship environment/secret "
                    f"files as org metadata"
                )
    if file_count > MAX_BUNDLE_FILES:
        issues.append(
            f"{bundle_dir}: contains {file_count} files, over the documented "
            f"{MAX_BUNDLE_FILES}-file UIBundle cap — ship built output only"
        )
    elif file_count > MAX_BUNDLE_FILES * FILE_COUNT_WARN_RATIO:
        issues.append(
            f"{bundle_dir}: contains {file_count} files, close to the "
            f"{MAX_BUNDLE_FILES}-file UIBundle cap"
        )


def _check_token_smells(bundle_dir: Path, issues: list[str]) -> None:
    """Flag hand-rolled auth in app code — createDataSDK() handles authentication."""
    for path in bundle_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".js", ".jsx", ".ts", ".tsx", ".mjs"}:
            continue
        if any(part in FORBIDDEN_DIR_NAMES for part in path.relative_to(bundle_dir).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        match = TOKEN_SMELL_RE.search(text)
        if match:
            issues.append(
                f"{path}: found '{match.group(0)}' — UI bundles must not hand-roll auth; "
                f"createDataSDK() from @salesforce/platform-sdk handles authentication"
            )


def _check_package_xml(pkg_path: Path, issues: list[str]) -> None:
    root, err = _parse_xml(pkg_path)
    if err is not None:
        issues.append(f"{pkg_path}: not valid XML ({err})")
        return
    has_uibundle = False
    for types_el in root:
        if _local_name(types_el.tag) != "types":
            continue
        names = [
            (child.text or "").strip()
            for child in types_el
            if _local_name(child.tag) == "name"
        ]
        if "UIBundle" in names:
            has_uibundle = True
    if not has_uibundle:
        return
    for child in root:
        if _local_name(child.tag) == "version":
            try:
                version = float((child.text or "").strip())
            except ValueError:
                issues.append(f"{pkg_path}: unparseable <version> for a UIBundle manifest")
                return
            if version < MIN_API_VERSION:
                issues.append(
                    f"{pkg_path}: <version>{version:g}</version> is below {MIN_API_VERSION:g} — "
                    f"UIBundle is available in API version 66.0 and later "
                    f"(use {CUSTOM_APP_TARGET_MIN_API:g}+ for the CustomApplication target)"
                )
            return
    issues.append(f"{pkg_path}: UIBundle manifest has no <version> element")


def check(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    bundle_roots = sorted(
        p for p in manifest_dir.rglob("uiBundles")
        if p.is_dir() and not any(part in FORBIDDEN_DIR_NAMES for part in p.parts)
    )
    if not bundle_roots:
        return [f"No 'uiBundles/' folder found under {manifest_dir} — nothing to check."]

    for ui_root in bundle_roots:
        for bundle_dir in sorted(p for p in ui_root.iterdir() if p.is_dir()):
            meta_files = sorted(bundle_dir.glob("*.uibundle-meta.xml"))
            if not meta_files:
                issues.append(
                    f"{bundle_dir}: no .uibundle-meta.xml descriptor found "
                    f"(required: masterLabel, version, isActive)"
                )
            for meta in meta_files:
                _check_meta_xml(meta, issues)
            _check_bundle_contents(bundle_dir, issues)
            _check_token_smells(bundle_dir, issues)

    for pkg in sorted(manifest_dir.rglob("package.xml")):
        if any(part in FORBIDDEN_DIR_NAMES for part in pkg.parts):
            continue
        _check_package_xml(pkg, issues)

    return issues


def main() -> int:
    args = parse_args()
    issues = check(Path(args.manifest_dir))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
