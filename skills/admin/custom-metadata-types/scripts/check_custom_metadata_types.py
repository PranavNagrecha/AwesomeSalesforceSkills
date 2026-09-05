#!/usr/bin/env python3
"""Check Salesforce metadata for Custom Metadata Type design smells."""

from __future__ import annotations

import argparse
import json
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


def first_child(parent: ET.Element, name: str) -> ET.Element | None:
    """Return the first direct child with the given local name, or None.

    A leaf ``Element`` is falsy, so ``parent.find(a) or parent.find(b)`` silently
    discards a real match. Every caller must test ``is not None``.
    """
    for child in parent:
        if local_name(child.tag) == name:
            return child
    return None


def child_text(parent: ET.Element, name: str) -> str | None:
    """Text of the first direct child with the given local name, else None."""
    child = first_child(parent, name)
    if child is None:
        return None
    return (child.text or "").strip()


def strip_namespace_prefix(api_name: str) -> str:
    """Drop a leading managed-package namespace from ``ns__Field__c``."""
    if api_name.count("__") >= 2 and not api_name.startswith("__"):
        head, _, tail = api_name.partition("__")
        if head and tail:
            return tail
    return api_name


def project_namespace(manifest_dir: Path) -> str:
    """Namespace from the nearest sfdx-project.json, or empty string."""
    for candidate in [manifest_dir, *manifest_dir.resolve().parents][:8]:
        project_file = candidate / "sfdx-project.json"
        if not project_file.exists():
            continue
        try:
            data = json.loads(project_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ""
        namespace = data.get("namespace")
        return namespace.strip() if isinstance(namespace, str) else ""
    return ""


def record_type_name(record_file: Path) -> str:
    """`Routing_Rule` from `customMetadata/Routing_Rule.EMEA_High.md-meta.xml`."""
    stem = record_file.name
    for suffix in (".md-meta.xml", ".md"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem.split(".", 1)[0] if "." in stem else ""


def declared_field_names(object_file: Path) -> set[str]:
    """Field API names on a type, from both source and metadata-API layouts."""
    names: set[str] = set()

    for field_file in field_files_for_object(object_file):
        field_root = parse_xml(field_file)
        if field_root is None:
            continue
        api_name = field_name(field_root)
        if api_name:
            names.add(strip_namespace_prefix(api_name))

    root = parse_xml(object_file)
    if root is not None:
        for element in root:
            if local_name(element.tag) != "fields":
                continue
            api_name = child_text(element, "fullName")
            if api_name:
                names.add(strip_namespace_prefix(api_name))

    return names


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


def check_record_fields_resolve(manifest_dir: Path, cmdt_object_files: list[Path]) -> list[str]:
    """A record value naming a field the type does not declare fails the deploy."""
    issues: list[str] = []

    fields_by_type: dict[str, set[str]] = {}
    for object_file in cmdt_object_files:
        type_name = object_file.name.split(".", 1)[0]
        if type_name.endswith("__mdt"):
            type_name = type_name[: -len("__mdt")]
        type_name = strip_namespace_prefix(type_name)
        fields_by_type.setdefault(type_name, set()).update(declared_field_names(object_file))

    for record_file in sorted(manifest_dir.rglob("*.md-meta.xml")):
        if "customMetadata" not in record_file.parts:
            continue
        type_name = strip_namespace_prefix(record_type_name(record_file))
        if type_name not in fields_by_type:
            # The type is not in this manifest (installed package or partial
            # retrieve); there is nothing to compare against.
            continue

        root = parse_xml(record_file)
        if root is None:
            continue

        declared = fields_by_type[type_name]
        for values in root:
            if local_name(values.tag) != "values":
                continue
            referenced = child_text(values, "field")
            if not referenced:
                issues.append(
                    f"{record_file}: a `values` block has no `field` element; both `field` and `value` are required."
                )
                continue
            if strip_namespace_prefix(referenced) not in declared:
                issues.append(
                    f"{record_file}: references field `{referenced}`, which `{type_name}__mdt` does not declare; "
                    "the deploy will fail unless the field ships in the same request."
                )

    return issues


def check_record_labels(manifest_dir: Path) -> list[str]:
    """`label` is what the packaging UI shows; an empty one ships as blank."""
    issues: list[str] = []

    for record_file in sorted(manifest_dir.rglob("*.md-meta.xml")):
        if "customMetadata" not in record_file.parts:
            continue
        root = parse_xml(record_file)
        if root is None:
            continue
        label = child_text(root, "label")
        if not label:
            issues.append(
                f"{record_file}: custom metadata record has no non-empty `label`; the packaging UI will show a blank record name."
            )

    return issues


def check_visibility_outside_namespace(
    manifest_dir: Path, cmdt_object_files: list[Path], namespace: str
) -> list[str]:
    """`Protected` / `PackageProtected` only mean something in a managed package."""
    issues: list[str] = []
    if namespace:
        return issues

    for object_file in cmdt_object_files:
        root = parse_xml(object_file)
        if root is None:
            continue
        visibility = object_visibility(root)
        if visibility in {"Protected", "PackageProtected"}:
            issues.append(
                f"WARNING: {object_file}: `visibility` is `{visibility}` but no namespace is set in sfdx-project.json; "
                "these values only restrict access once the type ships in a managed package."
            )

    return issues


def check_protected_records_outside_namespace(manifest_dir: Path, namespace: str) -> list[str]:
    """`protected` on a record is a managed-package boundary, and one-way."""
    issues: list[str] = []
    if namespace:
        return issues

    for record_file in sorted(manifest_dir.rglob("*.md-meta.xml")):
        if "customMetadata" not in record_file.parts:
            continue
        root = parse_xml(record_file)
        if root is None:
            continue
        protected = (child_text(root, "protected") or "").lower()
        if protected == "true":
            issues.append(
                f"INFO: {record_file}: record is `protected` in a project with no namespace; "
                "once released in a managed package its developer name can no longer change."
            )

    return issues


def check_custom_metadata_types(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    namespace = project_namespace(manifest_dir)
    cmdt_object_files = find_cmdt_object_files(manifest_dir)
    issues.extend(check_object_visibility_and_fields(cmdt_object_files))
    issues.extend(check_custom_metadata_record_values(manifest_dir))
    issues.extend(check_runtime_dml_usage(manifest_dir))
    issues.extend(check_record_fields_resolve(manifest_dir, cmdt_object_files))
    issues.extend(check_record_labels(manifest_dir))
    issues.extend(check_visibility_outside_namespace(manifest_dir, cmdt_object_files, namespace))
    issues.extend(check_protected_records_outside_namespace(manifest_dir, namespace))

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
