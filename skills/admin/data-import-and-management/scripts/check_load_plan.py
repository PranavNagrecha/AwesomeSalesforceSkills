#!/usr/bin/env python3
"""Validate the artefacts of an admin-run Salesforce data load.

Two modes, both stdlib-only:

  CSV mode (default)
      check_load_plan.py accounts.csv --external-id Legacy_Account_Id__c --required Name
      Required columns, blank values, duplicate/blank External IDs.

  Config mode
      check_load_plan.py --manifest-dir C:/Migration/Config
      Data Loader `process-conf.xml` beans and their `.sdl` mapping files.

Grounding for the config-mode thresholds (Data Loader Guide, Summer '26 / v62 PDF,
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf):

  * "The maximum import batch size is 200 records for SOAP API and 10000 records for
    Bulk API. ... If the Use Bulk API 2.0 option is selected, then neither batch size is
    used because Bulk API 2.0 handles batch size automatically."  (Settings reference)
    The command-line parameter table for `sfdc.loadBatchSize` still states a maximum of
    200 and recommends 50-100; that sentence describes the SOAP path only. This checker
    applies 200 when Bulk API is off and 10,000 when it is on, and reports an INFO when a
    batch size is set at all under Bulk API 2.0.
  * "Processing in parallel can cause database contention. When contention is severe, the
    load can fail."  (sfdc.bulkApiSerialMode)
  * `sfdc.externalIdField` is "used in upsert operations".
  * `sfdc.assignmentRule` sample value `03Mc00000026J7w` - a Salesforce Id, not a name.
  * The password "must be encrypted before you add it to the process-conf.xml file", via
    `encrypt.bat` against a key file named by `process.encryptionKeyFile`.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SEVERITY_WEIGHTS = {
    "CRITICAL": 20,
    "ERROR": 20,
    "HIGH": 10,
    "WARN": 10,
    "MEDIUM": 5,
    "LOW": 1,
    "INFO": 0,
    "REVIEW": 0,
}

# Data Loader Guide, Settings reference: 200 for SOAP API, 10000 for Bulk API.
MAX_BATCH_SOAP = 200
MAX_BATCH_BULK = 10000

# 15-character case-sensitive or 18-character case-insensitive alphanumeric.
SALESFORCE_ID = re.compile(r"^[a-zA-Z0-9]{15}$|^[a-zA-Z0-9]{18}$")

# `encrypt.bat` emits a hex string; the guide's sample value is `e8a68b73992a7a54`.
ENCRYPTED_PASSWORD = re.compile(r"^[0-9a-fA-F]{16,}$")

VALID_OPERATIONS = {
    "extract",
    "extract_all",
    "insert",
    "update",
    "upsert",
    "delete",
    "hard_delete",
}


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    # INFO / REVIEW findings are notes, not failures; they must not break a pipeline.
    blocking = [i for i in normalized if SEVERITY_WEIGHTS.get(i["severity"], 0) > 0]
    return 1 if blocking else 0


def audit_csv(path: Path, required: list[str], external_id: str | None) -> list[str]:
    findings: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in required if column not in fieldnames]
        for column in missing_columns:
            findings.append(f"HIGH {path}: missing required column `{column}`")

        seen_external_ids: set[str] = set()
        for index, row in enumerate(reader, start=2):
            for column in required:
                if column in row and not (row.get(column) or "").strip():
                    findings.append(f"MEDIUM {path}:{index}: blank value in required column `{column}`")

            if external_id:
                value = (row.get(external_id) or "").strip()
                if not value:
                    findings.append(f"HIGH {path}:{index}: blank External ID in `{external_id}`")
                elif value in seen_external_ids:
                    findings.append(f"HIGH {path}:{index}: duplicate External ID `{value}`")
                else:
                    seen_external_ids.add(value)

    return findings


def first_child(element, *tags):
    """Return the first child matching any of `tags`.

    A leaf ElementTree Element is falsy, so `element.find(a) or element.find(b)` silently
    discards a real but empty match. Test `is not None` explicitly.
    """
    for tag in tags:
        found = element.find(tag)
        if found is not None:
            return found
    return None


def bean_entries(bean) -> dict[str, str]:
    """Flatten a ProcessRunner bean's configOverrideMap into {key: value}."""
    entries: dict[str, str] = {}
    for prop in bean.findall("property"):
        if prop.get("name") != "configOverrideMap":
            continue
        mapping = first_child(prop, "map", "props")
        if mapping is None:
            continue
        for entry in mapping.findall("entry"):
            key = entry.get("key")
            if key is None:
                continue
            value = entry.get("value")
            if value is None:
                value = (entry.text or "").strip()
            entries[key] = value.strip()
    return entries


def as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1", "on"}


