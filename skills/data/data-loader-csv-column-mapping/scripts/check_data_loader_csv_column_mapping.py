#!/usr/bin/env python3
"""Pre-load checker for Data Loader / Bulk API V2 CSV column mappings.

Takes a CSV header row plus a target SObject's describe JSON and reports:
  - missing required fields (nillable=false, defaultedOnCreate=false, createable
    or updateable per operation)
  - extra columns not present on the target object (Bulk V2 rejects these;
    Data Loader silently drops)
  - case-sensitivity issues (header matches a field only when lower-cased — fine
    for Data Loader, broken for Bulk API V2)
  - type mismatches between simple inferred CSV column types and the target
    field type (e.g. a date-shaped column mapped to a text field, or a free-text
    column mapped to a date field)
  - polymorphic lookup columns missing the explicit type prefix
    (e.g. `Who.External_Id__c` without `Who.Lead.` or `Who.Contact.`)
  - relationship-style headers (`Account.External_Account_Id__c`) referencing
    fields that are not configured as External ID + Unique
  - namespace-prefix mismatches (header missing the prefix that exists on the
    target field)

Stdlib-only — no pip dependencies.

Usage:
    python3 check_data_loader_csv_column_mapping.py \\
        --csv-header path/to/header.csv \\
        --describe-json path/to/describe.json \\
        [--target-tool {dataloader,dataloaderio,workbench,bulkv2}] \\
        [--operation {insert,update,upsert,delete}] \\
        [--external-id FIELD_API_NAME] \\
        [--csv-sample path/to/sample.csv]

The header file may be a single line of comma-separated headers, or the first
line of a full CSV. The describe JSON is the result of a Salesforce describe
call — typically `sf sobject describe -s <Object> --json` (the script reads
either the raw `result` block or the full envelope).

Exit codes:
    0  no issues
    1  one or more issues reported (printed to stderr)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Type inference helpers (CSV cell -> coarse type bucket)
# ---------------------------------------------------------------------------

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"
)
INT_RE = re.compile(r"^-?\d+$")
DECIMAL_RE = re.compile(r"^-?\d+(?:\.\d+)?$")
ID18_RE = re.compile(r"^[a-zA-Z0-9]{15}([a-zA-Z0-9]{3})?$")
BOOL_VALUES = {"true", "false"}
BOOL_LOOSE_VALUES = {"true", "false", "1", "0", "yes", "no", "y", "n"}


def infer_cell_type(value: str) -> str:
    """Return a coarse type bucket for a CSV cell."""
    v = (value or "").strip()
    if v == "":
        return "blank"
    if v.lower() in BOOL_VALUES:
        return "boolean"
    if v.lower() in BOOL_LOOSE_VALUES:
        return "boolean_loose"  # 1/0/yes/no — V2 will reject
    if DATETIME_RE.match(v):
        return "datetime"
    if DATE_RE.match(v):
        return "date"
    if INT_RE.match(v):
        return "int"
    if DECIMAL_RE.match(v):
        return "decimal"
    if ID18_RE.match(v) and (len(v) == 15 or len(v) == 18):
        return "id"
    return "string"


def infer_column_type(values: Iterable[str]) -> str:
    """Aggregate cell-level inference across a column."""
    seen: set[str] = set()
    for v in values:
        t = infer_cell_type(v)
        if t == "blank":
            continue
        seen.add(t)
    if not seen:
        return "unknown"
    if len(seen) == 1:
        return next(iter(seen))
    # Mixed numeric — promote int to decimal
    if seen <= {"int", "decimal"}:
        return "decimal"
    if seen == {"date", "datetime"}:
        return "datetime"
    return "string"


# ---------------------------------------------------------------------------
# Salesforce field-type compatibility table
# ---------------------------------------------------------------------------

# Map describe field type -> set of acceptable inferred CSV column types.
# Conservative: when in doubt, "string" is acceptable everywhere because the
# server will attempt coercion.
FIELD_TYPE_ACCEPTS: dict[str, set[str]] = {
    "id": {"id", "string"},
    "reference": {"id", "string"},  # raw Id or relationship-resolved string
    "string": {"string", "int", "decimal", "boolean", "boolean_loose", "date", "datetime", "id"},
    "textarea": {"string", "int", "decimal", "boolean", "boolean_loose", "date", "datetime", "id"},
    "url": {"string"},
    "phone": {"string", "int"},
    "email": {"string"},
    "picklist": {"string"},
    "multipicklist": {"string"},
    "boolean": {"boolean"},  # boolean_loose explicitly NOT accepted by Bulk V2
    "date": {"date"},
    "datetime": {"datetime", "date"},
    "time": {"string"},
    "int": {"int"},
    "double": {"int", "decimal"},
    "currency": {"int", "decimal"},
    "percent": {"int", "decimal"},
    "address": {"string"},
    "anyType": {"string", "int", "decimal", "boolean", "date", "datetime", "id"},
    "encryptedstring": {"string"},
    "base64": {"string"},
    "combobox": {"string"},
    "complexvalue": {"string"},
}


# ---------------------------------------------------------------------------
# Describe loading
# ---------------------------------------------------------------------------

@dataclass
class FieldMeta:
    name: str
    type: str
    nillable: bool
    defaulted_on_create: bool
    createable: bool
    updateable: bool
    external_id: bool
    unique: bool
    reference_to: tuple[str, ...]
    relationship_name: str | None


@dataclass
class ObjectMeta:
    name: str
    fields: dict[str, FieldMeta]              # canonical API name -> meta
    fields_lc: dict[str, str]                 # lower-case -> canonical
    relationships_lc: dict[str, str]          # lower-case relationship name -> canonical relationship name
    relationship_to_field: dict[str, str]     # relationship name -> field API name
    polymorphic_relationships: set[str]       # relationship names that target multiple sobjects


def load_describe(path: Path) -> ObjectMeta:
    raw = json.loads(path.read_text())
    if "result" in raw and "fields" in raw.get("result", {}):
        body = raw["result"]
    else:
        body = raw
    name = body.get("name", "<unknown>")
    fields: dict[str, FieldMeta] = {}
    relationships_lc: dict[str, str] = {}
    relationship_to_field: dict[str, str] = {}
    polymorphic: set[str] = set()
    for f in body.get("fields", []):
        ref_to = tuple(f.get("referenceTo") or [])
        rel = f.get("relationshipName")
        meta = FieldMeta(
            name=f["name"],
            type=f.get("type", "string"),
            nillable=bool(f.get("nillable", True)),
            defaulted_on_create=bool(f.get("defaultedOnCreate", False)),
            createable=bool(f.get("createable", False)),
            updateable=bool(f.get("updateable", False)),
            external_id=bool(f.get("externalId", False)),
            unique=bool(f.get("unique", False)),
            reference_to=ref_to,
            relationship_name=rel,
        )
        fields[meta.name] = meta
        if rel:
            relationships_lc[rel.lower()] = rel
            relationship_to_field[rel] = meta.name
            if len(ref_to) > 1:
                polymorphic.add(rel)
    fields_lc = {n.lower(): n for n in fields}
    return ObjectMeta(
        name=name,
        fields=fields,
        fields_lc=fields_lc,
        relationships_lc=relationships_lc,
        relationship_to_field=relationship_to_field,
        polymorphic_relationships=polymorphic,
    )


# ---------------------------------------------------------------------------
# CSV header / sample loading
# ---------------------------------------------------------------------------

def load_header(path: Path) -> list[str]:
    text = path.read_text().splitlines()
    if not text:
        return []
    reader = csv.reader([text[0]])
    return [h.strip() for h in next(reader)]


def load_sample_columns(path: Path | None) -> dict[str, list[str]]:
    if path is None:
        return {}
    columns: dict[str, list[str]] = {}
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            for k, v in row.items():
                columns.setdefault(k, []).append(v if v is not None else "")
    return columns


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    severity: str   # ERROR | WARN
    code: str
    message: str

    def render(self) -> str:
        return f"{self.severity}: [{self.code}] {self.message}"


def parse_relationship_header(header: str) -> tuple[str, ...]:
    """Split a relationship-style header into its dotted parts."""
    return tuple(p for p in header.split(".") if p)


def check_required_fields(
    obj: ObjectMeta,
    headers: list[str],
    operation: str,
    issues: list[Issue],
) -> None:
    """Ensure required fields are present in the CSV for the chosen operation."""
    if operation not in {"insert", "upsert"}:
        return
    headers_lc = {h.lower() for h in headers}
    # Headers via relationship names also count as covering the underlying field
    for h in headers:
        parts = parse_relationship_header(h)
        if len(parts) >= 2 and parts[0].lower() in obj.relationships_lc:
            rel_canonical = obj.relationships_lc[parts[0].lower()]
            field_for_rel = obj.relationship_to_field.get(rel_canonical)
            if field_for_rel:
                headers_lc.add(field_for_rel.lower())
    for f in obj.fields.values():
        if f.nillable or f.defaulted_on_create:
            continue
        if not f.createable:
            continue
        if f.name.lower() in headers_lc:
            continue
        issues.append(
            Issue(
                "ERROR",
                "MISSING_REQUIRED",
                f"Required field '{f.name}' (type={f.type}) is not present in the CSV header",
            )
        )


def check_extra_columns(
    obj: ObjectMeta,
    headers: list[str],
    target_tool: str,
    issues: list[Issue],
) -> None:
    for h in headers:
        if "." in h:
            continue  # handled by relationship checks
        if h in obj.fields:
            continue
        if h.lower() in obj.fields_lc:
            continue  # handled by case-sensitivity checks
        sev = "ERROR" if target_tool == "bulkv2" else "WARN"
        issues.append(
            Issue(
                sev,
                "EXTRA_COLUMN",
                f"CSV column '{h}' does not match any field on {obj.name}. "
                f"Bulk API V2 will reject; Data Loader will silently drop.",
            )
        )


def check_case_sensitivity(
    obj: ObjectMeta,
    headers: list[str],
    target_tool: str,
    issues: list[Issue],
) -> None:
    for h in headers:
        if "." in h or h in obj.fields:
            continue
        canonical = obj.fields_lc.get(h.lower())
        if canonical and canonical != h:
            sev = "ERROR" if target_tool == "bulkv2" else "WARN"
            issues.append(
                Issue(
                    sev,
                    "CASE_MISMATCH",
                    f"Header '{h}' matches field '{canonical}' only when case-insensitive. "
                    f"Bulk API V2 is strictly case-sensitive — rename the header to '{canonical}'.",
                )
            )


def check_namespace_prefix(
    obj: ObjectMeta,
    headers: list[str],
    issues: list[Issue],
) -> None:
    """If a header matches a field's suffix ignoring a namespace prefix, flag it."""
    suffix_map: dict[str, str] = {}
    for fname in obj.fields:
        if "__" in fname:
            # e.g. npe01__Payment_Method__c -> Payment_Method__c
            tail = fname.split("__", 1)[1] if fname.count("__") >= 2 else fname
            suffix_map.setdefault(tail.lower(), fname)
    for h in headers:
        if "." in h or h in obj.fields:
            continue
        if h.lower() in obj.fields_lc:
            continue
        canonical = suffix_map.get(h.lower())
        if canonical and canonical != h:
            issues.append(
                Issue(
                    "ERROR",
                    "NAMESPACE_MISSING",
                    f"Header '{h}' looks like the un-prefixed form of '{canonical}'. "
                    f"Add the namespace prefix or the column will silently drop.",
                )
            )


