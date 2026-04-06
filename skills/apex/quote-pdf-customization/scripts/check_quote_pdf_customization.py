#!/usr/bin/env python3
"""Checker script for Quote PDF Customization skill.

Inspects Salesforce metadata for common anti-patterns in Visualforce-based
Quote PDF pages and their associated Apex controllers.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_quote_pdf_customization.py [--help]
    python3 check_quote_pdf_customization.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Quote PDF Customization configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _find_files(manifest_dir: Path, pattern: str) -> list[Path]:
    return list(manifest_dir.rglob(pattern))


def check_vf_pdf_pages(manifest_dir: Path) -> list[str]:
    """Check Visualforce pages that use renderAs='pdf' for anti-patterns."""
    issues: list[str] = []
    vf_pages = _find_files(manifest_dir, "*.page")

    for page_path in vf_pages:
        try:
            content = page_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only care about pages with renderAs="pdf"
        if not re.search(r'renderAs\s*=\s*["\']pdf["\']', content, re.IGNORECASE):
            continue

        rel = page_path.relative_to(manifest_dir)

        # Anti-pattern 1: script tags in PDF pages
        if re.search(r'<script[\s>]', content, re.IGNORECASE):
            issues.append(
                f"{rel}: contains <script> tag — JavaScript is ignored by the VF PDF renderer "
                f"(Flying Saucer / CSS 2.1). Move all dynamic logic to the Apex controller."
            )

        # Anti-pattern 2: $Resource used directly in img src (relative URL — breaks in PDF)
        if re.search(r'src\s*=\s*["\{][^"\']*\$Resource', content):
            issues.append(
                f"{rel}: uses {{!$Resource.*}} directly in an <img src> attribute. "
                f"The PDF renderer cannot resolve relative Salesforce resource URLs. "
                f"Build an absolute URL in Apex or embed the image as a base64 data URI."
            )

        # Anti-pattern 3: display:none to hide content (CSS hiding is not safe — use rendered= instead)
        if re.search(r'display\s*:\s*none', content, re.IGNORECASE):
            issues.append(
                f"{rel}: uses CSS 'display:none' to hide content. "
                f"Use Visualforce 'rendered=\"{{!booleanProperty}}\"' instead — "
                f"CSS hiding does not exclude content from the HTML source or PDF input."
            )

        # Anti-pattern 4: Flexbox or Grid layout properties (not supported by CSS 2.1)
        flex_grid_pattern = re.compile(
            r'display\s*:\s*(flex|grid|inline-flex|inline-grid)|'
            r'flex\s*:\s*\d|'
            r'grid-template|'
            r'align-items\s*:|'
            r'justify-content\s*:',
            re.IGNORECASE
        )
        if flex_grid_pattern.search(content):
            issues.append(
                f"{rel}: uses Flexbox or CSS Grid layout properties. "
                f"The VF PDF renderer supports CSS 2.1 only — these properties are silently ignored. "
                f"Use table-based or float-based layout instead."
            )

        # Check: showHeader="false" required for PDF pages
        if not re.search(r'showHeader\s*=\s*["\']false["\']', content, re.IGNORECASE):
            issues.append(
                f"{rel}: missing showHeader=\"false\" on a PDF page. "
                f"Without this the Salesforce chrome will appear in the PDF output."
            )

        # Check: sidebar="false" required for PDF pages
        if not re.search(r'sidebar\s*=\s*["\']false["\']', content, re.IGNORECASE):
            issues.append(
                f"{rel}: missing sidebar=\"false\" on a PDF page. "
                f"Without this the sidebar may appear in the PDF output."
            )

    return issues


def check_apex_controllers(manifest_dir: Path) -> list[str]:
    """Check Apex controller classes for PDF-related anti-patterns."""
    issues: list[str] = []
    apex_files = _find_files(manifest_dir, "*.cls")

    for cls_path in apex_files:
        try:
            content = cls_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = cls_path.relative_to(manifest_dir)

        # Anti-pattern: getContentAsPDF() not followed by a null check
        if "getContentAsPDF()" in content:
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if "getContentAsPDF()" in line:
                    # Check the next 12 lines for a null check
                    window = "\n".join(lines[i : i + 12])
                    if "== null" not in window and "!= null" not in window and "null ==" not in window:
                        issues.append(
                            f"{rel} (line ~{i + 1}): getContentAsPDF() call with no null check "
                            f"in the following ~12 lines. getContentAsPDF() returns null (not an "
                            f"exception) when the VF page errors — always check for null before "
                            f"using the blob."
                        )

            # Anti-pattern: Queueable calls getContentAsPDF() but missing AllowsCallouts
            if "implements Queueable" in content and "Database.AllowsCallouts" not in content:
                issues.append(
                    f"{rel}: Queueable class calls getContentAsPDF() but does not implement "
                    f"Database.AllowsCallouts. The PDF generation callout will fail at runtime."
                )

        # Anti-pattern: getContentAsPDF() called inside a trigger body
        # Heuristic: look for trigger keyword at the start of the file
        if re.match(r'\s*trigger\s+\w+', content) and "getContentAsPDF()" in content:
            issues.append(
                f"{rel}: getContentAsPDF() appears to be called inside a trigger. "
                f"Callouts are not allowed in trigger context (uncommitted DML). "
                f"Enqueue a Queueable implementing Database.AllowsCallouts instead."
            )

        # Anti-pattern: class references CPQ quote object but queries standard QuoteLineItem
        if "SBQQ__Quote__c" in content and "FROM QuoteLineItem" in content:
            issues.append(
                f"{rel}: queries QuoteLineItem but also references SBQQ__Quote__c. "
                f"CPQ stores lines in SBQQ__QuoteLine__c, not QuoteLineItem. "
                f"The QuoteLineItem query will return no records for CPQ quotes."
            )

    return issues


def check_trigger_callouts(manifest_dir: Path) -> list[str]:
    """Check trigger files for direct getContentAsPDF() callouts."""
    issues: list[str] = []
    trigger_files = _find_files(manifest_dir, "*.trigger")

    for trig_path in trigger_files:
        try:
            content = trig_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "getContentAsPDF()" in content:
            rel = trig_path.relative_to(manifest_dir)
            issues.append(
                f"{rel}: trigger directly calls getContentAsPDF(). "
                f"Callouts are forbidden in trigger DML transaction context. "
                f"Use System.enqueueJob() to dispatch a Queueable that implements "
                f"Database.AllowsCallouts."
            )

    return issues


def check_static_resources(manifest_dir: Path) -> list[str]:
    """Check static resources CSS for unsupported properties in PDF context."""
    issues: list[str] = []
    css_files = _find_files(manifest_dir, "*.css")

    for css_path in css_files:
        try:
            content = css_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only flag CSS files whose names suggest PDF/quote use
        name_lower = css_path.name.lower()
        is_pdf_related = (
            ("quote" in name_lower or "pdf" in name_lower) and
            any(kw in name_lower for kw in ("pdf", "print", "template"))
        )
        if not is_pdf_related:
            continue

        rel = css_path.relative_to(manifest_dir)

        flex_grid_pattern = re.compile(
            r'display\s*:\s*(flex|grid|inline-flex|inline-grid)|'
            r'flex\s*:\s*\d|'
            r'grid-template|'
            r'align-items\s*:|'
            r'justify-content\s*:',
            re.IGNORECASE
        )
        if flex_grid_pattern.search(content):
            issues.append(
                f"{rel}: CSS file likely used in a Quote PDF contains Flexbox/Grid properties "
                f"(unsupported by CSS 2.1 / Flying Saucer renderer). "
                f"Switch to table-based or float-based layout."
            )

        if re.search(r'--[\w-]+\s*:', content):
            issues.append(
                f"{rel}: CSS file uses CSS custom properties (variables). "
                f"CSS custom properties are not supported by the VF PDF renderer."
            )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def check_quote_pdf_customization(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_vf_pdf_pages(manifest_dir))
    issues.extend(check_apex_controllers(manifest_dir))
    issues.extend(check_trigger_callouts(manifest_dir))
    issues.extend(check_static_resources(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_quote_pdf_customization(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
