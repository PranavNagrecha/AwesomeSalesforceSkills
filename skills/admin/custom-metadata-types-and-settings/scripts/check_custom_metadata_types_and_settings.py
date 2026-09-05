#!/usr/bin/env python3
"""Checker for the Custom Metadata Types And Settings skill.

Reads a Salesforce metadata tree and reports Custom Settings mistakes that the
platform will not reject at deploy time but that change runtime behaviour.

Checks implemented (each grounded in an official guide; see
references/gotchas.md for the citation next to each rule):

  1. A CustomObject carrying <customSettingsType> with no <visibility> element.
     visibility defaults to Public (Metadata API Developer Guide, CustomObject).
  2. Use of <customSettingsVisibility>, superseded by <visibility> at API 34.0.
  3. Unsupported or suspicious field types on a custom setting: Location
     (geolocation is not supported in custom settings, Object Reference), and
     relationship fields.
  4. Apex calling hierarchy-only methods (getInstance() with no argument,
     getOrgDefaults()) on a setting declared List, or list-only methods
     (getAll(), getValues('literal')) on a setting declared Hierarchy.
  5. Runtime Apex issuing SOQL against a custom setting object -- that bypasses
     the application cache and costs a query (Apex Reference Guide).
  6. Test classes that read a custom setting without inserting its data and
     without SeeAllData=true (Apex Developer Guide: test isolation).
  7. A hierarchy custom setting inserted in @TestSetup and again in a test
     method, which throws DUPLICATE_VALUE in API 42.0 and later.

Stdlib only. Exit code 1 if any ERROR-severity finding is reported.

Usage:
    python3 check_custom_metadata_types_and_settings.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

RELATIONSHIP_TYPES = {"Lookup", "MasterDetail", "Hierarchy"}


class Finding:
    def __init__(self, severity: str, where: str, message: str) -> None:
        self.severity = severity
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity}: {self.where}: {self.message}"


def _child(element, tag):
    """Return the first direct child with `tag`, or None.

    Written as an explicit `is not None` test: a leaf Element is falsy, so
    `element.find(a) or element.find(b)` silently discards real matches.
    """
    if element is None:
        return None
    found = element.find(NS + tag)
    if found is None:
        found = element.find(tag)
    if found is None:
        return None
    return found


def _text(element, tag):
    node = _child(element, tag)
    if node is None:
        return None
    if node.text is None:
        return ""
    return node.text.strip()


def _children(element, tag):
    if element is None:
        return []
    out = list(element.findall(NS + tag))
    if not out:
        out = list(element.findall(tag))
    return out


# ---------------------------------------------------------------------------
# Metadata: custom setting definitions
# ---------------------------------------------------------------------------


def _object_api_name(path: Path) -> str:
    name = path.name
    for suffix in (".object-meta.xml", ".object"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def scan_object_files(manifest_dir: Path, findings: list[Finding]) -> dict[str, str]:
    """Return {objectApiName: 'List'|'Hierarchy'} for every custom setting found."""
    settings: dict[str, str] = {}

    candidates = list(manifest_dir.rglob("*.object-meta.xml")) + list(
        manifest_dir.rglob("*.object")
    )
    for path in sorted(set(candidates)):
        try:
            root = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            findings.append(Finding("ERROR", str(path), f"could not parse XML ({exc})"))
            continue

        cs_type = _text(root, "customSettingsType")
        legacy_visibility = _text(root, "customSettingsVisibility")
        if cs_type is None and legacy_visibility is None:
            continue  # a plain custom object or a custom metadata type

        api_name = _object_api_name(path)
        resolved_type = cs_type if cs_type else "Hierarchy"
        settings[api_name] = resolved_type

        if cs_type is None:
            findings.append(
                Finding(
                    "WARN",
                    str(path),
                    "custom setting has no <customSettingsType>; the Metadata API "
                    "defaults it to Hierarchy. State it explicitly so the Apex "
                    "access pattern is unambiguous.",
                )
            )
        elif cs_type not in ("List", "Hierarchy"):
            findings.append(
                Finding(
                    "ERROR",
                    str(path),
                    f"<customSettingsType>{cs_type}</customSettingsType> is not a valid "
                    "value; only List and Hierarchy are accepted.",
                )
            )

        if legacy_visibility is not None:
            findings.append(
                Finding(
                    "ERROR",
                    str(path),
                    "<customSettingsVisibility> is available only in API versions 17.0 "
                    "through 33.0. In 34.0 and later use <visibility> instead; a file "
                    "carrying only the old element deploys as Public.",
                )
            )

        if _text(root, "visibility") is None:
            findings.append(
                Finding(
                    "WARN",
                    str(path),
                    "no <visibility> element; it defaults to Public. Set it "
                    "deliberately (Public or Protected) -- and remember Protected only "
                    "restricts access inside a managed package installed in a "
                    "subscriber org.",
                )
            )

        # Fields declared inline (Metadata API format .object files)
        for field in _children(root, "fields"):
            _check_field(path, _text(field, "fullName") or "?", _text(field, "type"), findings)

    # Fields in DX source format live in objects/<Name>/fields/*.field-meta.xml
    for field_path in sorted(manifest_dir.rglob("fields/*.field-meta.xml")):
        owner = field_path.parent.parent.name
        if owner not in settings:
            continue
        try:
            root = ET.parse(field_path).getroot()
        except (ET.ParseError, OSError) as exc:
            findings.append(Finding("ERROR", str(field_path), f"could not parse XML ({exc})"))
            continue
        _check_field(
            field_path, _text(root, "fullName") or field_path.name, _text(root, "type"), findings
        )

    return settings


def _check_field(path: Path, field_name: str, field_type, findings: list[Finding]) -> None:
    if field_type is None:
        return
    if field_type == "Location":
        findings.append(
            Finding(
                "ERROR",
                f"{path}:{field_name}",
                "Geolocation (type Location) fields aren't supported in custom "
                "settings. Store latitude and longitude as two Number fields, or move "
                "the data to a custom metadata type or custom object.",
            )
        )
    elif field_type in RELATIONSHIP_TYPES:
        findings.append(
            Finding(
                "WARN",
                f"{path}:{field_name}",
                f"relationship field of type {field_type} on a custom setting. The "
                "Apex custom settings methods return cached rows and give you no way "
                "to traverse a relationship, so the value is only reachable by a SOQL "
                "query that bypasses the cache. UNVERIFIED (2026-09-05): the extracted "
                "guides do not state that relationship fields are rejected outright, "
                "only that geolocation is unsupported -- confirm in your own org.",
            )
        )


# ---------------------------------------------------------------------------
# Apex
# ---------------------------------------------------------------------------

_IS_TEST = re.compile(r"@\s*IsTest", re.IGNORECASE)
_SEE_ALL_DATA = re.compile(r"SeeAllData\s*=\s*true", re.IGNORECASE)
_TEST_SETUP = re.compile(r"@\s*TestSetup", re.IGNORECASE)


def _method_calls(content: str, api_name: str) -> dict[str, bool]:
    esc = re.escape(api_name)
    return {
        "getInstance_noarg": bool(re.search(esc + r"\.getInstance\s*\(\s*\)", content)),
        "getOrgDefaults": bool(re.search(esc + r"\.getOrgDefaults\s*\(", content)),
        "getAll": bool(re.search(esc + r"\.getAll\s*\(", content)),
        "getValues_literal": bool(
            re.search(esc + r"\.getValues\s*\(\s*['\"]", content)
        ),
        "any": bool(re.search(esc + r"\s*\.(getInstance|getValues|getAll|getOrgDefaults)\s*\(", content)),
        "referenced": bool(re.search(r"\b" + esc + r"\b", content)),
    }


def scan_apex(manifest_dir: Path, settings: dict[str, str], findings: list[Finding]) -> None:
    if not settings:
        return

    apex_files = sorted(
        set(list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger")))
    )
    for path in apex_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding("WARN", str(path), f"could not read file ({exc})"))
            continue

        is_test = bool(_IS_TEST.search(content))

        for api_name, cs_type in sorted(settings.items()):
            calls = _method_calls(content, api_name)
            if not calls["referenced"]:
                continue

            if cs_type == "List":
                if calls["getInstance_noarg"] or calls["getOrgDefaults"]:
                    findings.append(
                        Finding(
                            "ERROR",
                            f"{path}:{api_name}",
                            "hierarchy-only method (getInstance() with no argument or "
                            "getOrgDefaults()) called on a setting declared "
                            "customSettingsType=List. List settings expose getAll(), "
                            "getInstance(dataSetName) and getValues(dataSetName) only.",
                        )
                    )
            else:  # Hierarchy
                if calls["getAll"]:
                    findings.append(
                        Finding(
                            "ERROR",
                            f"{path}:{api_name}",
                            "getAll() called on a setting declared "
                            "customSettingsType=Hierarchy. getAll() is a list custom "
                            "setting method; use getInstance() / getInstance(id) so the "
                            "hierarchy actually resolves.",
                        )
                    )
                if calls["getValues_literal"]:
                    findings.append(
                        Finding(
                            "ERROR",
                            f"{path}:{api_name}",
                            "getValues('<literal>') called on a hierarchy setting. The "
                            "hierarchy overloads take a user Id or profile Id, and they "
                            "return only that level's row without merging -- a field set "
                            "solely at the org level reads back null.",
                        )
                    )

            # SOQL against the setting in runtime code bypasses the cache.
            soql = re.search(
                r"\[\s*SELECT\b[^\]]*\bFROM\s+" + re.escape(api_name) + r"\b",
                content,
                re.IGNORECASE | re.DOTALL,
            )
            if soql and not is_test:
                findings.append(
                    Finding(
                        "WARN",
                        f"{path}:{api_name}",
                        "SOQL against a custom setting does not use the application "
                        "cache and counts against the query governor limit. Use the "
                        "Apex custom settings methods in runtime code and keep SOQL for "
                        "verification or migration scripts.",
                    )
                )

            if is_test:
                inserts_data = bool(
                    re.search(
                        r"\b(insert|upsert)\b[^;]{0,200}?" + re.escape(api_name),
                        content,
                        re.IGNORECASE | re.DOTALL,
                    )
                    or re.search(
                        r"new\s+" + re.escape(api_name) + r"\s*\(", content
                    )
                )
                if calls["any"] and not inserts_data and not _SEE_ALL_DATA.search(content):
                    findings.append(
                        Finding(
                            "ERROR",
                            f"{path}:{api_name}",
                            "test reads a custom setting but never creates its data. "
                            "Custom settings data is treated as data for Apex test "
                            "isolation, so the test sees nothing. Insert the rows in "
                            "@TestSetup rather than reaching for SeeAllData=true.",
                        )
                    )

                if cs_type == "Hierarchy" and _TEST_SETUP.search(content):
                    setup_block = content.split("@TestSetup", 1)[1]
                    # crude split: everything after the setup method's closing brace
                    body_after = setup_block.split("@IsTest", 1)
                    if len(body_after) == 2:
                        setup_body, methods_body = body_after
                        seeded = re.search(
                            r"new\s+" + re.escape(api_name), setup_body
                        )
                        reinserted = re.search(
                            r"new\s+" + re.escape(api_name), methods_body
                        )
                        owner_re = re.compile(
                            r"SetupOwnerId\s*=\s*UserInfo\.getOrganizationId\s*\(\s*\)",
                            re.IGNORECASE,
                        )
                        if (
                            seeded
                            and reinserted
                            and owner_re.search(setup_body)
                            and owner_re.search(methods_body)
                        ):
                            findings.append(
                                Finding(
                                    "ERROR",
                                    f"{path}:{api_name}",
                                    "the org-default row (SetupOwnerId = "
                                    "UserInfo.getOrganizationId()) is inserted in both "
                                    "@TestSetup and a test method. In API 42.0 and later "
                                    "the second insert throws DUPLICATE_VALUE. Seed once "
                                    "and update, or use a different SetupOwnerId.",
                                )
                            )


# ---------------------------------------------------------------------------


def run(manifest_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not manifest_dir.exists():
        findings.append(Finding("ERROR", str(manifest_dir), "manifest directory not found"))
        return findings

    settings = scan_object_files(manifest_dir, findings)
    scan_apex(manifest_dir, settings, findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Custom Settings definition and Apex access "
            "mistakes: missing visibility, superseded customSettingsVisibility, "
            "unsupported field types, list/hierarchy method mismatches, cache-bypassing "
            "SOQL, and test-isolation failures."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata to scan (default: current directory).",
    )
    args = parser.parse_args()

    findings = run(Path(args.manifest_dir).resolve())

    if not findings:
        print("No issues found.")
        return 0

    for finding in findings:
        print(finding)

    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = len(findings) - errors
    print(f"\n{errors} error(s), {warns} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
