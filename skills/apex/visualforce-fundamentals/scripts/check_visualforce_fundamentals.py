#!/usr/bin/env python3
"""Checker script for Visualforce Fundamentals skill.

Scans Salesforce metadata for common Visualforce anti-patterns:
  - SOQL queries in Apex controllers without WITH USER_MODE
  - SOQL queries still carrying WITH SECURITY_ENFORCED, which can't be used in Apex
    at API 67.0 and later (apexdev 264 L11926-11927)
  - Non-transient List/Map controller properties (view state bloat risk)
  - DML operations inside page-action-bound methods
  - window.top / window.parent usage in VF page scripts (LEX incompatibility)
  - renderAs="pdf" pages with <script> tags (JS ignored by PDF renderer)

Uses stdlib only — no pip dependencies.

Exit contract (2026-10-20): every finding is WARN — exit 0, exit 1 with --strict.
Missing --manifest-dir: ERROR exit 1. No .cls or .page files: one WARN, exit 0.
SOQL-NO-ENFORCEMENT is skipped for classes whose .cls-meta.xml apiVersion is 67.0+,
where Apex runs in user mode by default (apexdev 264 L11928-11929).

Usage:
    python3 check_visualforce_fundamentals.py [--manifest-dir path/to/metadata] [--strict]
    python3 check_visualforce_fundamentals.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# SOQL query that lacks USER_MODE or SECURITY_ENFORCED enforcement
_SOQL_NO_ENFORCEMENT = re.compile(
    r"\[[\s]*SELECT\b.*?\]",
    re.DOTALL | re.IGNORECASE,
)
# SECURITY_ENFORCED is matched here DELIBERATELY. It can't be used in Apex at
# API 67.0 and later (apexdev 264 L11926-11927), but a query that carries it did enforce FLS at the versions
# where it compiled, so treating it as "no enforcement at all" would be a
# false positive on a controller pinned below 67.0. It is reported separately
# by _LEGACY_SECURITY_ENFORCED below. Do not drop the alternation.
_SOQL_USER_MODE = re.compile(
    r"\bWITH\s+(USER_MODE|SECURITY_ENFORCED)\b",
    re.IGNORECASE,
)
# The removed clause itself. Per agents/_shared/AGENT_CONTRACT.md
# (Apex security idiom by API version), a scanner flags WITH SECURITY_ENFORCED
# rather than scoring it clean: on a 67.0+ class it is a compile failure, and
# below that it is legacy tech debt with WITH USER_MODE as the named migration.
_LEGACY_SECURITY_ENFORCED = re.compile(
    r"\bWITH\s+SECURITY_ENFORCED\b",
    re.IGNORECASE,
)

# Non-transient List or Map instance variable declarations in Apex
# Matches "public List<..." or "public Map<..." without a preceding "transient" keyword
_NON_TRANSIENT_COLLECTION = re.compile(
    r"^\s*(?:public|private|protected)\s+(?!.*\btransient\b)(List|Map)\s*<",
    re.MULTILINE | re.IGNORECASE,
)

# DML keywords in Apex (insert, update, delete, upsert, merge)
_DML_KEYWORDS = re.compile(
    r"\b(insert|update|delete|upsert|merge)\s+\w",
    re.IGNORECASE,
)

# Apex class that looks like a VF controller (heuristic: extends or uses ApexPages)
_VF_CONTROLLER_HINT = re.compile(
    r"\bApexPages\b|\bApexPages\.StandardController\b",
    re.IGNORECASE,
)

# VF page action attribute binding
_PAGE_ACTION_ATTR = re.compile(
    r'<apex:page\b[^>]*\baction\s*=\s*["\{]\s*!\s*(\w+)',
    re.IGNORECASE,
)

# Script tags in VF pages
_SCRIPT_TAG = re.compile(
    r"<script\b",
    re.IGNORECASE,
)

# renderAs="pdf" on apex:page
_RENDER_AS_PDF = re.compile(
    r'<apex:page\b[^>]*\brenderAs\s*=\s*["\']pdf["\']',
    re.IGNORECASE,
)

# window.top / window.parent in JS
_CROSS_FRAME_JS = re.compile(
    r"\bwindow\.(top|parent)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def _class_api_version(cls_file: Path) -> float | None:
    meta = cls_file.with_name(cls_file.name + "-meta.xml")
    try:
        m = re.search(r"<apiVersion>\s*([0-9.]+)\s*</apiVersion>", meta.read_text(encoding="utf-8"))
    except OSError:
        return None
    return float(m.group(1)) if m else None


def check_apex_files(apex_dir: Path) -> list[str]:
    """Scan .cls files for SOQL without enforcement and non-transient collections."""
    issues: list[str] = []
    cls_files = list(apex_dir.rglob("*.cls"))

    for cls_file in cls_files:
        try:
            source = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        is_vf_controller = bool(_VF_CONTROLLER_HINT.search(source))
        api_version = _class_api_version(cls_file)
        user_mode_default = api_version is not None and api_version >= 67.0

        # Check SOQL queries for missing enforcement (flag in VF controllers explicitly)
        for match in _SOQL_NO_ENFORCEMENT.finditer(source):
            query_text = match.group(0)
            if not _SOQL_USER_MODE.search(query_text):
                if user_mode_default:
                    continue  # 67.0+: user mode is the default (apexdev 264 L11928-11929)
                issues.append(
                    f"[SOQL-NO-ENFORCEMENT] {cls_file.name}: "
                    f"SOQL query missing WITH USER_MODE (class not at API 67.0+, so system "
                    f"mode is the default, apexdev 264 L11928-11929) — "
                    f"snippet: {query_text[:80].strip()!r}"
                )
            elif _LEGACY_SECURITY_ENFORCED.search(query_text):
                issues.append(
                    f"[SOQL-LEGACY-SECURITY-ENFORCED] {cls_file.name}: "
                    f"SOQL query uses WITH SECURITY_ENFORCED, which can't be used in "
                    f"Apex at API 67.0 and later (apexdev 264 L11926-11927); below 67.0 "
                    f"it should migrate to WITH USER_MODE. The gate "
                    f"is the apiVersion in the class's .cls-meta.xml, not the org's "
                    f"release — snippet: {query_text[:80].strip()!r}"
                )

        # Check for non-transient collection declarations in VF controllers
        if is_vf_controller:
            for match in _NON_TRANSIENT_COLLECTION.finditer(source):
                issues.append(
                    f"[VIEW-STATE-RISK] {cls_file.name}: "
                    f"Non-transient collection property may bloat view state — "
                    f"line: {match.group(0).strip()!r}. "
                    f"Consider marking it transient if it is display-only."
                )

    return issues


def check_vf_pages(pages_dir: Path) -> list[str]:
    """Scan .page files for PDF+JS anti-patterns and cross-frame JS usage."""
    issues: list[str] = []
    page_files = list(pages_dir.rglob("*.page"))

    for page_file in page_files:
        try:
            markup = page_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        is_pdf_page = bool(_RENDER_AS_PDF.search(markup))

        if is_pdf_page and _SCRIPT_TAG.search(markup):
            issues.append(
                f"[PDF-SCRIPT-TAG] {page_file.name}: "
                f"Page uses renderAs=\"pdf\" but contains <script> tags. "
                f"JavaScript is NOT executed by the PDF renderer — "
                f"remove all <script> blocks from PDF pages."
            )

        if _CROSS_FRAME_JS.search(markup):
            issues.append(
                f"[LEX-CROSS-FRAME] {page_file.name}: "
                f"Found window.top or window.parent reference. "
                f"This fails in Lightning Experience iframes (cross-origin restriction). "
                f"Use sforce.one.* API for LEX navigation instead."
            )

        # Warn about page action attribute (heuristic — may have false positives)
        action_match = _PAGE_ACTION_ATTR.search(markup)
        if action_match:
            issues.append(
                f"[PAGE-ACTION-WARNING] {page_file.name}: "
                f"Page has action=\"{{!{action_match.group(1)}}}\" — verify this method "
                f"performs only read-only data loading. DML in page action fires on "
                f"every GET request and is a CSRF risk."
            )

    return issues


def check_visualforce_fundamentals(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Common SFDX project layout: force-app/main/default/classes / pages
    # Also support flat layouts where .cls and .page files are at top level
    apex_dirs = [
        manifest_dir / "force-app" / "main" / "default" / "classes",
        manifest_dir / "src" / "classes",
        manifest_dir / "classes",
        manifest_dir,
    ]
    page_dirs = [
        manifest_dir / "force-app" / "main" / "default" / "pages",
        manifest_dir / "src" / "pages",
        manifest_dir / "pages",
        manifest_dir,
    ]

    apex_checked = False
    for d in apex_dirs:
        if d.exists() and list(d.rglob("*.cls")):
            issues.extend(check_apex_files(d))
            apex_checked = True
            break

    if not apex_checked:
        # Fall back to scanning the whole manifest dir
        issues.extend(check_apex_files(manifest_dir))

    pages_checked = False
    for d in page_dirs:
        if d.exists() and list(d.rglob("*.page")):
            issues.extend(check_vf_pages(d))
            pages_checked = True
            break

    if not pages_checked:
        issues.extend(check_vf_pages(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Visualforce metadata for common security "
            "and performance anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)
    if not (any(manifest_dir.rglob("*.cls")) or any(manifest_dir.rglob("*.page"))):
        print(f"WARN: no .cls or .page files under {manifest_dir}")
        return 0
    issues = check_visualforce_fundamentals(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}")

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