def check_polymorphic_lookup(
    obj: ObjectMeta,
    headers: list[str],
    issues: list[Issue],
) -> None:
    for h in headers:
        parts = parse_relationship_header(h)
        if len(parts) < 2:
            continue
        rel_lc = parts[0].lower()
        if rel_lc not in obj.relationships_lc:
            continue
        rel = obj.relationships_lc[rel_lc]
        if rel not in obj.polymorphic_relationships:
            continue
        # Polymorphic — second part must be one of the referenceTo SObjects
        field_api = obj.relationship_to_field[rel]
        targets = obj.fields[field_api].reference_to
        if len(parts) < 3:
            issues.append(
                Issue(
                    "ERROR",
                    "POLYMORPHIC_NO_TYPE",
                    f"Header '{h}' targets polymorphic relationship '{rel}' "
                    f"({', '.join(targets)}) but lacks an explicit type. "
                    f"Use '{rel}.<Type>.<ExternalIdField>' — e.g. '{rel}.{targets[0]}.<ExtIdField>'.",
                )
            )
            continue
        if parts[1] not in targets:
            issues.append(
                Issue(
                    "ERROR",
                    "POLYMORPHIC_BAD_TYPE",
                    f"Header '{h}' specifies type '{parts[1]}' but '{rel}' resolves to "
                    f"{', '.join(targets)}.",
                )
            )


