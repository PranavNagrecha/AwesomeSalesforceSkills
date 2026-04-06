#!/usr/bin/env python3
"""Checker script for reCAPTCHA and Bot Prevention skill.

Scans Salesforce metadata for common reCAPTCHA configuration issues:
- Hardcoded reCAPTCHA secret keys in Apex classes
- Missing Remote Site Settings for google.com
- Missing CSP Trusted Sites for gstatic.com
- reCAPTCHA token generated on page load instead of submit

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_recaptcha_and_bot_prevention.py [--help]
    python3 check_recaptcha_and_bot_prevention.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check reCAPTCHA and Bot Prevention configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files(root: Path, extensions: list[str]) -> list[Path]:
    """Recursively find files with the given extensions."""
    results: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if any(fname.endswith(ext) for ext in extensions):
                results.append(Path(dirpath) / fname)
    return results


def check_hardcoded_secret_keys(apex_files: list[Path]) -> list[str]:
    """Detect hardcoded reCAPTCHA secret keys in Apex source files."""
    issues: list[str] = []
    # reCAPTCHA keys start with 6L and are 40 chars total
    key_pattern = re.compile(r"""['"]6L[a-zA-Z0-9_-]{38}['"]""")
    secret_assign_pattern = re.compile(
        r"(?i)(secret|recaptcha).*?=\s*['\"][a-zA-Z0-9_-]{20,}['\"]"
    )
    for fpath in apex_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_num, line in enumerate(content.splitlines(), start=1):
            if key_pattern.search(line):
                issues.append(
                    f"Possible hardcoded reCAPTCHA key in {fpath}:{line_num} — "
                    f"store keys in Custom Metadata or Named Credentials."
                )
            elif secret_assign_pattern.search(line):
                # Only flag if not a CustomMetadata or Named Credential fetch
                if "getInstance" not in line and "NamedCredential" not in line:
                    issues.append(
                        f"Possible hardcoded secret in {fpath}:{line_num} — "
                        f"review this line for credential leakage."
                    )
    return issues


def check_token_on_page_load(js_files: list[Path]) -> list[str]:
    """Detect reCAPTCHA tokens generated on page load instead of submit."""
    issues: list[str] = []
    lifecycle_pattern = re.compile(
        r"(connectedCallback|renderedCallback|ngOnInit|componentDidMount|init\s*\()\s*"
    )
    recaptcha_execute = re.compile(r"grecaptcha\.execute")
    for fpath in js_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = content.splitlines()
        in_lifecycle = False
        brace_depth = 0
        for line_num, line in enumerate(lines, start=1):
            if lifecycle_pattern.search(line):
                in_lifecycle = True
                brace_depth = 0
            if in_lifecycle:
                brace_depth += line.count("{") - line.count("}")
                if recaptcha_execute.search(line):
                    issues.append(
                        f"reCAPTCHA token generated in lifecycle method at {fpath}:{line_num} — "
                        f"tokens expire in 120s; generate at submit time instead."
                    )
                if brace_depth <= 0 and in_lifecycle:
                    in_lifecycle = False
    return issues


def check_remote_site_settings(manifest_dir: Path) -> list[str]:
    """Check for Remote Site Setting for google.com."""
    issues: list[str] = []
    rss_dir = manifest_dir / "remoteSiteSettings"
    if not rss_dir.exists():
        # Also check force-app style
        rss_dir = manifest_dir / "force-app" / "main" / "default" / "remoteSiteSettings"
    if not rss_dir.exists():
        # Can't verify — not necessarily an issue if metadata isn't retrieved
        return issues

    found_google = False
    for fpath in rss_dir.glob("*.remoteSite-meta.xml"):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "google.com" in content.lower():
            found_google = True
            break

    if not found_google:
        issues.append(
            "No Remote Site Setting found for google.com — required for server-side "
            "reCAPTCHA verification callout to https://www.google.com/recaptcha/api/siteverify."
        )
    return issues


def check_csp_trusted_sites(manifest_dir: Path) -> list[str]:
    """Check for CSP Trusted Sites covering google.com and gstatic.com."""
    issues: list[str] = []
    csp_dir = manifest_dir / "cspTrustedSites"
    if not csp_dir.exists():
        csp_dir = manifest_dir / "force-app" / "main" / "default" / "cspTrustedSites"
    if not csp_dir.exists():
        return issues

    found_google = False
    found_gstatic = False
    for fpath in csp_dir.glob("*.cspTrustedSite-meta.xml"):
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "google.com" in content.lower():
            found_google = True
        if "gstatic.com" in content.lower():
            found_gstatic = True

    if not found_google:
        issues.append(
            "No CSP Trusted Site found for google.com — reCAPTCHA script will fail to load "
            "in Experience Cloud sites."
        )
    if not found_gstatic:
        issues.append(
            "No CSP Trusted Site found for gstatic.com — reCAPTCHA widget resources will be "
            "blocked even if google.com is allowed. Add https://www.gstatic.com as a CSP Trusted Site."
        )
    return issues


def check_recaptcha_and_bot_prevention(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_files(manifest_dir, [".cls", ".trigger"])
    js_files = find_files(manifest_dir, [".js"])

    issues.extend(check_hardcoded_secret_keys(apex_files))
    issues.extend(check_token_on_page_load(js_files))
    issues.extend(check_remote_site_settings(manifest_dir))
    issues.extend(check_csp_trusted_sites(manifest_dir))

    if not issues:
        return []

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_recaptcha_and_bot_prevention(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
