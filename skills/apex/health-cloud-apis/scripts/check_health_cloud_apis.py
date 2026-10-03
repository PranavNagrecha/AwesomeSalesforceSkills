#!/usr/bin/env python3
"""Check a project for Health Cloud API integration mistakes.

Stdlib only. Point --manifest-dir at a source-format project folder (for example
force-app/main/default), an integration repository, or both. Rules are grounded on
the Salesforce Healthcare API guide (developer.salesforce.com/docs/industries/health/
guide: Get Started, Authorization, Call the API, Considerations), fetched 2026-10-03.

Correction (2026-10-03): the previous version of this checker required an OAuth scope
named `healthcare` on any connected app that mentioned FHIR, and treated
/services/data/vXX.0/healthcare/fhir as the Healthcare API path. Neither exists in the
Healthcare API guide. The Healthcare API runs on api.healthcloud.salesforce.com (and
eu., ca., au. variants) with resource-level OAuth custom scopes such as
system_condition_read plus the refresh_token scope.

Rules
  HC-URL-01     ERROR  A /services/data/...fhir path is used for FHIR calls; the Healthcare
                       API host is api.healthcloud.salesforce.com/<module>/fhir-r4/v1/<Resource>.
  HC-SCOPE-01   ERROR  An OAuth scope named `healthcare` is configured or requested.
  HC-SCOPE-02   WARN   A SMART on FHIR wildcard scope (patient/*.read, system/*.write) is used;
                       Salesforce does not allow wildcards in OAuth scopes.
  HC-BUNDLE-01  ERROR  A Bundle uses type `transaction`; only `batch` is supported.
  HC-BUNDLE-02  ERROR  A Bundle JSON file has more than 30 entries or more than 10 GET entries.
  HC-BUNDLE-03  WARN   Code sets a bundle size constant above 30.
  HC-424-01     WARN   Code calls the Healthcare API and checks HTTP status but never handles 424.
  HC-CONC-01    WARN   Code that calls the Healthcare API sets concurrency above 5.

Usage
  python3 check_health_cloud_apis.py --manifest-dir force-app/main/default [--strict]
  python3 check_health_cloud_apis.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CODE_SUFFIXES = {".cls", ".trigger", ".js", ".ts", ".py", ".java", ".cs", ".go", ".rb"}
CONFIG_SUFFIXES = {".xml", ".json", ".yaml", ".yml", ".properties", ".env"}

OLD_PATH_RE = re.compile(r"/services/data/v?\d*[.\d]*/?[^'\"\s]*fhir", re.IGNORECASE)
HC_HOST_RE = re.compile(r"(api\.healthcloud\.salesforce\.com|fhir-r4/v1|callout:[A-Za-z0-9_]+/[a-z_-]+/fhir-r4)", re.IGNORECASE)
HEALTHCARE_SCOPE_RE = re.compile(
    r"<(oauthScope|scopes)>\s*healthcare\s*</\1>|commaSeparated\w*Scopes>[^<]*\bhealthcare\b|scope[s]?\s*[=:]\s*['\"][^'\"]*\bhealthcare\b",
    re.IGNORECASE,
)
SMART_SCOPE_RE = re.compile(r"\b(patient|user|system)/\*\.(read|write|\*)", re.IGNORECASE)
TRANSACTION_RE = re.compile(r"[\"']type[\"']\s*:\s*[\"']transaction[\"']", re.IGNORECASE)
BUNDLE_CONST_RE = re.compile(r"\b(bundle[_a-z]*(size|max|entries|chunk)[_a-z]*)\s*[:=]\s*(\d+)", re.IGNORECASE)
STATUS_CHECK_RE = re.compile(r"getStatusCode\(\)|\.status\b|statusCode|status_code", re.IGNORECASE)
CONC_RE = re.compile(r"\b(max_workers|concurrency|maxConcurrent\w*|parallelism|pool_size)\s*[:=]\s*(\d+)|Semaphore\((\d+)\)", re.IGNORECASE)


def strip_line_comments(text: str) -> str:
    return re.sub(r"(?m)^\s*(//|#).*$", "", text)


def check_bundle_json(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    try:
        data = json.loads(text)
    except ValueError:
        return findings
    if not isinstance(data, dict) or data.get("resourceType") != "Bundle":
        return findings
    if str(data.get("type", "")).lower() == "transaction":
        findings.append(f"ERROR HC-BUNDLE-01 {path}: Bundle type is transaction; the Healthcare API supports only batch")
    entries = data.get("entry") or []
    gets = sum(1 for e in entries if isinstance(e, dict) and str((e.get("request") or {}).get("method", "")).upper() == "GET")
    if len(entries) > 30 or gets > 10:
        findings.append(
            f"ERROR HC-BUNDLE-02 {path}: Bundle has {len(entries)} entries and {gets} GET entries; "
            f"the limit is 30 entries with at most 10 read or search requests"
        )
    return findings


def scan_file(path: Path) -> list[str]:
    findings: list[str] = []
    suffix = path.suffix.lower()
    if suffix not in CODE_SUFFIXES | CONFIG_SUFFIXES:
        return findings
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    text = strip_line_comments(raw) if suffix in CODE_SUFFIXES else raw

    if OLD_PATH_RE.search(text):
        findings.append(
            f"ERROR HC-URL-01 {path}: FHIR call under /services/data; the Healthcare API host is "
            f"api.healthcloud.salesforce.com/<module>/fhir-r4/v1/<Resource> (regional eu., ca., au.; /sandBox/ for sandboxes)"
        )
    if HEALTHCARE_SCOPE_RE.search(text):
        findings.append(
            f"ERROR HC-SCOPE-01 {path}: OAuth scope `healthcare` is not a Healthcare API scope; use resource custom "
            f"scopes such as system_condition_read and assign refresh_token to the external client app"
        )
    if SMART_SCOPE_RE.search(text):
        findings.append(
            f"WARN HC-SCOPE-02 {path}: SMART on FHIR wildcard scope found; Salesforce does not allow wildcards in "
            f"OAuth scopes, so map each to a specific custom scope"
        )
    if suffix == ".json":
        findings.extend(check_bundle_json(path, raw))
    elif TRANSACTION_RE.search(text) and "bundle" in text.lower():
        findings.append(f"ERROR HC-BUNDLE-01 {path}: Bundle type transaction; the Healthcare API supports only batch")

    if suffix in CODE_SUFFIXES:
        for match in BUNDLE_CONST_RE.finditer(text):
            if int(match.group(3)) > 30:
                findings.append(
                    f"WARN HC-BUNDLE-03 {path}: {match.group(1)} = {match.group(3)}; bundles cap at 30 entries"
                )
                break
        calls_hapi = bool(HC_HOST_RE.search(text))
        if calls_hapi and STATUS_CHECK_RE.search(text) and "424" not in text:
            findings.append(
                f"WARN HC-424-01 {path}: Healthcare API status handling without 424; dependent bundle entries "
                f"return 424 when an entry they reference fails"
            )
        if calls_hapi:
            for match in CONC_RE.finditer(text):
                value = int(match.group(2) or match.group(3))
                if value > 5:
                    findings.append(
                        f"WARN HC-CONC-01 {path}: concurrency {value}; Salesforce recommends at most five "
                        f"concurrent Healthcare API requests per org"
                    )
                    break
    return findings


def scan(root: Path) -> tuple[int, list[str]]:
    if not root.exists():
        return 0, [f"ERROR HC-DIR-01 {root}: folder not found"]
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    findings: list[str] = []
    for path in files:
        findings.extend(scan_file(path))
    return len(files), findings


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    _, good = scan(here / "good")
    _, bad = scan(here / "bad")
    expected = {"HC-URL-01", "HC-SCOPE-01", "HC-SCOPE-02", "HC-BUNDLE-01", "HC-BUNDLE-02",
                "HC-BUNDLE-03", "HC-424-01", "HC-CONC-01"}
    seen = {f.split()[1] for f in bad}
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print(f"  unexpected: {f}")
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    return 0 if not good and expected <= seen else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check a project for Health Cloud API integration mistakes.")
    ap.add_argument("--manifest-dir", default=".", help="Project folder to scan (default: current directory).")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    ap.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    count, findings = scan(Path(args.manifest_dir))
    for f in findings:
        print(f)
    errors = [f for f in findings if f.startswith("ERROR")]
    warns = [f for f in findings if f.startswith("WARN")]
    print(f"Scanned {count} file(s): {len(errors)} error(s), {len(warns)} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