def check_relationship_external_id(
    obj: ObjectMeta,
    headers: list[str],
    issues: list[Issue],
) -> None:
    """For relationship-style headers, ensure the target field is External ID + Unique.

    This requires loading the target object's describe — which we do not have in
    this single-object check. We surface a WARN when we can detect the form but
    cannot verify the target side.
    """
    for h in headers:
        parts = parse_relationship_header(h)
        if len(parts) < 2:
            continue
        rel_lc = parts[0].lower()
        if rel_lc not in obj.relationships_lc:
            issues.append(
                Issue(
                    "ERROR",
                    "UNKNOWN_RELATIONSHIP",
                    f"Header '{h}' references relationship '{parts[0]}' which does not exist on {obj.name}.",
                )
            )
            continue
        # Cannot verify target-side externalId/unique without target describe
        issues.append(
            Issue(
                "WARN",
                "REL_EXTID_UNVERIFIED",
                f"Header '{h}' uses relationship binding. Verify the target field "
                f"(last segment) is configured 'External ID = true' and 'Unique = true' "
                f"on the related object — this checker only sees {obj.name}'s describe.",
            )
        )


def check_type_compatibility(
    obj: ObjectMeta,
    headers: list[str],
    sample: dict[str, list[str]],
    target_tool: str,
    issues: list[Issue],
) -> None:
    if not sample:
        return
    for h in headers:
        if "." in h:
            continue
        canonical = obj.fields.get(h) or obj.fields.get(obj.fields_lc.get(h.lower(), ""))
        if canonical is None:
            continue
        col_values = sample.get(h, [])
        if not col_values:
            continue
        inferred = infer_column_type(col_values)
        if inferred in {"unknown", "blank"}:
            continue
        # Special-case boolean_loose against a boolean field BEFORE the generic
        # accepts check, because behaviour depends on the target tool.
        if canonical.type == "boolean" and inferred == "boolean_loose":
            if target_tool == "bulkv2":
                issues.append(
                    Issue(
                        "ERROR",
                        "BOOLEAN_LOOSE",
                        f"Column '{h}' contains values like 1/0/yes/no. Bulk API V2 "
                        f"only accepts TRUE/FALSE for boolean field '{canonical.name}'.",
                    )
                )
            else:
                issues.append(
                    Issue(
                        "WARN",
                        "BOOLEAN_LOOSE",
                        f"Column '{h}' uses 1/0/yes/no for boolean field '{canonical.name}'. "
                        f"Data Loader tolerates this; Bulk API V2 would reject. Normalise to TRUE/FALSE.",
                    )
                )
            continue
        accepts = FIELD_TYPE_ACCEPTS.get(canonical.type, {"string"})
        if inferred in accepts:
            continue
        issues.append(
            Issue(
                "ERROR",
                "TYPE_MISMATCH",
                f"Column '{h}' inferred type '{inferred}' is not compatible with "
                f"field '{canonical.name}' (type={canonical.type}).",
            )
        )