def audit_process_conf(path: Path) -> tuple[list[str], list[tuple[str, str]]]:
    """Audit one process-conf.xml. Returns (findings, [(bean_id, mapping_file), ...])."""
    findings: list[str] = []
    mappings: list[tuple[str, str]] = []

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        return [f"ERROR {path}: not well-formed XML ({error})"], []

    beans = [b for b in root.iter("bean") if "ProcessRunner" in (b.get("class") or "")]
    if not beans:
        return [f"INFO {path}: no ProcessRunner bean found; skipped"], []

    for bean in beans:
        bean_id = bean.get("id") or "(unnamed bean)"
        where = f"{path}:{bean_id}"
        cfg = bean_entries(bean)

        operation = cfg.get("process.operation", "").strip()
        use_bulk = as_bool(cfg.get("sfdc.useBulkApi", ""))
        use_bulk_v2 = as_bool(cfg.get("sfdc.useBulkApiV2", "")) or as_bool(
            cfg.get("sfdc.useBulkV2Api", "")
        )

        if operation and operation not in VALID_OPERATIONS:
            findings.append(
                f"ERROR {where}: process.operation `{operation}` is not one of "
                f"{sorted(VALID_OPERATIONS)} (values are lowercase)"
            )

        # 1. Batch size against the ceiling for the API actually enabled.
        raw_batch = cfg.get("sfdc.loadBatchSize", "").strip()
        if raw_batch:
            try:
                batch = int(raw_batch)
            except ValueError:
                findings.append(
                    f"ERROR {where}: sfdc.loadBatchSize `{raw_batch}` is not an integer"
                )
            else:
                if use_bulk_v2:
                    findings.append(
                        f"INFO {where}: sfdc.loadBatchSize={batch} is ignored under Bulk API 2.0, "
                        "which batches automatically; the value is misleading, not harmful"
                    )
                elif use_bulk and batch > MAX_BATCH_BULK:
                    findings.append(
                        f"ERROR {where}: sfdc.loadBatchSize={batch} exceeds the documented Bulk API "
                        f"maximum of {MAX_BATCH_BULK}"
                    )
                elif not use_bulk and batch > MAX_BATCH_SOAP:
                    findings.append(
                        f"ERROR {where}: sfdc.loadBatchSize={batch} exceeds the documented SOAP API "
                        f"maximum of {MAX_BATCH_SOAP}; sfdc.useBulkApi is not true, so this is the "
                        "SOAP path"
                    )
                elif use_bulk and batch <= MAX_BATCH_SOAP:
                    findings.append(
                        f"INFO {where}: sfdc.loadBatchSize={batch} with Bulk API on wastes the "
                        f"batch allocation; the Bulk API ceiling is {MAX_BATCH_BULK}"
                    )

        # 2. Bulk API on with no explicit serial-mode decision.
        if use_bulk and "sfdc.bulkApiSerialMode" not in cfg:
            findings.append(
                f"INFO {where}: sfdc.useBulkApi is true but sfdc.bulkApiSerialMode is unset "
                "(defaults to parallel); record the decision - parallel contention on a shared "
                "parent can fail the load"
            )

        # 3. An upsert key configured on an operation that cannot use it.
        external_id = cfg.get("sfdc.externalIdField", "").strip()
        if external_id and operation and operation != "upsert":
            findings.append(
                f"WARN {where}: sfdc.externalIdField=`{external_id}` is set on a "
                f"`{operation}` operation, where it is ignored; a re-run will not match, it "
                "will duplicate"
            )
        if operation == "upsert" and not external_id:
            findings.append(
                f"WARN {where}: process.operation is upsert but sfdc.externalIdField is empty; "
                "matching falls back to the record Id"
            )

        # 5. Assignment rule must be an Id, not a name.
        assignment = cfg.get("sfdc.assignmentRule", "").strip()
        if assignment and not SALESFORCE_ID.match(assignment):
            findings.append(
                f"WARN {where}: sfdc.assignmentRule=`{assignment}` is not shaped like a 15- or "
                "18-character Salesforce Id (sample value `03Mc00000026J7w`); query AssignmentRule "
                "for the Id"
            )
        if assignment and operation in {"insert", "update", "upsert"}:
            findings.append(
                f"INFO {where}: sfdc.assignmentRule is set, so it overrides any OwnerId column in "
                "the CSV for Cases and Leads"
            )

        # 6. Password must be the encrypt.bat output, with a key file beside it.
        password = cfg.get("sfdc.password", "").strip()
        if password:
            if not ENCRYPTED_PASSWORD.match(password):
                findings.append(
                    f"WARN {where}: sfdc.password does not look like encrypt.bat output "
                    "(expected a hex string); a plaintext password must never be committed"
                )
            if not cfg.get("process.encryptionKeyFile", "").strip():
                findings.append(
                    f"WARN {where}: sfdc.password is set but process.encryptionKeyFile is missing; "
                    "the encrypted value cannot be decrypted without its key file"
                )

        # Hard delete is only reachable through the Bulk APIs.
        if operation == "hard_delete" and not (use_bulk or use_bulk_v2):
            findings.append(
                f"ERROR {where}: process.operation=hard_delete requires sfdc.useBulkApi (or Bulk "
                "API 2.0) to be enabled"
            )

        mapping_file = cfg.get("process.mappingFile", "").strip()
        if mapping_file:
            mappings.append((where, mapping_file))
        elif operation in {"insert", "update", "upsert"}:
            findings.append(
                f"INFO {where}: no process.mappingFile; the CSV headers must match field API names "
                "exactly"
            )

    return findings, mappings


