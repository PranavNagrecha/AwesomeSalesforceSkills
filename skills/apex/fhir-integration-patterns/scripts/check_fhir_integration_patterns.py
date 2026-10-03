#!/usr/bin/env python3
"""Check Health Cloud FHIR integration code and configuration for documented pitfalls.

Stdlib only. Scans --manifest-dir recursively. Each rule cites the source it encodes:
  HC guide  = Agentforce Health (Health Cloud) Developer Guide, release 262
  HAPI      = Salesforce Healthcare API guide (developer.salesforce.com/docs/industries/health/guide)

Rules
  FHIR-HC24-01   WARN   Apex, Flow, or integration config that references a packaged EHR object
                        (HC24__Ehr...__c). HC guide: "Starting with the Spring '23 release, new customers
                        won't be able to create records in the packaged EHR objects that have
                        counterpart standard objects."
  FHIR-CSB-01    ERROR  CodeSet16Id (or higher) on CodeSetBundle. HC guide: CodeableConcept flattens to
                        "15 zero-to-one Code Set references ... CodeSet1Id ... until CodeSet15Id."
  FHIR-SCOPE-01  WARN   SMART-style wildcard scopes (patient/*.read, user/*.*, system/*.read) in client
                        configuration. HAPI Considerations: SMART scope format is not supported because
                        Salesforce doesn't allow wildcard characters in OAuth scopes.
  FHIR-URL-01    WARN   A Healthcare API call built as /services/data/.../healthcare/fhir/... . HAPI
                        "Call the API": URLs are https://api.healthcloud.salesforce.com/<module>/fhir-r4/v1/<Resource>.
  FHIR-PERM-01   WARN   Experience Cloud permission sets present but none that looks like the
                        "FHIR R4 for Experience Cloud Sites" permission set (HC guide, Clinical Data Model
                        note). The permission set API name is UNVERIFIED; this rule matches on name text.

Usage
  python3 check_fhir_integration_patterns.py --manifest-dir force-app/main/default
  python3 check_fhir_integration_patterns.py --self-test

Exit codes: 0 when no issues; 1 when any issue is found or the folder is missing.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = (".cls", ".trigger", ".apex", ".xml", ".json", ".yaml", ".yml", ".properties", ".dwl", ".js", ".ts", ".py", ".md")
HC24_RE = re.compile(r"\bHC24__Ehr\w*__c\b", re.IGNORECASE)
CODESET_OVER_RE = re.compile(r"\bCodeSet(1[6-9]|[2-9]\d)Id\b")
SMART_SCOPE_RE = re.compile(r"(?<![\w/])(patient|user|system)/(\*|[A-Z][A-Za-z]+)\.(\*|read|write|rs|cruds)\b")
OLD_URL_RE = re.compile(r"/services/data/v\d+\.\d+/healthcare/fhir", re.IGNORECASE)


def iter_text_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and p.name.endswith(TEXT_SUFFIXES))


def check_file(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    name = path.name
    is_code_or_config = not name.endswith(".md")
    if is_code_or_config:
        found = sorted(set(m.group(0) for m in HC24_RE.finditer(text)))
        if found:
            issues.append(f"{path}: references packaged EHR object(s) {', '.join(found[:3])}; new customers can't create "
                          "records in packaged EHR objects that have FHIR R4-aligned standard counterparts")
        over = sorted(set(m.group(0) for m in CODESET_OVER_RE.finditer(text)))
        if over:
            issues.append(f"ERROR {path}: {over[0]} does not exist; CodeSetBundle holds CodeSet1Id to CodeSet15Id")
        if SMART_SCOPE_RE.search(text):
            issues.append(f"{path}: SMART-style wildcard scope found; the Salesforce Healthcare API uses custom scopes such as "
                          "user_condition_read and doesn't support wildcard scopes")
        if OLD_URL_RE.search(text):
            issues.append(f"{path}: Healthcare API call uses /services/data/.../healthcare/fhir; the documented shape is "
                          "https://api.healthcloud.salesforce.com/<module>/fhir-r4/v1/<Resource>")
    return issues


def check_experience_cloud_perms(root: Path) -> list[str]:
    perm_files = [p for p in root.rglob("*.permissionset-meta.xml") if p.is_file()]
    exp = [p for p in perm_files if re.search(r"experience|community|portal", p.name, re.IGNORECASE)]
    if not exp:
        return []
    has_fhir = any(re.search(r"fhir.*experience|experience.*fhir", p.name + p.read_text(encoding="utf-8", errors="ignore")[:4000], re.IGNORECASE)
                   for p in perm_files)
    if has_fhir:
        return []
    return [f"{root}: Experience Cloud permission sets found but nothing resembling 'FHIR R4 for Experience Cloud Sites'; "
            "community users need it to use Clinical Data Model objects on a site"]


def scan(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        issues.extend(check_file(path, text))
    issues.extend(check_experience_cloud_perms(root))
    return issues


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    good, bad = base / "good", base / "bad"
    if not good.is_dir() or not bad.is_dir():
        print("ERROR: fixtures/good or fixtures/bad is missing")
        return 1
    failures = 0
    good_issues = scan(good)
    if good_issues:
        failures += 1
        print(f"ERROR: self-test: fixtures/good produced {good_issues}")
    bad_issues = scan(bad)
    for path in sorted(p for p in bad.rglob("*") if p.is_file()):
        if not any(str(path) in issue for issue in bad_issues) and not path.name.endswith(".permissionset-meta.xml"):
            failures += 1
            print(f"ERROR: self-test: bad fixture {path.name} produced no issue")
    if not any("Experience Cloud Sites" in issue for issue in bad_issues):
        failures += 1
        print("ERROR: self-test: Experience Cloud permission set rule did not fire")
    if failures:
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check FHIR integration code and configuration for documented pitfalls.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan (default: current directory).")
    parser.add_argument("--self-test", action="store_true", help="Run against scripts/fixtures/good and bad.")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    if not iter_text_files(root):
        print(f"WARN: no code or configuration files under {root}")
        return 0
    issues = scan(root)
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(issue if issue.startswith("ERROR ") else f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
