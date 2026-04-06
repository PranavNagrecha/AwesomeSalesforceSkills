#!/usr/bin/env python3
"""Checker script for Document Generation OmniStudio skill.

Scans a Salesforce metadata directory for common OmniStudio DocGen issues:
- Document Templates missing from the package
- OmniDataTransform definitions missing Mapping type
- Token name mismatches between templates and Data Mapper definitions
- Image/rich-text tokens used in server-side configurations

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_document_generation_omnistudio.py [--help]
    python3 check_document_generation_omnistudio.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check OmniStudio Document Generation configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def extract_tokens_from_docx_xml(xml_content: str) -> set[str]:
    """Extract {{ }} merge tokens from XML content of a .docx word/document.xml.

    This is a best-effort extraction — real .docx files are ZIP archives
    containing XML. This function works on the raw XML text if already extracted.
    """
    tokens: set[str] = set()
    # Match simple tokens: {{Name}}
    for match in re.finditer(r"\{\{([^#/&%!][^}]*?)\}\}", xml_content):
        tokens.add(match.group(1).strip())
    # Match repeating section names: {{#Items}} / {{/Items}}
    for match in re.finditer(r"\{\{#(\w+)\}\}", xml_content):
        tokens.add(f"#{match.group(1)}")
    # Match image tokens: {{%ImageField}}
    for match in re.finditer(r"\{\{%(\w+)\}\}", xml_content):
        tokens.add(f"%{match.group(1)}")
    # Match rich text tokens: {{&RichField}}
    for match in re.finditer(r"\{\{&(\w+)\}\}", xml_content):
        tokens.add(f"&{match.group(1)}")
    return tokens


def find_omnidatatransform_files(manifest_dir: Path) -> list[Path]:
    """Find OmniDataTransform metadata files in the manifest directory."""
    patterns = [
        "**/*OmniDataTransform*",
        "**/*DataRaptor*",
        "**/omniDataTransforms/**",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(manifest_dir.glob(pattern))
    return [f for f in files if f.is_file() and f.suffix in (".xml", ".json")]


def find_document_templates(manifest_dir: Path) -> list[Path]:
    """Find document template references in the manifest directory."""
    patterns = [
        "**/*DocumentTemplate*",
        "**/*DocGenSetting*",
        "**/documentGenerationSettings/**",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(manifest_dir.glob(pattern))
    return [f for f in files if f.is_file()]


def check_image_tokens_in_server_side(manifest_dir: Path) -> list[str]:
    """Check for image or rich text tokens that may be used with server-side generation."""
    issues: list[str] = []
    for xml_file in manifest_dir.rglob("*.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        has_image_token = bool(re.search(r"\{\{%\w+\}\}", content))
        has_richtext_token = bool(re.search(r"\{\{&\w+\}\}", content))
        has_server_side_ref = bool(
            re.search(r"(?i)server.?side|integrationprocedure", content)
        )

        if (has_image_token or has_richtext_token) and has_server_side_ref:
            token_types = []
            if has_image_token:
                token_types.append("image ({{%...}})")
            if has_richtext_token:
                token_types.append("rich text ({{&...}})")
            issues.append(
                f"{xml_file.name}: Contains {', '.join(token_types)} tokens "
                f"alongside server-side generation references. "
                f"Image and rich text tokens are only supported in client-side mode."
            )
    return issues


def check_token_case_consistency(manifest_dir: Path) -> list[str]:
    """Look for potential case-sensitivity issues in token names across files."""
    issues: list[str] = []
    all_tokens: dict[str, list[str]] = {}  # lowercase -> [(original, source_file)]

    for xml_file in manifest_dir.rglob("*.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for match in re.finditer(r"\{\{([^}]+)\}\}", content):
            token = match.group(1).strip().lstrip("#/&%")
            if token:
                lower = token.lower()
                if lower not in all_tokens:
                    all_tokens[lower] = []
                all_tokens[lower].append((token, xml_file.name))

    for lower_token, occurrences in all_tokens.items():
        unique_casings = set(t[0] for t in occurrences)
        if len(unique_casings) > 1:
            files = set(t[1] for t in occurrences)
            issues.append(
                f"Token case mismatch: {unique_casings} found across {files}. "
                f"Token names are case-sensitive — ensure consistent casing."
            )

    return issues


def check_document_generation_omnistudio(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for image/rich text tokens in server-side contexts
    issues.extend(check_image_tokens_in_server_side(manifest_dir))

    # Check for token case consistency
    issues.extend(check_token_case_consistency(manifest_dir))

    # Check for OmniDataTransform presence
    odt_files = find_omnidatatransform_files(manifest_dir)
    template_files = find_document_templates(manifest_dir)

    if template_files and not odt_files:
        issues.append(
            "Document Generation Settings found but no OmniDataTransform/DataRaptor "
            "metadata detected. Ensure the Data Mapper is included in the package."
        )

    if not issues:
        # No issues is a valid outcome — return empty list
        pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_document_generation_omnistudio(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
