#!/usr/bin/env python3
"""Checker script for the Data Model Documentation skill.

Two independent modes; run either or both.

  --manifest-dir DIR
      Scans retrieved Salesforce metadata (sf CLI source format) for custom fields
      with a blank or missing <description>, i.e. documentation debt at the source.
      Expects <DIR>/**/objects/<Object>/fields/<Field>.field-meta.xml.

  --file FILE
      Lints the reviewed data dictionary artefact (see
      references/worked-examples.md section 5, templates/data-dictionary.yaml).

Dictionary checks
  D1  every object entry carries object, owner, classification, record_volume,
      last_reviewed                                                        ERROR
  D2  object API names are unique within the record                        ERROR
  D3  classification is one of the platform's securityClassification values
      (Public, Internal, Confidential, Restricted, MissionCritical) and
      business_status, when present, is Active|DeprecateCandidate|Hidden   ERROR
  D4  record_volume is a non-negative integer or the literal 'unknown';
      last_reviewed is YYYY-MM-DD and not in the future                    ERROR
  D5  every field row carries api_name and a non-empty type                ERROR
  D6  last_reviewed older than --max-age-days (default 365)                WARN
  D7  a field row with an empty or missing description                     WARN

Exit codes: 1 if any ERROR was reported, 0 otherwise (WARNs alone do not fail).

Stdlib only. The YAML reader below accepts the documented subset used by this
skill's artefact — nested mappings, sequences of mappings, plain and quoted
scalars, and block scalars (| > |- >-). It is not a general YAML parser; if the
dictionary is authored with anchors, flow collections or multi-document streams,
convert it first.

Usage:
    python3 check_data_model_documentation.py --file data-dictionary.yaml
    python3 check_data_model_documentation.py --manifest-dir force-app
    python3 check_data_model_documentation.py --file d.yaml --manifest-dir force-app
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FIELD_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"

# Platform value sets, Metadata API Developer Guide, CustomField:
#   securityClassification -> api_meta.txt L43614-L43622
#   businessStatus         -> api_meta.txt L43313-L43321
SECURITY_CLASSIFICATIONS = {
    "Public",
    "Internal",
    "Confidential",
    "Restricted",
    "MissionCritical",
}
BUSINESS_STATUSES = {"Active", "DeprecateCandidate", "Hidden"}

REQUIRED_OBJECT_KEYS = (
    "object",
    "owner",
    "classification",
    "record_volume",
    "last_reviewed",
)


# --------------------------------------------------------------------------- #
# Minimal YAML reader (documented subset)
# --------------------------------------------------------------------------- #


def _strip_comment(raw: str) -> str:
    """Drop a trailing ' #' comment when it is not inside quotes."""
    out = []
    quote = ""
    prev = ""
    for ch in raw:
        if quote:
            out.append(ch)
            if ch == quote and prev != "\\":
                quote = ""
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch == "#" and (not out or out[-1] in (" ", "\t")):
            break
        else:
            out.append(ch)
        prev = ch
    return "".join(out).rstrip()


def _scalar(raw: str):
    text = raw.strip()
    if not text:
        return ""
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    lowered = text.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("null", "~"):
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


class YamlSubsetError(ValueError):
    """The document uses YAML this reader does not implement."""


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _read_block_scalar(lines: list[str], start: int, parent_indent: int) -> tuple[str, int]:
    """Collect a folded/literal block starting at index `start`."""
    body: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            body.append("")
            i += 1
            continue
        if _indent_of(line) <= parent_indent:
            break
        body.append(line.strip())
        i += 1
    return " ".join(part for part in body if part), i


def _parse_block(lines: list[str], start: int, indent: int):
    """Parse one mapping or sequence at column `indent`. Returns (value, next_index)."""
    i = start
    mapping: dict = {}
    sequence: list = []
    kind = ""

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        col = _indent_of(line)
        if col < indent:
            break
        if col > indent:
            raise YamlSubsetError(f"line {i + 1}: unexpected indentation")

        body = _strip_comment(line).strip()
        if not body:
            i += 1
            continue

        if body.startswith("- "):
            if kind == "map":
                break
            kind = "seq"
            # A sequence item that is itself a mapping: re-indent and recurse.
            item_indent = col + 2
            rest = line[item_indent:]
            synthetic = [" " * item_indent + rest.lstrip()] + lines[i + 1 :]
            value, consumed = _parse_block(synthetic, 0, item_indent)
            sequence.append(value)
            i = i + consumed
            continue

        if kind == "seq":
            break
        kind = "map"

        if ":" not in body:
            raise YamlSubsetError(f"line {i + 1}: expected 'key: value'")
        key, _, raw_value = body.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()

        if raw_value in ("|", ">", "|-", ">-", "|+", ">+"):
            text, i = _read_block_scalar(lines, i + 1, col)
            mapping[key] = text
            continue

        if raw_value == "":
            nested, consumed = _parse_block(lines, i + 1, col + 2)
            if consumed == i + 1:
                # Nothing indented under it: an empty value.
                mapping[key] = ""
                i += 1
            else:
                mapping[key] = nested
                i = consumed
            continue

        mapping[key] = _scalar(raw_value)
        i += 1

    if kind == "seq":
        return sequence, i
    return mapping, i


def load_dictionary(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8").replace("\t", "    ")
    lines = [ln.rstrip("\n") for ln in raw.split("\n")]
    lines = [ln for ln in lines if not ln.lstrip().startswith("---")]
    value, _ = _parse_block(lines, 0, 0)
    if not isinstance(value, dict):
        raise YamlSubsetError("top level of the dictionary must be a mapping")
    return value


# --------------------------------------------------------------------------- #
# Mode 1: source-metadata description debt
# --------------------------------------------------------------------------- #


def get_description(field_xml: Path) -> str:
    """Return the <description> text of a .field-meta.xml file, or '' if absent."""
    try:
        root = ET.parse(field_xml).getroot()
    except ET.ParseError:
        return ""
    desc_el = root.find(f"{{{FIELD_NAMESPACE}}}description")
    if desc_el is None:
        # Some retrieved files omit the namespace. Never chain with `or` —
        # a childless Element is falsy, so `a.find(x) or a.find(y)` misfires.
        desc_el = root.find("description")
    if desc_el is not None and desc_el.text:
        return desc_el.text.strip()
    return ""


def check_field_documentation(manifest_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for custom fields missing a Description."""
    errors: list[str] = []
    warnings: list[str] = []

    if not manifest_dir.exists():
        errors.append(f"manifest directory not found: {manifest_dir}")
        return errors, warnings

    field_files = list(manifest_dir.rglob("*.field-meta.xml"))
    if not field_files:
        errors.append(
            f"no *.field-meta.xml files found under {manifest_dir} — run "
            "'sf project retrieve start --manifest manifest/data-dictionary.xml' first"
        )
        return errors, warnings

    missing: list[str] = []
    for field_file in sorted(field_files):
        field_name = field_file.stem.replace(".field-meta", "")
        if not field_name.endswith("__c"):
            continue
        parts = list(field_file.parts)
        object_name = parts[parts.index("fields") - 1] if "fields" in parts else "<unknown>"
        if not get_description(field_file):
            missing.append(f"{object_name}.{field_name}")

    if missing:
        listing = "\n".join(f"        {name}" for name in missing)
        warnings.append(
            f"{len(missing)} custom field(s) have no <description> in source "
            f"metadata:\n{listing}"
        )

    return errors, warnings