def check_external_id_field(
    obj: ObjectMeta,
    external_id: str | None,
    issues: list[Issue],
) -> None:
    if not external_id:
        return
    f = obj.fields.get(external_id) or obj.fields.get(obj.fields_lc.get(external_id.lower(), ""))
    if f is None:
        issues.append(
            Issue(
                "ERROR",
                "EXTID_FIELD_NOT_FOUND",
                f"Upsert External ID field '{external_id}' does not exist on {obj.name}.",
            )
        )
        return
    if not f.external_id:
        issues.append(
            Issue(
                "ERROR",
                "EXTID_FIELD_NOT_FLAGGED",
                f"Field '{f.name}' is not configured 'External ID = true'.",
            )
        )
    if not f.unique:
        issues.append(
            Issue(
                "ERROR",
                "EXTID_FIELD_NOT_UNIQUE",
                f"Field '{f.name}' is not 'Unique = true' — upsert matches will be non-deterministic.",
            )
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pre-load checker for Data Loader / Bulk API V2 CSV column mappings.",
    )
    parser.add_argument("--csv-header", required=True, help="Path to a CSV file (only the header row is read).")
    parser.add_argument("--describe-json", required=True, help="Path to a Salesforce describe JSON for the target SObject.")
    parser.add_argument(
        "--target-tool",
        choices=("dataloader", "dataloaderio", "workbench", "bulkv2"),
        default="bulkv2",
        help="The strictest tool the CSV must satisfy. Default: bulkv2.",
    )
    parser.add_argument(
        "--operation",
        choices=("insert", "update", "upsert", "delete"),
        default="insert",
        help="Operation type (drives required-field checks). Default: insert.",
    )
    parser.add_argument(
        "--external-id",
        default=None,
        help="External ID field API name (only meaningful for --operation upsert).",
    )
    parser.add_argument(
        "--csv-sample",
        default=None,
        help="Optional path to a sample CSV (with data rows) for type-compatibility inference.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    header_path = Path(args.csv_header)
    describe_path = Path(args.describe_json)
    sample_path = Path(args.csv_sample) if args.csv_sample else None

    if not header_path.exists():
        print(f"ERROR: CSV header file not found: {header_path}", file=sys.stderr)
        return 1
    if not describe_path.exists():
        print(f"ERROR: Describe JSON file not found: {describe_path}", file=sys.stderr)
        return 1

    headers = load_header(header_path)
    if not headers:
        print(f"ERROR: No headers found in {header_path}", file=sys.stderr)
        return 1

    obj = load_describe(describe_path)
    sample = load_sample_columns(sample_path)

    issues: list[Issue] = []
    check_required_fields(obj, headers, args.operation, issues)
    check_extra_columns(obj, headers, args.target_tool, issues)
    check_case_sensitivity(obj, headers, args.target_tool, issues)
    check_namespace_prefix(obj, headers, issues)
    check_polymorphic_lookup(obj, headers, issues)
    check_relationship_external_id(obj, headers, issues)
    check_type_compatibility(obj, headers, sample, args.target_tool, issues)
    check_external_id_field(obj, args.external_id, issues)

    if not issues:
        print(f"OK: {len(headers)} headers checked against {obj.name} — no issues.")
        return 0

    errors = [i for i in issues if i.severity == "ERROR"]
    warns = [i for i in issues if i.severity == "WARN"]
    for i in issues:
        print(i.render(), file=sys.stderr)
    print(
        f"\n{len(errors)} error(s), {len(warns)} warning(s) "
        f"across {len(headers)} header(s) on {obj.name}.",
        file=sys.stderr,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
