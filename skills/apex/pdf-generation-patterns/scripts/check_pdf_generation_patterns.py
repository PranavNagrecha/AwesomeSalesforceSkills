#!/usr/bin/env python3
"""Checker script for PDF Generation Patterns skill.

Scans Salesforce metadata in a project directory for common PDF generation
anti-patterns documented in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_pdf_generation_patterns.py [--manifest-dir path/to/metadata]
    python3 check_pdf_generation_patterns.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for PDF generation anti-patterns. "
            "Scans Visualforce pages and Apex classes."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Visualforce page checks
# ---------------------------------------------------------------------------

def check_vf_pages(manifest_dir: Path) -> list[str]:
    """Check .page files for PDF-related anti-patterns."""
    issues: list[str] = []
    page_files = list(manifest_dir.rglob("*.page"))

    for page_file in page_files:
        try:
            content = page_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Only check pages that use renderAs="pdf"
        if not re.search(r'renderAs\s*=\s*["\']pdf["\']', content, re.IGNORECASE):
            continue

        rel = page_file.relative_to(manifest_dir)

        # Anti-pattern: <script> tags in a PDF page (JS is ignored by renderer)
        if re.search(r"<script[\s>]", content, re.IGNORECASE):
            issues.append(
                f"{rel}: PDF page contains <script> tag — JavaScript is silently "
                "ignored by the Flying Saucer renderer. Remove all script tags; "
                "load data server-side in the Apex controller."
            )

        # Anti-pattern: $Resource used directly in img src (relative URL — broken in PDF)
        if re.search(r'<img[^>]+\$Resource\.[^>]+>', content, re.IGNORECASE):
            issues.append(
                f"{rel}: PDF page uses {{!$Resource.X}} directly in <img src>. "
                "The renderer cannot resolve relative resource URLs. "
                "Build an absolute URL in the Apex controller using "
                "URL.getSalesforceBaseUrl().toExternalForm() + '/resource/Name'."
            )

        # Anti-pattern: apex:remoteAction (JS callout — never executes in PDF)
        if re.search(r"apex:remoteAction", content, re.IGNORECASE):
            issues.append(
                f"{rel}: PDF page uses apex:remoteAction — JavaScript does not "
                "execute during PDF rendering. Load all data in the Apex controller."
            )

        # Anti-pattern: display:none hiding data (use rendered= instead)
        if re.search(r"display\s*:\s*none", content, re.IGNORECASE):
            issues.append(
                f"{rel}: PDF page uses CSS 'display:none' to hide content. "
                "Hidden HTML is still present in the page source. "
                "Use rendered=\"{{!booleanProperty}}\" to exclude content server-side."
            )

        # Anti-pattern: external CDN stylesheet link
        if re.search(r'<link[^>]+href\s*=\s*["\']https?://', content, re.IGNORECASE):
            issues.append(
                f"{rel}: PDF page links an external stylesheet via https://. "
                "The Flying Saucer renderer does not fetch external CSS. "
                "Inline all CSS in a <style> block or use a Salesforce static resource."
            )

        # Warning: Flexbox or Grid in inline style (silently ignored by renderer)
        if re.search(r"display\s*:\s*(flex|grid)", content, re.IGNORECASE):
            issues.append(
                f"{rel}: PDF page uses CSS Flexbox or Grid layout. "
                "Flying Saucer only supports CSS 2.1 — these properties are silently "
                "ignored. Use display:table / display:table-cell for column layouts."
            )

        # Missing showHeader=false or sidebar=false
        if not re.search(r'showHeader\s*=\s*["\']false["\']', content, re.IGNORECASE):
            issues.append(
                f"{rel}: PDF page does not set showHeader=\"false\". "
                "The Salesforce page chrome will appear in the PDF output."
            )
        if not re.search(r'sidebar\s*=\s*["\']false["\']', content, re.IGNORECASE):
            issues.append(
                f"{rel}: PDF page does not set sidebar=\"false\". "
                "Set sidebar=\"false\" to suppress the navigation sidebar in PDF output."
            )

    return issues


# ---------------------------------------------------------------------------
# Apex class checks
# ---------------------------------------------------------------------------

def check_apex_classes(manifest_dir: Path) -> list[str]:
    """Check .cls files for PDF generation anti-patterns."""
    issues: list[str] = []
    cls_files = list(manifest_dir.rglob("*.cls"))

    for cls_file in cls_files:
        try:
            content = cls_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = cls_file.relative_to(manifest_dir)

        # Only check files that reference getContentAsPDF
        if "getContentAsPDF" not in content:
            continue

        # Anti-pattern: getContentAsPDF called without null check
        # Look for assignment without subsequent null check in nearby lines
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if "getContentAsPDF" in line and "=" in line:
                # Check the next 5 lines for a null check
                window = "\n".join(lines[i : i + 6])
                if "!= null" not in window and "== null" not in window:
                    issues.append(
                        f"{rel}:{i + 1}: getContentAsPDF() result assigned without "
                        "null check in the following lines. The method returns null "
                        "(not an exception) when the VF page throws an error. "
                        "Add: if (pdf == null) {{ /* log and return */ }}"
                    )

        # Anti-pattern: getContentAsPDF called in a trigger class
        # Heuristic: file name ends in Trigger or contains 'trigger' keyword
        if re.search(r"\btrigger\b", content, re.IGNORECASE) and cls_file.suffix == ".cls":
            if "getContentAsPDF" in content:
                issues.append(
                    f"{rel}: getContentAsPDF() appears in a file that may be a trigger "
                    "context. Callouts are not allowed after DML in trigger transactions. "
                    "Move PDF generation to a Queueable implementing Database.AllowsCallouts."
                )

        # Anti-pattern: class uses getContentAsPDF but does not implement AllowsCallouts
        if "getContentAsPDF" in content:
            if "Database.AllowsCallouts" not in content and "@future" not in content:
                # Only warn if this looks like it could be a Queueable or Batch
                if "implements Queueable" in content or "implements Database.Batchable" in content:
                    issues.append(
                        f"{rel}: Queueable or Batch class calls getContentAsPDF() but "
                        "does not implement Database.AllowsCallouts. "
                        "Add 'Database.AllowsCallouts' to the implements clause."
                    )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_pdf_generation_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_vf_pages(manifest_dir))
    issues.extend(check_apex_classes(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_pdf_generation_patterns(manifest_dir)

    if not issues:
        print("No PDF generation anti-patterns found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
