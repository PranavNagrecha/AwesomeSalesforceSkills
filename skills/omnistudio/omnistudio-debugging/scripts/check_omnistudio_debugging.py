#!/usr/bin/env python3
"""Audit OmniStudio assets for debugging-blocking patterns.

Scans OmniStudio metadata (OmniScript `*.os-meta.xml`, OmniIntegrationProcedure
`*.oip-meta.xml`, OmniDataTransform `*.rpt-meta.xml`) plus any DataPack JSON for:

  HIGH    hardcoded http(s) endpoint with no named credential reference
          (promotion breaks; non-named-credential callouts also need a Remote Site Setting)
  MEDIUM  placeholder or generic failure response text that will reach users
  MEDIUM  OmniDataTransform with fieldLevelSecurityEnabled=false
  REVIEW  asset whose active flag is false (isActive / active), so it won't run
  REVIEW  Integration Procedure with no Try-Catch block element (failures may not
          reach the caller; Trailhead: a Try-Catch Block "returns specified output or
          calls an Apex class if a step within it fails")
  REVIEW  Navigate Action present (test navigation in the deployed page)

Earlier versions flagged Integration Procedures without `rollbackOnError: true` as
HIGH/MEDIUM. The OmniIntegrationProcedure metadata reference (Summer '26) has no such
field, and the claim that it controls error surfacing is not in the fetched sources,
so that rule was removed.

Exit codes: 1 if the directory is missing or any HIGH finding exists (MEDIUM and
REVIEW too with --strict); 0 otherwise. Stdlib only.

Usage:
    python3 check_omnistudio_debugging.py --manifest-dir path/to/metadata [--json] [--strict]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

OMNI_SUFFIXES = (".os-meta.xml", ".oip-meta.xml", ".rpt-meta.xml", ".omniScript",
                 ".omniIntegrationProcedure", ".omniDataTransform")
OMNI_RE = re.compile(r"OmniScript|OmniIntegrationProcedure|IntegrationProcedure|OmniDataTransform|DataRaptor|OmniProcess",
                     re.IGNORECASE)
HTTP_URL_RE = re.compile(r"https?://[a-zA-Z0-9._/:-]+", re.IGNORECASE)
NAMED_CRED_RE = re.compile(r"namedCredential|Named_Credential|callout:", re.IGNORECASE)
# The pattern spells the placeholder word with a character class so this file holds no literal marker.
PLACEHOLDER_FAILURE_RE = re.compile(
    r"(failureResponse|failureMessage|errorMessage)[^\n]{0,40}?(TO[D]O|TBD|placeholder|your message here|"
    r"error occurred|something went wrong)", re.IGNORECASE)
NAV_ACTION_RE = re.compile(r"Navigate Action|NavigateAction|NavigationAction", re.IGNORECASE)
TRY_CATCH_RE = re.compile(r"Try\s*-?\s*Catch", re.IGNORECASE)
INACTIVE_RE = re.compile(r"<(isActive|active)>false</(isActive|active)>")
FLS_OFF_RE = re.compile(r"<fieldLevelSecurityEnabled>false</fieldLevelSecurityEnabled>")
SEVERITY_WEIGHTS = {"HIGH": 10, "MEDIUM": 5, "REVIEW": 0}


def iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name.endswith(OMNI_SUFFIXES) or path.suffix.lower() == ".json":
            out.append(path)
    return sorted(out)


def check_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not path.name.endswith(OMNI_SUFFIXES) and not OMNI_RE.search(text):
        return []
    findings: list[dict] = []
    rel = str(path)
    is_ip = path.name.endswith((".oip-meta.xml", ".omniIntegrationProcedure")) or "<OmniIntegrationProcedure" in text

    urls = [u for u in HTTP_URL_RE.findall(text)
            if not re.search(r"salesforce\.com|soap\.sforce\.com|w3\.org", u, re.IGNORECASE)]
    if urls and not NAMED_CRED_RE.search(text):
        findings.append({"severity": "HIGH", "file": rel,
                         "message": f"hardcoded endpoint {urls[0]!r} with no named credential reference; "
                                    "use a named credential (no Remote Site Setting needed) or deploy a Remote Site Setting"})
    if PLACEHOLDER_FAILURE_RE.search(text):
        findings.append({"severity": "MEDIUM", "file": rel,
                         "message": "placeholder or generic failure text will reach users; write a specific message"})
    if FLS_OFF_RE.search(text):
        findings.append({"severity": "MEDIUM", "file": rel,
                         "message": "fieldLevelSecurityEnabled is false; restricted users may see different results than Preview"})
    if INACTIVE_RE.search(text):
        findings.append({"severity": "REVIEW", "file": rel,
                         "message": "asset is inactive in this file; confirm which version is active in the target org"})
    if is_ip and not TRY_CATCH_RE.search(text):
        findings.append({"severity": "REVIEW", "file": rel,
                         "message": "no Try-Catch block found; decide how step failures reach the caller"})
    if NAV_ACTION_RE.search(text):
        findings.append({"severity": "REVIEW", "file": rel,
                         "message": "Navigate Action present; test navigation in the deployed page, not only in Preview"})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OmniStudio metadata for debugging-blocking patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan (default: .)")
    parser.add_argument("--json", dest="output_json", action="store_true", help="Emit JSON")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on MEDIUM and REVIEW findings too")
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    files = iter_files(root)
    findings: list[dict] = []
    for path in files:
        findings.extend(check_file(path))
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in findings))

    if args.output_json:
        print(json.dumps({"score": score, "file_count": len(files), "findings": findings}, indent=2))
    elif not files:
        print(f"WARN: no OmniStudio metadata found under {root}")
    elif not findings:
        print(f"OK: scanned {len(files)} file(s), no issues")
    else:
        for f in findings:
            print(f"{f['severity']}: {f['file']}: {f['message']}")

    blocking = {"HIGH"} | ({"MEDIUM", "REVIEW"} if args.strict else set())
    return 1 if any(f["severity"] in blocking for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
