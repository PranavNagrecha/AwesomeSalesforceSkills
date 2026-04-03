#!/usr/bin/env python3
"""Check Salesforce metadata for Custom Metadata Type design smells."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


APEX_DML_RE = re.compile(
    r"\b(?:insert|update|upsert|delete|undelete)\s+[^;]*__mdt\b"
    r"|\bDatabase\.(?:insert|update|upsert|delete|undelete)\s*\([^)]*__mdt",
    re.IGNORECASE | re.DOTALL,
)
SECRET_RE = re.compile(r"(secret|token|password|api[_-]?key|client[_-]?secret)", re.IGNORECASE)
HOST_RE = re.compile(r"(https?://|localhost|sandbox|my\.salesforce\.com)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Custom Metadata Types metadata and source for common anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def find_cmdt_object_files(manifest_dir: Path) -> list[Path]:
    return sorted(path for path in manifest_dir.rglob("*.object-meta.xml") if path.stem.endswith("__mdt.object-meta"))


def field_files_for_object(object_file: Path) -> list[Path]:
    fields_dir = object_file.parent / "fields"
    if not fields_dir.exists():
        return []
    return sorted(fields_dir.glob("*.field-meta.xml"))


def object_visibility(root: ET.Element) -> str:
    for element in root.iter():
        if local_name(element.tag) == "visibility":
            return (element.text or "").strip()
    return ""


def field_name(field_root: ET.Element) -> str:
    for element in field_root.iter():
        if local_name(element.tag) == "fullName":
            return (element.text or "").strip()
    return ""


def check_object_visibility_and_fields(cmdt_object_files: list[Path]) -> list[str]:
    issues: list[str] = []

    for object_file in cmdt_object_files:
        root = parse_xml(object_file)
        if root is None:
            issues.append(f"{object_file}: unable to parse custom metadata type definition.")
            continue

        visibility = object_visibility(root)
        if visibility.lower() != "public":
            continue

        for field_file in field_files_for_object(object_file):
            field_root = parse_xml(field_file)
            if field_root is None:
                issues.append(f"{field_file}: unable to parse field metadata.")
                continue
            api_name = field_name(field_root)
            if SECRET_RE.search(api_name):
                issues.append(
                    f"{field_file}: public custom metadata appears to contain a sensitive field name `{api_name}`; review whether the value belongs in Named Credentials or a protected package boundary."
                )

    return issues


def check_custom_metadata_record_values(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    for record_file in sorted(manifest_dir.rglob("*.md-meta.xml")):
        if "customMetadata" not in record_file.parts:
            continue

        root = parse_xml(record_file)
        if root is None:
            issues.append(f"{record_file}: unable to parse custom metadata record.")
            continue

        current_field = ""
        for element in root.iter():
            name = local_name(element.tag)
            text = (element.text or "").strip()
            if name == "field":
                current_field = text
            elif name == "value" and text:
                if current_field and SECRET_RE.search(current_field):
                    issues.append(
                        f"{record_file}: field `{current_field}` has a concrete value; review whether sensitive data is being stored in metadata."
                    )
                if HOST_RE.search(text):
                    issues.append(
                        f"{record_file}: metadata record contains a concrete host or environment-specific URL `{text}`; prefer Named Credentials or environment-safe indirection for endpoints."
                    )

    return issues


def check_runtime_dml_usage(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    for path in sorted(manifest_dir.rglob("*")):
        if path.suffix not in {".cls", ".trigger"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in APEX_DML_RE.finditer(text):
            issues.append(
                f"{path}:{line_number(text, match.start())}: appears to perform DML on `__mdt`; review whether runtime mutation has been designed into deployable metadata."
            )
    return issues


def check_custom_metadata_types(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    cmdt_object_files = find_cmdt_object_files(manifest_dir)
    issues.extend(check_object_visibility_and_fields(cmdt_object_files))
    issues.extend(check_custom_metadata_record_values(manifest_dir))
    issues.extend(check_runtime_dml_usage(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    issues = check_custom_metadata_types(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
