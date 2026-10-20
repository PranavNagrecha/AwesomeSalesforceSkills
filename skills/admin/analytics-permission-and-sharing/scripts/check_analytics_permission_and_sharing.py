#!/usr/bin/env python3
"""Checker script for Analytics Permission and Sharing skill.

Reads three inputs under --manifest-dir:
- WaveApplication metadata (*.wapp): every <shares> entry is a FolderShare whose
  Required accessLevel is View, EditAllContents or Manage (api_meta 264
  L77522-77532; WaveApplication.shares, L142489). An unknown value is an ERROR;
  Manage or EditAllContents shared to the whole Organization is a WARN.
- WaveDataset metadata (*.wds): the type has no predicate or sharing-inheritance
  fields (api_meta 264 L142729-142739), so each dataset gets one WARN telling you
  to verify its row security outside the retrieve.
- Dataset-security JSON exports in this skill's own convention (an object with a
  "security" / "securityPredicate" / "rowLevelSecurity" key; this is not a
  Salesforce file format). Other JSON files are skipped.
  UNVERIFIED (2026-10-20): the 5,000-character predicate limit, the five-object
  sharing-inheritance list, the 3,000-record backup-predicate fallback and the
  all-rows-visible default these rules encode are not in the corpus.

Exit codes: ERROR (missing directory, unparseable XML/JSON, invalid accessLevel)
exits 1 always; WARN exits 0 unless --strict; nothing to check is one WARN, exit 0.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_permission_and_sharing.py --manifest-dir path/to/metadata [--strict]
    python3 check_analytics_permission_and_sharing.py --predicate "'OwnerId' == \\"\\$User.Id\\""
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
PREDICATE_MAX_LENGTH = 5000  # UNVERIFIED (2026-10-20), see docstring
SHARING_INHERITANCE_SUPPORTED_OBJECTS = {"Account", "Case", "Contact", "Lead", "Opportunity"}  # UNVERIFIED (2026-10-20)
LIKELY_WRONG_CASING = ["ownerid", "accountid", "contactid", "caseid", "leadid"]
FOLDER_SHARE_LEVELS = {"View", "EditAllContents", "Manage"}
SECURITY_KEYS = ("security", "securityPredicate", "rowLevelSecurity")
SKIP_PARTS = ("node_modules", "registry", "vector_index", ".git")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check CRM Analytics app sharing and dataset row-security inputs.")
    parser.add_argument("--manifest-dir", default=".", help="Directory to scan (default: current directory).")
    parser.add_argument("--predicate", default=None, help="A single security predicate string to validate.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any WARN finding.")
    return parser.parse_args()


def _text(el: ET.Element, tag: str) -> str:
    child = el.find(NS + tag)
    if child is None:
        child = el.find(tag)
    return (child.text or "").strip() if child is not None else ""


def check_predicate_string(predicate: str, name: str) -> list[str]:
    """Length and casing checks for one predicate. Returns WARN strings."""
    issues: list[str] = []
    if len(predicate) > PREDICATE_MAX_LENGTH:
        issues.append(f"WARN: {name}: predicate is {len(predicate)} characters, over the "
                      f"{PREDICATE_MAX_LENGTH}-character limit — refactor to a join-based predicate.")
    for wrong in LIKELY_WRONG_CASING:
        if f"'{wrong}'" in predicate:  # case-sensitive: the all-lowercase column name is literally present
            issues.append(f"WARN: {name}: predicate references column '{wrong}' in all-lowercase; "
                          f"copy the exact column name from the dataset schema.")
    return issues


def check_wapp(path: Path) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"ERROR: {path.name}: not parseable XML — {exc}"]
    issues: list[str] = []
    shares = root.findall(NS + "shares") + root.findall("shares")
    for share in shares:
        level, to_type = _text(share, "accessLevel"), _text(share, "sharedToType")
        if level not in FOLDER_SHARE_LEVELS:
            issues.append(f"ERROR: {path.name}: shares accessLevel {level!r} is not View, EditAllContents or Manage.")
        elif to_type == "Organization" and level in ("Manage", "EditAllContents"):
            issues.append(f"WARN: {path.name}: app shared to the whole Organization with {level} — "
                          f"grant View org-wide and Manage only to app owners.")
    return issues


def check_dataset_json(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        return [f"ERROR: {path.name}: could not parse JSON — {exc}"]
    if not isinstance(data, dict) or not any(k in data for k in SECURITY_KEYS):
        return []  # not a dataset-security export
    name = path.stem
    security = next((data[k] for k in SECURITY_KEYS if k in data), None)
    if not security:
        return [f"WARN: {name}: no row security configured — every licensed app user sees every row; "
                f"document it if intentional."]
    if isinstance(security, str):
        return check_predicate_string(security, name)
    issues: list[str] = []
    kind = str(security.get("predicateType") or security.get("type") or "").lower()
    if kind in ("sharinginheritance", "sharing_inheritance", "sharing"):
        obj = security.get("inheritedObject") or security.get("salesforceObject") or ""
        if obj and obj not in SHARING_INHERITANCE_SUPPORTED_OBJECTS:
            issues.append(f"WARN: {name}: sharing inheritance on {obj!r}, outside "
                          f"{sorted(SHARING_INHERITANCE_SUPPORTED_OBJECTS)} — use a predicate.")
        backup = str(security.get("backupPredicate") or security.get("fallbackPredicate") or "").strip()
        if not backup:
            issues.append(f"WARN: {name}: sharing inheritance with a blank backup predicate — set it to 'false'.")
        else:
            issues.extend(check_predicate_string(backup, name + " (backup predicate)"))
    predicate = security.get("predicate") or security.get("saqlPredicate") or ""
    if predicate:
        issues.extend(check_predicate_string(predicate, name))
    return issues


def check_manifest_dir(manifest_dir: Path) -> tuple[list[str], int]:
    issues: list[str] = []
    checked = 0
    for path in sorted(manifest_dir.rglob("*")):
        if not path.is_file() or any(p in path.parts for p in SKIP_PARTS):
            continue
        if path.suffix == ".wapp":
            issues.extend(check_wapp(path)); checked += 1
        elif path.suffix == ".wds":
            issues.append(f"WARN: {path.name}: WaveDataset metadata has no row-security fields "
                          f"(api_meta 264 L142729-142739) — verify its predicate or sharing inheritance "
                          f"in Analytics Studio."); checked += 1
        elif path.suffix == ".json":
            issues.extend(check_dataset_json(path)); checked += 1
    return issues, checked


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        return 1

    issues: list[str] = []
    if args.predicate is not None:
        issues.extend(check_predicate_string(args.predicate, "<provided predicate>"))
    dir_issues, checked = check_manifest_dir(manifest_dir)
    issues.extend(dir_issues)
    if checked == 0 and args.predicate is None:
        issues.append(f"WARN: {manifest_dir} holds no .wapp, .wds or .json files — nothing to check.")

    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(issue)
    if any(i.startswith("ERROR") for i in issues):
        return 1
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
