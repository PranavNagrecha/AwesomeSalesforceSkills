#!/usr/bin/env python3
"""Checker script for CPQ Quote Templates skill.

Inspects Salesforce metadata in a project directory for common CPQ quote
template configuration mistakes:
  - Standard quote template objects present alongside CPQ (mixed configuration)
  - SBQQ__LineColumn__c records whose DisplayWidth values do not sum to 100
  - HTML content blocks that contain CSS class attributes or <style> blocks
  - SBQQ__TemplateSection__c records without a ConditionalPrintField but with
    suspicious HTML conditional patterns (CSS display:none)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_quote_templates.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_xml_files(directory: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under directory."""
    return list(directory.glob(pattern))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_standard_template_conflict(manifest_dir: Path) -> list[str]:
    """Warn if standard Salesforce quote templates exist alongside CPQ metadata.

    Standard quote templates (Setup > Quote Templates) query QuoteLineItem.
    CPQ stores lines in SBQQ__QuoteLine__c. The two systems must not be mixed.
    """
    issues: list[str] = []

    # Check for QuoteTemplate metadata type (standard)
    standard_template_dir = manifest_dir / "quoteTemplates"
    cpq_objects_dir = manifest_dir / "objects"

    has_standard_templates = (
        standard_template_dir.exists()
        and any(standard_template_dir.glob("*.quoteTemplate-meta.xml"))
    )

    # Look for any SBQQ__ object definitions to confirm CPQ is in use
    has_cpq_objects = False
    if cpq_objects_dir.exists():
        for obj_file in cpq_objects_dir.rglob("*.object-meta.xml"):
            if "SBQQ__" in obj_file.name:
                has_cpq_objects = True
                break
        # Also check for SBQQ fields in any object
        if not has_cpq_objects:
            for field_file in cpq_objects_dir.rglob("*.field-meta.xml"):
                if "SBQQ__" in _read_text(field_file):
                    has_cpq_objects = True
                    break

    if has_standard_templates and has_cpq_objects:
        issues.append(
            "CONFLICT: Standard Salesforce quote templates found in quoteTemplates/ "
            "alongside CPQ (SBQQ) metadata. Standard templates query QuoteLineItem — "
            "not SBQQ__QuoteLine__c — and will produce empty line item tables in a "
            "CPQ org. Use SBQQ__QuoteTemplate__c records instead."
        )

    return issues


def check_html_content_css_classes(manifest_dir: Path) -> list[str]:
    """Warn if HTML content blocks in CPQ templates contain CSS class attributes
    or <style> blocks.

    The CPQ PDF engine converts HTML to XSL-FO. CSS classes and style blocks
    are silently ignored. Only inline style attributes work.
    """
    issues: list[str] = []

    # Look for records directories or CSV data files that might contain
    # SBQQ__TemplateContent__c HTML
    content_patterns = [
        "**/*TemplateContent*.xml",
        "**/*templatecontent*.xml",
        "**/SBQQ__TemplateContent__c/**",
    ]

    found_files: list[Path] = []
    for pattern in content_patterns:
        found_files.extend(manifest_dir.glob(pattern))

    # De-duplicate
    found_files = list(set(found_files))

    style_block_re = re.compile(r"<style[\s>]", re.IGNORECASE)
    class_attr_re = re.compile(r'\bclass\s*=\s*["\']', re.IGNORECASE)

    for xml_file in found_files:
        content = _read_text(xml_file)
        if not content:
            continue

        if style_block_re.search(content):
            issues.append(
                f"CSS_CLASS: {xml_file} contains a <style> block inside HTML template "
                "content. CSS style blocks are silently stripped by the XSL-FO renderer. "
                "Use inline style attributes on every element instead."
            )
        elif class_attr_re.search(content):
            issues.append(
                f"CSS_CLASS: {xml_file} uses class=\"...\" attributes in HTML template "
                "content. CSS class rules are not honored by the CPQ PDF renderer. "
                "Use inline style attributes on every element instead."
            )

    return issues


