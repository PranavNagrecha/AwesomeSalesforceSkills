#!/usr/bin/env python3
"""Static checker for global search configuration hygiene.

Scans a Salesforce metadata source tree (`force-app/main/default/objects/...`)
for signals that the org's per-object Search Layouts are reasonable:

- objects whose <searchLayouts> block is empty or absent (Lightning global
  search will fall back to Name-only)
- Search Layouts with fewer than 3 columns on the customSearchLayout slot
  (often the symptom of a Classic-era configuration not refreshed for Lightning)
- references to deleted fields in Search Layout column lists (silent rot)
- Lookup Dialog layouts with more than 6 columns on a Classic-also org
  (only first 6 render in Classic)
- objects with Allow Search disabled at the external object level

Stdlib only. XML parsing via xml.etree.ElementTree.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

# Heuristic: a populated Search Layout for global search results should carry
# at least 3 columns including Name. Below that, results render as a thin row
# and users start clicking into every record to disambiguate.
MIN_SEARCH_RESULT_COLUMNS = 3

# Classic Lookup Dialog hard cap is 6 columns. Hybrid orgs need the first 6
# columns to be the most useful ones.
CLASSIC_LOOKUP_DIALOG_MAX = 6

# Search Layout 10-column hard limit (any slot).
SEARCH_LAYOUT_MAX_COLUMNS = 10

# Synonym Group org cap.
SYNONYM_GROUP_MAX = 2000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit per-object Search Layouts and synonym configuration.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    parser.add_argument(
        "--include-hybrid-classic",
        action="store_true",
        help=(
            "Flag Lookup Dialog layouts that exceed the Classic 6-column cap. "
            "Use this in orgs that still have Classic users."
        ),
    )
    return parser.parse_args()


def force_app_root(manifest_dir: Path) -> Path | None:
    candidate = manifest_dir / "force-app"
    if candidate.exists():
        return candidate
    # Some projects put the source under src/ or unmanaged/
    for alt in ("src", "unmanaged"):
        candidate = manifest_dir / alt
        if candidate.exists():
            return candidate
    return None


def find_object_files(src_root: Path) -> list[Path]:
    """Return all CustomObject XML files under the source tree."""
    objects: list[Path] = []
    for path in src_root.rglob("*.object-meta.xml"):
        objects.append(path)
    # Some unpackaged metadata uses `<Name>.object` instead.
    for path in src_root.rglob("*.object"):
        objects.append(path)
    return sorted(set(objects))


def parse_search_layouts(object_path: Path) -> dict[str, list[str]]:
    """Return mapping of layout-slot-name -> list of field API names.

    Slot names follow the metadata API element names:
        customSearchLayout              (Lightning default global search)
        searchResultsAdditionalFields   (Classic search results)
        lookupDialogsAdditionalFields   (lookup picker)
        lookupPhoneDialogsAdditionalFields (telephony lookup)
        customTabFields                 (tab columns)
        searchFilterFields              (search facets in Lightning)
    """
    layouts: dict[str, list[str]] = {}
    try:
        tree = ET.parse(object_path)
    except ET.ParseError:
        return layouts
    root = tree.getroot()
    sl = root.find(f"{NS}searchLayouts")
    if sl is None:
        return layouts
    for child in sl:
        # Strip namespace from tag name for keying.
        tag = child.tag.replace(NS, "")
        # Each child element may itself contain repeated <field> entries.
        fields = [f.text for f in child.findall(f"{NS}field") if f.text]
        if not fields:
            # Older metadata may put each field directly as repeated children.
            if child.text and child.text.strip():
                fields = [child.text.strip()]
        if tag not in layouts:
            layouts[tag] = []
        layouts[tag].extend(fields)
    return layouts


def object_api_name(object_path: Path) -> str:
    name = object_path.name
    for suffix in (".object-meta.xml", ".object"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def known_field_names_for_object(object_path: Path) -> set[str]:
    """Return the set of field API names declared inside this object's metadata.

    For unpacked sfdx-format orgs, fields live under
    `objects/<Object>/fields/<Field>.field-meta.xml`. We scan that sibling
    directory if present.
    """
    fields: set[str] = set()
    # sfdx-format: object dir is the parent of <Object>.object-meta.xml; fields
    # sit in fields/ subdir.
    object_dir = object_path.parent
    fields_dir = object_dir / "fields"
    if fields_dir.exists():
        for fp in fields_dir.glob("*.field-meta.xml"):
            fields.add(fp.stem.removesuffix(".field-meta"))
    # Also inspect inline <fields> children if any (legacy single-file format).
    try:
        tree = ET.parse(object_path)
        root = tree.getroot()
        for f in root.findall(f"{NS}fields"):
            full = f.find(f"{NS}fullName")
            if full is not None and full.text:
                fields.add(full.text)
    except ET.ParseError:
        pass
    return fields


def standard_fields_for_account_contact_case() -> set[str]:
    """Subset of standard fields commonly referenced in Search Layouts.

    The checker does not have full access to the standard schema, so it
    permits common standard fields by name without flagging them as
    "missing". This list keeps false positives low for ordinary orgs.
    """
    return {
        "NAME", "Name", "Id", "Owner", "OwnerId",
        "CreatedDate", "LastModifiedDate", "CreatedBy", "LastModifiedBy",
        "Phone", "Email", "Industry", "Type", "AccountId",
        "BillingCity", "BillingState", "BillingCountry", "BillingPostalCode",
        "ShippingCity", "ShippingState", "ShippingCountry",
        "Status", "Priority", "Subject", "CaseNumber",
        "StageName", "Amount", "CloseDate",
        "Title", "Department", "MobilePhone",
        "RecordTypeId", "RecordType",
    }


def check_object(
    object_path: Path,
    flag_classic_overflow: bool,
) -> list[str]:
    """Return list of issue strings for one object's Search Layout config."""
    issues: list[str] = []
    api_name = object_api_name(object_path)
    layouts = parse_search_layouts(object_path)
    declared_fields = known_field_names_for_object(object_path)
    standard_allowlist = standard_fields_for_account_contact_case()

    if not layouts:
        # No <searchLayouts> block at all.
        issues.append(
            f"{api_name}: object has no <searchLayouts> block — Lightning "
            f"global search will render Name-only column. Configure Default "
            f"Layout (customSearchLayout) for at least 3 columns."
        )
        return issues

    lightning_default = layouts.get("customSearchLayout") or []
    if not lightning_default:
        issues.append(
            f"{api_name}: customSearchLayout (Lightning Default Layout) is "
            f"empty. Lightning global search falls back to Name-only column."
        )
    elif len(lightning_default) < MIN_SEARCH_RESULT_COLUMNS:
        issues.append(
            f"{api_name}: customSearchLayout has only "
            f"{len(lightning_default)} column(s); recommended minimum is "
            f"{MIN_SEARCH_RESULT_COLUMNS}."
        )

    # Column-count caps per slot.
    for slot, fields in layouts.items():
        if len(fields) > SEARCH_LAYOUT_MAX_COLUMNS:
            issues.append(
                f"{api_name}: layout '{slot}' has {len(fields)} columns "
                f"(max {SEARCH_LAYOUT_MAX_COLUMNS}); deploy will fail or "
                f"trailing columns will be dropped."
            )

    # Classic Lookup Dialog cap (only flag if requested).
    if flag_classic_overflow:
        lookup_dialog = layouts.get("lookupDialogsAdditionalFields") or []
        if len(lookup_dialog) > CLASSIC_LOOKUP_DIALOG_MAX:
            issues.append(
                f"{api_name}: lookupDialogsAdditionalFields has "
                f"{len(lookup_dialog)} columns; only the first "
                f"{CLASSIC_LOOKUP_DIALOG_MAX} render in Classic. Order by "
                f"priority or remove Classic from supported surfaces."
            )

    # Detect references to deleted fields in any slot.
    for slot, fields in layouts.items():
        for field in fields:
            if not field:
                continue
            # Standard fields and Name proxies allowed without further check.
            if field in standard_allowlist:
                continue
            if field.upper() == "NAME":
                continue
            # Cross-object references (Owner.Name, Account.Industry) are not
            # always declared in the local field metadata; skip dotted paths.
            if "." in field:
                continue
            # Standard-relationship Owner accessors are valid.
            if field.startswith("OWNER") or field.endswith("__r"):
                continue
            if declared_fields and field not in declared_fields:
                issues.append(
                    f"{api_name}: layout '{slot}' references field "
                    f"'{field}' which is not declared on this object. "
                    f"Likely a deleted-field rot — remove or update the "
                    f"Search Layout."
                )

    return issues


