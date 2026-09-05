#!/usr/bin/env python3
"""Static auditor for a Salesforce data-export configuration.

Two kinds of check, both driven off one directory:

A. ARTEFACT CHECKS — the deployable files described in
   references/metadata-examples.md:

     1. export-inventory.json  (any *.json whose top level has an "objects" list)
        - every object names apiName, mode, filter, schedule, retentionDays, owner
        - mode "incremental" must watermark on SystemModstamp
        - retentionDays must not exceed policy.maxRetentionDays
        - containsPii true requires a real maskingNote
        - operation must be one of query / queryAll / extract / extract_all

     2. *.permissionset-meta.xml  (any XML whose root is PermissionSet)
        - userPermissions limited to the documented export permissions
        - objectPermissions must be read-only: no create / edit / delete /
          modifyAllRecords on an export operator

     3. process-conf.xml  (any XML whose root is <beans>)
        - every extract / extract_all bean has sfdc.extractionSOQL
        - dataAccess.type is csvWrite (the guide's sample bean is csvRead
          because it is an insert; copying it unchanged writes nothing)
        - dataAccess.name (the output path) is set
        - an encrypted sfdc.password has its process.encryptionKeyFile

B. RUNBOOK PROSE CHECKS — markdown/text describing the Data Export Service:

     4. mentions Data Export without the 48-hour download window
     5. calls it a "backup" without acknowledging the no-restore gap
     6. omits the Big Object / External Object / metadata exclusions
     7. recommends binary content with no named consumer requirement
     8. claims a scriptable / API trigger for the UI service

Stdlib only. Usage:

    python3 check_data_export_service.py [--manifest-dir PATH] [--quiet]

Default scans docs/, runbooks/, compliance/ and the current directory.
Exits 1 when any ERROR or WARN is reported, 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

DOC_GLOBS = ("**/*.md", "**/*.txt", "**/*.adoc", "**/*.rst")
JSON_GLOB = "**/*.json"
XML_GLOBS = ("**/*.xml",)
DEFAULT_ROOTS = ("docs", "runbooks", "compliance", ".")
SKIP_DIRS = {"node_modules", ".git", "vendor", "__pycache__", ".sfdx", "dist", "build"}

# User permissions an export operator legitimately needs.
#   ApiEnabled  — the guide's own userPermissions example (api_meta.txt:95216)
#   WeeklyExport — the Weekly Data Export checkbox; API name UNVERIFIED, see
#                  references/metadata-examples.md § 2
ALLOWED_USER_PERMISSIONS = {"ApiEnabled", "WeeklyExport"}

# Flags that must never be true on an export-operator permission set.
FORBIDDEN_OBJECT_FLAGS = ("allowCreate", "allowEdit", "allowDelete", "modifyAllRecords")

VALID_OPERATIONS = {"query", "queryAll", "extract", "extract_all"}
EXTRACT_OPERATIONS = {"extract", "extract_all"}
REQUIRED_OBJECT_KEYS = ("apiName", "mode", "filter", "schedule", "retentionDays", "owner")


class Report:
    """Collects findings and decides the exit code."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warns: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warns.append(f"{where}: {message}")

    @property
    def failed(self) -> bool:
        return bool(self.errors or self.warns)


# ---------------------------------------------------------------- discovery


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a Salesforce data-export configuration: inventory JSON, "
        "operator permission set, Data Loader process-conf.xml, and runbook prose.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory holding the export artefacts and runbooks "
        "(default: scans docs/, runbooks/, compliance/, current dir).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the per-file OK lines; print findings and the summary only.",
    )
    return parser.parse_args()


def candidate_roots(arg: str | None) -> list[Path]:
    if arg:
        root = Path(arg)
        if not root.is_dir():
            print(f"ERROR: --manifest-dir {arg} is not a directory", file=sys.stderr)
            sys.exit(2)
        return [root]
    found = [Path(name) for name in DEFAULT_ROOTS if Path(name).is_dir()]
    return found or [Path(".")]