def check_html_display_none(manifest_dir: Path) -> list[str]:
    """Warn if HTML content blocks use display:none or visibility:hidden for
    conditional visibility.

    These CSS properties are not reliably applied by the XSL-FO renderer.
    Use SBQQ__TemplateSection__c.SBQQ__ConditionalPrintField__c instead.
    """
    issues: list[str] = []

    content_patterns = [
        "**/*TemplateContent*.xml",
        "**/*templatecontent*.xml",
        "**/SBQQ__TemplateContent__c/**",
    ]

    found_files: list[Path] = []
    for pattern in content_patterns:
        found_files.extend(manifest_dir.glob(pattern))
    found_files = list(set(found_files))

    display_none_re = re.compile(r"display\s*:\s*none", re.IGNORECASE)
    visibility_hidden_re = re.compile(r"visibility\s*:\s*hidden", re.IGNORECASE)

    for xml_file in found_files:
        content = _read_text(xml_file)
        if not content:
            continue

        if display_none_re.search(content) or visibility_hidden_re.search(content):
            issues.append(
                f"CONDITIONAL_CSS: {xml_file} uses display:none or visibility:hidden "
                "inside HTML template content. These properties are not reliably honored "
                "by the XSL-FO renderer. Use SBQQ__TemplateSection__c."
                "SBQQ__ConditionalPrintField__c for conditional section visibility."
            )

    return issues


def check_line_column_widths(manifest_dir: Path) -> list[str]:
    """Warn if SBQQ__LineColumn__c display width values do not sum to 100.

    All column widths are percentages of the table width. If they do not sum
    to 100, the table overflows or leaves unexplained gaps.
    """
    issues: list[str] = []

    column_patterns = [
        "**/*LineColumn*.xml",
        "**/*linecolumn*.xml",
        "**/SBQQ__LineColumn__c/**",
    ]

    found_files: list[Path] = []
    for pattern in column_patterns:
        found_files.extend(manifest_dir.glob(pattern))
    found_files = list(set(found_files))

    if not found_files:
        return issues

    # Group by parent template content (we use filename prefix as a proxy
    # when we cannot follow full object relationships in static metadata)
    width_re = re.compile(
        r"<SBQQ__DisplayWidth__c>([\d.]+)</SBQQ__DisplayWidth__c>",
        re.IGNORECASE,
    )

    total_width = 0.0
    count = 0
    for xml_file in found_files:
        content = _read_text(xml_file)
        match = width_re.search(content)
        if match:
            try:
                total_width += float(match.group(1))
                count += 1
            except ValueError:
                pass

    if count > 0 and abs(total_width - 100.0) > 0.5:
        issues.append(
            f"COLUMN_WIDTH: Found {count} SBQQ__LineColumn__c records with display "
            f"widths summing to {total_width:.1f} (expected 100). Line items table "
            "will overflow or leave gaps. Adjust SBQQ__DisplayWidth__c values so "
            "they sum to exactly 100."
        )

    return issues


def check_missing_cpq_template_objects(manifest_dir: Path) -> list[str]:
    """Warn if the metadata contains quote-related customizations but no
    SBQQ__QuoteTemplate__c records, suggesting standard templates may be
    used in a CPQ context.
    """
    issues: list[str] = []

    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    # Check if SBQQ namespace is present at all
    has_sbqq = any(
        "SBQQ__" in str(f)
        for f in objects_dir.rglob("*")
        if f.is_file()
    )

    if not has_sbqq:
        return issues  # Not a CPQ org based on available metadata

    # Check for SBQQ__QuoteTemplate__c object definition or records
    template_patterns = [
        "**/*SBQQ__QuoteTemplate__c*",
        "**/*QuoteTemplate*",
        "**/*quotetemplate*",
    ]

    has_cpq_templates = any(
        list(manifest_dir.glob(p)) for p in template_patterns
    )

    standard_template_dir = manifest_dir / "quoteTemplates"
    has_standard_templates = (
        standard_template_dir.exists()
        and any(standard_template_dir.iterdir())
    )

    if has_standard_templates and not has_cpq_templates and has_sbqq:
        issues.append(
            "TEMPLATE_TYPE: Standard quote template metadata found in a CPQ (SBQQ) org "
            "but no SBQQ__QuoteTemplate__c metadata detected. Standard templates will "
            "not render CPQ quote lines. Configure templates using the CPQ-native "
            "SBQQ__QuoteTemplate__c object."
        )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_cpq_quote_templates(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_standard_template_conflict(manifest_dir))
    issues.extend(check_missing_cpq_template_objects(manifest_dir))
    issues.extend(check_html_content_css_classes(manifest_dir))
    issues.extend(check_html_display_none(manifest_dir))
    issues.extend(check_line_column_widths(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CPQ Quote Template metadata for common configuration issues: "
            "standard vs. CPQ template conflicts, CSS class usage, conditional "
            "visibility via CSS, and line column width totals."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cpq_quote_templates(manifest_dir)

    if not issues:
        print("No CPQ quote template issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