# --------------------------------------------------------------------------- #
# Mode 2: data dictionary lint
# --------------------------------------------------------------------------- #


def _check_last_reviewed(value, label: str, max_age_days: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = str(value).strip()
    try:
        reviewed = _dt.date.fromisoformat(text)
    except ValueError:
        errors.append(f"{label}: last_reviewed '{text}' is not an ISO date (YYYY-MM-DD)")
        return errors, warnings

    today = _dt.date.today()
    if reviewed > today:
        errors.append(f"{label}: last_reviewed {reviewed.isoformat()} is in the future")
        return errors, warnings

    age = (today - reviewed).days
    if age > max_age_days:
        warnings.append(
            f"{label}: last reviewed {age} days ago ({reviewed.isoformat()}), "
            f"over the {max_age_days}-day threshold"
        )
    return errors, warnings


def check_dictionary(path: Path, max_age_days: int) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a data dictionary record."""
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return [f"dictionary file not found: {path}"], warnings

    try:
        doc = load_dictionary(path)
    except YamlSubsetError as exc:
        return [f"{path}: {exc}"], warnings

    objects = doc.get("objects")
    if not isinstance(objects, list) or not objects:
        return [f"{path}: no 'objects:' list found — nothing to lint"], warnings

    seen: set[str] = set()

    for position, entry in enumerate(objects, start=1):
        if not isinstance(entry, dict):
            errors.append(f"objects[{position}]: entry is not a mapping")
            continue

        name = str(entry.get("object", "")).strip()
        label = f"object '{name}'" if name else f"objects[{position}]"

        # D1 — required keys
        for key in REQUIRED_OBJECT_KEYS:
            value = entry.get(key)
            if value is None or str(value).strip() == "":
                errors.append(f"{label}: missing required key '{key}'")

        # D2 — unique object API names
        if name:
            if name in seen:
                errors.append(f"{label}: duplicate object entry")
            seen.add(name)

        # D3 — classification value set
        classification = str(entry.get("classification", "")).strip()
        if classification and classification not in SECURITY_CLASSIFICATIONS:
            errors.append(
                f"{label}: classification '{classification}' is not a platform "
                f"securityClassification value ({', '.join(sorted(SECURITY_CLASSIFICATIONS))})"
            )

        # D4 — record_volume and last_reviewed shape
        volume = entry.get("record_volume")
        if volume is not None and str(volume).strip() != "":
            volume_text = str(volume).strip()
            if volume_text.lower() != "unknown":
                if not volume_text.isdigit():
                    errors.append(
                        f"{label}: record_volume '{volume_text}' is neither a "
                        "non-negative integer nor 'unknown'"
                    )
        reviewed = entry.get("last_reviewed")
        if reviewed is not None and str(reviewed).strip():
            date_errors, date_warnings = _check_last_reviewed(reviewed, label, max_age_days)
            errors.extend(date_errors)
            warnings.extend(date_warnings)

        # D5 / D7 — field rows
        fields = entry.get("fields")
        if fields is None or fields == "":
            warnings.append(f"{label}: no 'fields:' rows recorded")
            continue
        if not isinstance(fields, list):
            errors.append(f"{label}: 'fields' must be a list of field rows")
            continue

        for row_index, row in enumerate(fields, start=1):
            if not isinstance(row, dict):
                errors.append(f"{label}: fields[{row_index}] is not a mapping")
                continue
            api_name = str(row.get("api_name", "")).strip()
            row_label = f"{label}, field '{api_name}'" if api_name else (
                f"{label}, fields[{row_index}]"
            )
            if not api_name:
                errors.append(f"{row_label}: missing 'api_name'")
            if not str(row.get("type", "")).strip():
                errors.append(f"{row_label}: missing 'type'")

            status = str(row.get("business_status", "")).strip()
            if status and status not in BUSINESS_STATUSES:
                errors.append(
                    f"{row_label}: business_status '{status}' is not a platform value "
                    f"({', '.join(sorted(BUSINESS_STATUSES))})"
                )

            row_classification = str(row.get("classification", "")).strip()
            if row_classification and row_classification not in SECURITY_CLASSIFICATIONS:
                errors.append(
                    f"{row_label}: classification '{row_classification}' is not a platform "
                    "securityClassification value"
                )

            if not str(row.get("description", "")).strip():
                warnings.append(f"{row_label}: description is empty — documentation debt")

    return errors, warnings


# --------------------------------------------------------------------------- #


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a Salesforce data dictionary record and/or scan retrieved metadata "
            "for custom fields with no Description."
        ),
    )
    parser.add_argument(
        "--file",
        help="Path to the data dictionary record (YAML subset) to lint.",
    )
    parser.add_argument(
        "--manifest-dir",
        help="Root directory of retrieved Salesforce metadata to scan for description debt.",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=365,
        help="Warn when an object's last_reviewed date is older than this (default: 365).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.file and not args.manifest_dir:
        print("ERROR: pass --file <dictionary.yaml> and/or --manifest-dir <metadata-root>")
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    if args.file:
        file_errors, file_warnings = check_dictionary(Path(args.file), args.max_age_days)
        errors.extend(file_errors)
        warnings.extend(file_warnings)

    if args.manifest_dir:
        dir_errors, dir_warnings = check_field_documentation(Path(args.manifest_dir))
        errors.extend(dir_errors)
        warnings.extend(dir_warnings)

    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s). Documentation not deliverable.")
        return 1

    if warnings:
        print(f"\n0 errors, {len(warnings)} warning(s). Deliverable, with documentation debt listed.")
        return 0

    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