def iter_files(roots: Iterable[Path], globs: Iterable[str]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for root in roots:
        for pattern in globs:
            for path in sorted(root.glob(pattern)):
                if path in seen or not path.is_file():
                    continue
                if SKIP_DIRS & set(path.parts):
                    continue
                seen.add(path)
                out.append(path)
    return out


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# ------------------------------------------------------------- XML helpers


def strip_ns(tag: str) -> str:
    """'{http://…/metadata}userPermissions' -> 'userPermissions'."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child(elem: ET.Element, tag: str) -> ET.Element | None:
    """First direct child with the given local name, or None.

    Never rely on the truthiness of an Element: an element with no children
    is falsy even when it exists, so `elem.find(a) or elem.find(b)` silently
    discards a real leaf node. Everything here tests `is not None`.
    """
    for kid in elem:
        if strip_ns(kid.tag) == tag:
            return kid
    return None


def child_text(elem: ET.Element, tag: str) -> str | None:
    node = child(elem, tag)
    if node is None:
        return None
    if node.text is None:
        return ""
    return node.text.strip()


def children(elem: ET.Element, tag: str) -> list[ET.Element]:
    return [kid for kid in elem if strip_ns(kid.tag) == tag]


def parse_xml(path: Path) -> ET.Element | None:
    """Parse, tolerating the Spring DOCTYPE in process-conf.xml."""
    text = read_text(path)
    text = re.sub(r"<!DOCTYPE[^>\[]*(\[[^\]]*\])?[^>]*>", "", text, count=1, flags=re.S)
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return None


# ---------------------------------------------- 1. export-inventory.json


def check_inventory(path: Path, report: Report) -> bool:
    """Return True if this file was an export inventory (checked or rejected)."""
    try:
        data = json.loads(read_text(path))
    except (json.JSONDecodeError, ValueError):
        return False
    if not isinstance(data, dict) or not isinstance(data.get("objects"), list):
        return False

    rel = path.as_posix()
    policy = data.get("policy") if isinstance(data.get("policy"), dict) else {}
    max_retention = policy.get("maxRetentionDays")
    watermark = policy.get("incrementalWatermarkField") or "SystemModstamp"

    if max_retention is None:
        report.warn(
            rel,
            "policy.maxRetentionDays is not declared, so no per-object retention "
            "can be checked against a ceiling. Declare the org's policy here.",
        )

    if not data["objects"]:
        report.error(rel, "'objects' is empty — an export inventory with no objects "
                          "documents nothing.")
        return True

    for index, obj in enumerate(data["objects"]):
        label = f"{rel} objects[{index}]"
        if not isinstance(obj, dict):
            report.error(label, "entry is not an object.")
            continue
        name = obj.get("apiName") or f"<unnamed #{index}>"
        label = f"{rel} objects[{index}] ({name})"

        for key in REQUIRED_OBJECT_KEYS:
            if key not in obj:
                report.error(label, f"missing required key '{key}'. Every exported "
                                    "object needs a filter, schedule, retention and owner.")
            elif key != "filter" and (obj[key] is None or obj[key] == ""):
                report.error(label, f"'{key}' is empty. 'filter' may be null for a full "
                                    "export; the others may not.")

        mode = obj.get("mode")
        if mode not in (None, "full", "incremental"):
            report.error(label, f"mode '{mode}' is not 'full' or 'incremental'.")

        filt = obj.get("filter") or ""
        soql = obj.get("soql") or ""
        if mode == "incremental":
            if watermark.lower() not in filt.lower():
                report.error(
                    label,
                    f"incremental export does not watermark on {watermark}. "
                    "LastModifiedDate records only user edits; SystemModstamp also "
                    "records automated processes, so a LastModifiedDate watermark "
                    "silently drops trigger- and roll-up-driven changes.",
                )
            elif "<" not in filt:
                report.warn(
                    label,
                    "incremental filter has no upper bound. An open-ended window "
                    "widens until it stops being selective enough for the "
                    "SystemModstamp standard index, then full-scans.",
                )

        operation = obj.get("operation")
        if operation is not None and operation not in VALID_OPERATIONS:
            report.error(
                label,
                f"operation '{operation}' is not one of {sorted(VALID_OPERATIONS)}.",
            )

        for field_name, value in (("filter", filt), ("soql", soql)):
            upper = value.upper()
            if "ORDER BY" in upper or re.search(r"\bLIMIT\b", upper):
                report.warn(
                    label,
                    f"'{field_name}' contains ORDER BY or LIMIT, which disables PK "
                    "chunking on a Bulk API 2.0 query job. Sort and cap downstream.",
                )

        retention = obj.get("retentionDays")
        if isinstance(retention, bool) or not isinstance(retention, (int, float)):
            if retention is not None:
                report.error(label, "retentionDays must be a number of days.")
        elif retention <= 0:
            report.error(label, "retentionDays must be greater than zero.")
        elif isinstance(max_retention, (int, float)) and retention > max_retention:
            report.error(
                label,
                f"retentionDays {retention} exceeds policy.maxRetentionDays "
                f"{max_retention}.",
            )

        if obj.get("containsPii") is True:
            note = (obj.get("maskingNote") or "").strip()
            if len(note) < 20:
                report.error(
                    label,
                    "containsPii is true but maskingNote is missing or too short to "
                    "say anything. Name the transform and the boundary it happens at.",
                )

    return True


# ------------------------------------------- 2. PermissionSet metadata XML


def check_permission_set(path: Path, root: ET.Element, report: Report) -> None:
    rel = path.as_posix()

    granted = []
    for perm in children(root, "userPermissions"):
        name = child_text(perm, "name")
        enabled = (child_text(perm, "enabled") or "").lower()
        if name is None:
            report.error(rel, "a <userPermissions> block has no <name>.")
            continue
        if enabled != "true":
            continue
        granted.append(name)
        if name not in ALLOWED_USER_PERMISSIONS:
            report.error(
                rel,
                f"grants user permission '{name}', which is not one of the export "
                f"permissions this skill documents ({sorted(ALLOWED_USER_PERMISSIONS)}). "
                "The Data Loader guide names 'Read on the records' as the export "
                "permission — not ViewAllData, ModifyAllData or Manage Users.",
            )

    if not granted:
        report.warn(
            rel,
            "grants no user permissions. An export operator using the API or Data "
            "Loader needs ApiEnabled.",
        )
    elif "ApiEnabled" not in granted:
        report.warn(
            rel,
            "does not grant ApiEnabled. Bulk API 2.0 and Data Loader both need it.",
        )

    object_blocks = children(root, "objectPermissions")
    if not object_blocks:
        report.warn(rel, "grants no objectPermissions — nothing is exportable through it.")

    for block in object_blocks:
        obj_name = child_text(block, "object") or "<unnamed>"
        where = f"{rel} objectPermissions[{obj_name}]"

        read = (child_text(block, "allowRead") or "").lower()
        if read != "true":
            report.error(where, "allowRead is not true, so this object cannot be exported.")

        for flag in FORBIDDEN_OBJECT_FLAGS:
            value = child_text(block, flag)
            if value is not None and value.lower() == "true":
                report.error(
                    where,
                    f"{flag} is true. An export operator must be read-only — an "
                    "operator that can write is an operator that can destroy the "
                    "thing being archived.",
                )


# --------------------------------------- 3. Data Loader process-conf.xml


def bean_entries(bean: ET.Element) -> dict[str, str]:
    """Flatten <property name="configOverrideMap"><map><entry key= value=/>."""
    entries: dict[str, str] = {}
    for prop in bean.iter():
        if strip_ns(prop.tag) != "entry":
            continue
        key = prop.get("key")
        if key:
            entries[key] = prop.get("value") or (prop.text or "").strip()
    return entries


def check_process_conf(path: Path, root: ET.Element, report: Report) -> None:
    rel = path.as_posix()
    beans = [b for b in root.iter() if strip_ns(b.tag) == "bean"]
    if not beans:
        report.error(rel, "no <bean> found — this is not a usable process-conf.xml.")
        return

    extract_beans = 0
    for bean in beans:
        bean_id = bean.get("id") or "<unnamed bean>"
        where = f"{rel} bean[{bean_id}]"
        entries = bean_entries(bean)
        operation = (entries.get("process.operation") or "").strip()

        if operation and operation != operation.lower():
            report.error(
                where,
                f"process.operation '{operation}' must be lowercase.",
            )
        if operation.lower() not in EXTRACT_OPERATIONS:
            continue
        extract_beans += 1

        soql = (entries.get("sfdc.extractionSOQL") or "").strip()
        if not soql:
            report.error(
                where,
                "an extract bean has no sfdc.extractionSOQL, so it has nothing to export.",
            )
        else:
            upper = soql.upper()
            if "ORDER BY" in upper or re.search(r"\bLIMIT\b", upper):
                report.warn(
                    where,
                    "sfdc.extractionSOQL contains ORDER BY or LIMIT. Sort and cap "
                    "downstream instead.",
                )
            if re.search(r"\(\s*SELECT\b", upper):
                report.error(
                    where,
                    "sfdc.extractionSOQL contains a nested/child query. Data Loader "
                    "does not support nested queries or querying child objects.",
                )

        dao_type = (entries.get("dataAccess.type") or "").strip()
        if dao_type != "csvWrite":
            report.error(
                where,
                f"dataAccess.type is '{dao_type or '<missing>'}' on an extract bean; "
                "it must be csvWrite. The guide's sample bean is csvRead because it "
                "is an insert — copying it unchanged produces no output file.",
            )

        if not (entries.get("dataAccess.name") or "").strip():
            report.error(
                where,
                "dataAccess.name (the output CSV path) is not set.",
            )

        if entries.get("sfdc.password") and not (
            entries.get("process.encryptionKeyFile") or ""
        ).strip():
            report.error(
                where,
                "sfdc.password is set without process.encryptionKeyFile. Batch-mode "
                "passwords must be encrypted, and an encrypted value cannot be "
                "decrypted without its key file.",
            )

        if (entries.get("sfdc.debugMessages") or "").lower() == "true":
            report.warn(
                where,
                "sfdc.debugMessages is true. Debug messages can contain a session id "
                "and the trace file has no size limit — never on an export host.",
            )

    if extract_beans == 0:
        report.warn(
            rel,
            "contains beans but none with process.operation extract or extract_all.",
        )


# ------------------------------------------------- 4-8. runbook prose scan

DATA_EXPORT_MENTION = re.compile(
    r"\b(data\s*export\s*service|weekly\s*export|monthly\s*export|setup\s*[->/–]\s*data\s*export)\b",
    re.IGNORECASE,
)
HOUR_48_MENTION = re.compile(r"\b48[-\s]?hour|forty[-\s]?eight\s*hour\b", re.IGNORECASE)

BACKUP_CLAIM = re.compile(
    r"\b(backup\s*strategy|our\s*backup|nightly\s*backup|weekly\s*backup|backup\s*plan|disaster\s*recovery\s*backup)\b",
    re.IGNORECASE,
)
RESTORE_GAP_ACK = re.compile(
    r"\b(no\s*restore|cannot\s*restore|evidence\s*archive|backup\s*and\s*restore\s*\(?separate|managed\s*backup\s*product)\b",
    re.IGNORECASE,
)

BIG_OBJECT_GAP_ACK = re.compile(
    r"\b(big\s*object|external\s*object|metadata\s*excluded|metadata\s*api\s*\(?separately|skipped\s*by\s*data\s*export)\b",
    re.IGNORECASE,
)

BINARY_INCLUDE = re.compile(
    r"\b(include\s*(?:all\s*)?(?:images|documents|attachments|salesforce\s*files|chatter\s*files|binary))\b",
    re.IGNORECASE,
)
BINARY_JUSTIFY = re.compile(
    r"\b(legal\s*hold|discovery|legal\s*request|content\s*replication|specific\s*consumer\s*requirement|file\s*retention\s*regulation)\b",
    re.IGNORECASE,
)

API_CLAIM = re.compile(
    r"\b(sf\s+data\s+export\s+run|/dataExports?/|DataExport(?:Service)?(?:Client|Api)|trigger.{0,30}via.{0,30}(rest|cli|sfdx|api))\b",
    re.IGNORECASE,
)


def check_runbook(path: Path, report: Report) -> bool:
    text = read_text(path)
    if not DATA_EXPORT_MENTION.search(text):
        return False
    rel = path.as_posix()

    if not HOUR_48_MENTION.search(text):
        report.warn(
            rel,
            "mentions Data Export but does not mention the 48-hour download window. "
            "The window must be in any operational doc.",
        )

    if BACKUP_CLAIM.search(text) and not RESTORE_GAP_ACK.search(text):
        report.warn(
            rel,
            "calls this a 'backup' without acknowledging the no-restore gap. Must "
            "reference 'evidence archive', 'no restore', or 'Backup and Restore "
            "(separate paid product)'.",
        )

    if not BIG_OBJECT_GAP_ACK.search(text):
        report.warn(
            rel,
            "does not acknowledge Big Object / External Object / metadata exclusions. "
            "These are silently skipped by Data Export.",
        )

    if BINARY_INCLUDE.search(text) and not BINARY_JUSTIFY.search(text):
        report.warn(
            rel,
            "recommends including binary content without naming a consumer "
            "requirement (legal hold, discovery, file replication). Default binary "
            "checkboxes to OFF.",
        )

    if API_CLAIM.search(text):
        report.warn(
            rel,
            "claims Data Export can be triggered via API/CLI. The Setup service is "
            "UI-only — use Bulk API 2.0 for programmatic extracts.",
        )

    return True


# ------------------------------------------------------------------- main


def main() -> int:
    args = parse_args()
    roots = candidate_roots(args.manifest_dir)
    report = Report()

    inventories = permission_sets = process_confs = runbooks = 0

    for path in iter_files(roots, (JSON_GLOB,)):
        if check_inventory(path, report):
            inventories += 1

    for path in iter_files(roots, XML_GLOBS):
        root = parse_xml(path)
        if root is None:
            continue
        tag = strip_ns(root.tag)
        if tag == "PermissionSet":
            permission_sets += 1
            check_permission_set(path, root, report)
        elif tag == "beans":
            process_confs += 1
            check_process_conf(path, root, report)

    for path in iter_files(roots, DOC_GLOBS):
        if check_runbook(path, report):
            runbooks += 1

    scanned = inventories + permission_sets + process_confs + runbooks
    where = ", ".join(str(r) for r in roots)

    if scanned == 0:
        print(
            f"OK: nothing to check under {where} — no export inventory, permission "
            "set, process-conf.xml, or Data Export runbook found."
        )
        return 0

    if not args.quiet:
        print(
            f"Scanned under {where}: {inventories} inventory file(s), "
            f"{permission_sets} permission set(s), {process_confs} process-conf "
            f"file(s), {runbooks} runbook(s)."
        )

    for issue in report.errors:
        print(f"ERROR: {issue}", file=sys.stderr)
    for issue in report.warns:
        print(f"WARN: {issue}", file=sys.stderr)

    if not report.failed:
        print("OK: no issues found.")
        return 0

    print(
        f"\n{len(report.errors)} error(s), {len(report.warns)} warning(s).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
