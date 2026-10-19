#!/usr/bin/env python3
"""Checker for the consent-data-model-health skill.

Point --manifest-dir at a folder holding SOQL exports as JSON (a list of records,
{"records": [...]}, or the sf CLI --json shape {"result": {"records": [...]}})
and/or Apex source (.cls, .trigger). Field rules come from the Object Reference
entries for AuthorizationFormConsent and AuthorizationFormDataUse.

Severity:
  ERROR  AuthorizationFormConsent row with Status outside Rejected/Seen/Signed;
         row missing AuthorizationFormTextId, ConsentGiverId,
         ConsentCapturedDateTime, ConsentCapturedSource, or
         ConsentCapturedSourceType; ConsentCapturedSourceType outside the
         picklist; AuthorizationFormDataUse row without AuthorizationFormId or
         DataUsePurposeId; Apex that filters through
         AuthorizationFormText.AuthorizationFormDataUses (data uses hang off the
         form, not the text).
         A JSON file that cannot be read or parsed is also an ERROR.
  WARN   ConsentGiver.Type different from --giver-type (default Individual);
         a consent export missing one of the required columns;
         consent export without ConsentGiver.Type (giver type can't be checked);
         Apex that sets ConsentCapturedSource but never ConsentCapturedSourceType.

Exit codes: 0 clean or WARN only; 1 on ERROR, missing directory, or WARN with
--strict. An empty directory prints a WARN and exits 0. Stdlib only.

Export example:
    SELECT Id, ConsentGiverId, ConsentGiver.Type, Status, ConsentCapturedSource,
           ConsentCapturedSourceType, ConsentCapturedDateTime, AuthorizationFormTextId
    FROM AuthorizationFormConsent

Usage:
    python3 check_consent_data_model_health.py --manifest-dir path/to/export [--giver-type Individual] [--strict]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

STATUS_VALUES = {"Rejected", "Seen", "Signed"}
SOURCE_TYPES = {"Email", "InPerson", "MailingAddress", "Phone", "Social", "Video", "Web"}
CONSENT_REQUIRED = ("AuthorizationFormTextId", "ConsentGiverId", "ConsentCapturedDateTime", "ConsentCapturedSource", "ConsentCapturedSourceType")
BAD_PATH_RE = re.compile(r"AuthorizationFormText\.AuthorizationFormDataUses", re.IGNORECASE)
SOURCE_SET_RE = re.compile(r"ConsentCapturedSource\s*=")
SOURCE_TYPE_RE = re.compile(r"ConsentCapturedSourceType")


def records_from(data: object) -> list[dict]:
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        if isinstance(data.get("records"), list):
            return records_from(data["records"])
        result = data.get("result")
        if isinstance(result, dict):
            return records_from(result)
    return []


def kind(row: dict) -> str:
    attrs = row.get("attributes")
    if isinstance(attrs, dict) and attrs.get("type"):
        return str(attrs["type"])
    if "ConsentGiverId" in row or "ConsentCapturedDateTime" in row:
        return "AuthorizationFormConsent"
    if "DataUsePurposeId" in row and "AuthorizationFormId" in row:
        return "AuthorizationFormDataUse"
    return ""


def giver_type(row: dict) -> str | None:
    if "ConsentGiver.Type" in row:
        return row["ConsentGiver.Type"]
    giver = row.get("ConsentGiver")
    if isinstance(giver, dict):
        if "Type" in giver:
            return giver["Type"]
        attrs = giver.get("attributes")
        if isinstance(attrs, dict):
            return attrs.get("type")
    return None


def check_json(path: Path, expected_giver: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [("ERROR", f"{path}: cannot read JSON ({exc}); export not checked")]
    missing_type_noted = False
    missing_cols_noted: set[str] = set()
    for i, row in enumerate(records_from(data), start=1):
        rid = row.get("Id", f"row {i}")
        k = kind(row)
        if k == "AuthorizationFormConsent":
            status = row.get("Status")
            if status not in STATUS_VALUES:
                out.append(("ERROR", f"{path}: {rid}: Status '{status}' is not Rejected, Seen, or Signed"))
            for field in CONSENT_REQUIRED:
                if field not in row:
                    if field not in missing_cols_noted:
                        out.append(("WARN", f"{path}: export has no {field} column; add it to the SOQL so the required-field check can run"))
                        missing_cols_noted.add(field)
                elif row.get(field) in (None, ""):
                    out.append(("ERROR", f"{path}: {rid}: required field {field} is empty"))
            st = row.get("ConsentCapturedSourceType")
            if st not in (None, "") and st not in SOURCE_TYPES:
                out.append(("ERROR", f"{path}: {rid}: ConsentCapturedSourceType '{st}' is not a picklist value"))
            gt = giver_type(row)
            if gt is None:
                if not missing_type_noted:
                    out.append(("WARN", f"{path}: export has no ConsentGiver.Type; add it to the SOQL to check the giver type"))
                    missing_type_noted = True
            elif gt != expected_giver:
                out.append(("WARN", f"{path}: {rid}: consent giver is {gt}, expected {expected_giver}; checks written for {expected_giver} Ids won't find it"))
        elif k == "AuthorizationFormDataUse":
            for field in ("AuthorizationFormId", "DataUsePurposeId"):
                if row.get(field) in (None, ""):
                    out.append(("ERROR", f"{path}: {rid}: AuthorizationFormDataUse missing {field}"))
    return out


def check_apex(path: Path) -> list[tuple[str, str]]:
    src = path.read_text(encoding="utf-8", errors="replace")
    out: list[tuple[str, str]] = []
    m = BAD_PATH_RE.search(src)
    if m is not None:
        line = src.count("\n", 0, m.start()) + 1
        out.append(("ERROR", f"{path}:{line}: filters through AuthorizationFormText.AuthorizationFormDataUses; data uses link to the form (AuthorizationFormId), so query them first"))
    s = SOURCE_SET_RE.search(src)
    if s is not None and SOURCE_TYPE_RE.search(src) is None:
        line = src.count("\n", 0, s.start()) + 1
        out.append(("WARN", f"{path}:{line}: sets ConsentCapturedSource but never ConsentCapturedSourceType (both are required)"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Check consent exports and Apex (consent-data-model-health skill).")
    ap.add_argument("--manifest-dir", default=".", help="Folder with JSON exports and/or Apex source")
    ap.add_argument("--giver-type", default="Individual", help="Expected ConsentGiver type (default Individual)")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    jsons = sorted(root.rglob("*.json"))
    apex = sorted(list(root.rglob("*.cls")) + list(root.rglob("*.trigger")))
    if not jsons and not apex:
        print(f"WARN: no JSON exports or Apex under {root}; nothing to check")
        return 0

    findings: list[tuple[str, str]] = []
    for f in jsons:
        findings.extend(check_json(f, args.giver_type))
    for f in apex:
        findings.extend(check_apex(f))
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = len(findings) - errors
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    print(f"Scanned {len(jsons)} JSON file(s), {len(apex)} Apex file(s): {errors} ERROR, {warns} WARN")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