def parse_sdl(path: Path) -> tuple[list[str], list[tuple[int, str, str]]]:
    """Parse an .sdl mapping file into (findings, [(line_no, source, target), ...])."""
    findings: list[str] = []
    pairs: list[tuple[int, str, str]] = []

    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        return [f"ERROR {path}: cannot read mapping file ({error})"], []

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if "=" not in line:
            findings.append(
                f"ERROR {path}:{line_no}: `{line}` has no `=` separator; every mapping line pairs a "
                "source with a destination"
            )
            continue
        source, _, target = line.partition("=")
        source = source.strip()
        target = target.strip()
        if not target:
            # Documented idiom: an empty destination drops the source column.
            continue
        for field in (part.strip() for part in target.split(",")):
            if field:
                pairs.append((line_no, source, field))

    return findings, pairs


def audit_sdl(path: Path) -> list[str]:
    findings, pairs = parse_sdl(path)

    # 4. The same destination field written twice - Data Loader will not say which won.
    seen: dict[str, int] = {}
    for line_no, source, field in pairs:
        key = field.lower()
        if key in seen:
            findings.append(
                f"ERROR {path}:{line_no}: destination field `{field}` is already mapped on line "
                f"{seen[key]}; which mapping wins is undefined"
            )
        else:
            seen[key] = line_no

    sources: dict[str, int] = {}
    for line_no, source, _field in pairs:
        if source.startswith('"'):
            continue  # a constant may legitimately feed several fields
        key = source.lower()
        if key in sources and sources[key] != line_no:
            findings.append(
                f"INFO {path}:{line_no}: source column `{source}` is mapped again (first on line "
                f"{sources[key]}); intentional fan-out, or a copy-paste error?"
            )
        else:
            sources[key] = line_no

    if not pairs and not findings:
        findings.append(f"WARN {path}: mapping file contains no mappings")

    return findings


def audit_manifest_dir(directory: Path) -> tuple[list[str], int]:
    findings: list[str] = []
    scanned = 0

    xml_files = sorted(p for p in directory.rglob("*.xml") if p.is_file())
    sdl_files = sorted(p for p in directory.rglob("*.sdl") if p.is_file())

    if not xml_files and not sdl_files:
        return [f"WARN {directory}: no *.xml or *.sdl files found"], 0

    referenced: set[str] = set()
    for xml_file in xml_files:
        scanned += 1
        conf_findings, mappings = audit_process_conf(xml_file)
        findings.extend(conf_findings)
        for where, mapping_file in mappings:
            name = Path(mapping_file.replace("\\", "/")).name
            referenced.add(name.lower())
            local = next((s for s in sdl_files if s.name.lower() == name.lower()), None)
            if local is None:
                findings.append(
                    f"WARN {where}: process.mappingFile points at `{mapping_file}`, which is not "
                    f"in {directory}; the mapping could not be checked"
                )

    for sdl_file in sdl_files:
        scanned += 1
        findings.extend(audit_sdl(sdl_file))
        if referenced and sdl_file.name.lower() not in referenced:
            findings.append(
                f"INFO {sdl_file}: not referenced by any process.mappingFile in {directory}"
            )

    return findings, scanned


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check data-load artefacts: CSV source files, or Data Loader process-conf.xml "
            "beans and .sdl mapping files."
        )
    )
    parser.add_argument("files", nargs="*", help="CSV files to audit")
    parser.add_argument("--required", nargs="*", default=[], help="Required column names")
    parser.add_argument("--external-id", help="Column used as External ID / upsert key")
    parser.add_argument(
        "--manifest-dir",
        help="Directory holding process-conf.xml and .sdl mapping files to audit",
    )
    args = parser.parse_args()

    if not args.files and not args.manifest_dir:
        parser.error("provide CSV files, --manifest-dir, or both")

    findings: list[str] = []
    scanned = 0

    if args.manifest_dir:
        directory = Path(args.manifest_dir)
        if not directory.is_dir():
            findings.append(f"ERROR {directory}: --manifest-dir is not a directory")
        else:
            config_findings, config_scanned = audit_manifest_dir(directory)
            findings.extend(config_findings)
            scanned += config_scanned

    for value in args.files:
        path = Path(value)
        if not path.is_file():
            findings.append(f"HIGH {path}: file not found")
            continue
        scanned += 1
        findings.extend(audit_csv(path, args.required, args.external_id))

    summary = f"Scanned {scanned} load artefact(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