def check_synonym_groups(src_root: Path) -> list[str]:
    """If the source tree includes Synonym Group metadata, sanity check it."""
    issues: list[str] = []
    synonyms_dir = None
    for candidate in src_root.rglob("synonymDictionaries"):
        if candidate.is_dir():
            synonyms_dir = candidate
            break
    if synonyms_dir is None:
        return issues
    groups: list[Path] = list(synonyms_dir.rglob("*.synonymDictionary-meta.xml"))
    if len(groups) > SYNONYM_GROUP_MAX:
        issues.append(
            f"Synonym Groups: source tree contains {len(groups)} "
            f"synonymDictionary entries; org cap is {SYNONYM_GROUP_MAX}."
        )
    # Each dictionary may carry many <terms> groups. We do not unpack those
    # here since deploy will reject duplicates and the platform enforces the
    # 2000-active cap.
    return issues


def check_external_data_sources(src_root: Path) -> list[str]:
    """Flag external data sources where allowSearch is false or missing."""
    issues: list[str] = []
    eds_dir = None
    for candidate in src_root.rglob("externalDataSources"):
        if candidate.is_dir():
            eds_dir = candidate
            break
    if eds_dir is None:
        return issues
    for path in eds_dir.rglob("*.dataSource-meta.xml"):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        adapter = root.findtext(f"{NS}type") or "unknown"
        allow = root.findtext(f"{NS}allowSearch")
        if allow is None or allow.lower() != "true":
            issues.append(
                f"ExternalDataSource '{path.stem.removesuffix('.dataSource-meta')}' "
                f"(type={adapter}): allowSearch is not true. External objects "
                f"sourced from this data source will not appear in global search "
                f"until the flag is enabled and the adapter supports SOSL "
                f"(OData 2.0 / 4.0 supported; Cross-Org and most custom Apex "
                f"adapters do not)."
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(
            f"ERROR: Manifest directory not found: {manifest_dir}",
            file=sys.stderr,
        )
        return 2

    src_root = force_app_root(manifest_dir)
    if src_root is None:
        print(
            f"ERROR: No 'force-app/', 'src/', or 'unmanaged/' folder found "
            f"under {manifest_dir}. Provide --manifest-dir pointing at a "
            f"Salesforce project root.",
            file=sys.stderr,
        )
        return 2

    issues: list[str] = []

    for object_path in find_object_files(src_root):
        issues.extend(check_object(object_path, args.include_hybrid_classic))

    issues.extend(check_synonym_groups(src_root))
    issues.extend(check_external_data_sources(src_root))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
