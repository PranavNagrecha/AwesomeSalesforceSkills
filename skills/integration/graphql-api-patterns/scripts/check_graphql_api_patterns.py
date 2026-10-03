#!/usr/bin/env python3
"""Audit Salesforce GraphQL API usage in LWC bundles and server code.

Stdlib only. Rules are grounded on the GraphQL API Developer Guide (Pagination,
Upper-Bound Pagination, Requests and Responses, Get Started, Wire Adapter Limitations)
and the LWC Developer Guide (lightning/graphql v2 and lightning/uiGraphQLApi v1),
fetched 2026-10-03.

Correction (2026-10-03): the previous version reported every `${` inside a gql
template as HIGH. The LWC guide says lightning/graphql (v2) supports dynamic query
construction, including ${} interpolation for composing fragments; only
lightning/uiGraphQLApi (v1) rejects it. Interpolating component state is still wrong
in both modules because gql is not reactive, so that case is reported separately.

Rules
  GQL-INTERP-01  ERROR  `${` inside gql in a file that imports lightning/uiGraphQLApi (unsupported in v1).
  GQL-INTERP-02  WARN   gql template interpolates component state (`${this.`); gql isn't reactive, use variables.
  GQL-V1-01      WARN   lightning/uiGraphQLApi import; v2 (lightning/graphql) is recommended unless Mobile Offline.
  GQL-ERR-01     WARN   graphql wire handler reads `error` (singular); the adapter returns `errors`.
  GQL-PAGE-01    ERROR  `first` above 2000 (a subquery returns at most 2000 records), or `upperBound` with `first` below 200.
  GQL-HOST-01    WARN   GraphQL or OAuth call to a lightning.force.com host; use MyDomainName.my.salesforce.com.
  GQL-RAW-01     WARN   Raw fetch to the GraphQL endpoint from an LWC bundle; prefer the wire adapter.
  GQL-VARS-01    WARN   Query string built with concatenation; pass runtime values as variables.

Usage
  python3 check_graphql_api_patterns.py --manifest-dir force-app/main/default [--strict]
  python3 check_graphql_api_patterns.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SUFFIXES = {".js", ".ts", ".mjs", ".cls", ".py", ".gql", ".graphql", ".json"}
GQL_TEMPLATE_RE = re.compile(r"gql\s*`([^`]*)`", re.S)
FIRST_RE = re.compile(r"\bfirst\s*:\s*(\d+)")
UPPER_RE = re.compile(r"\bupperBound\s*:")
CONCAT_QUERY_RE = re.compile(r"query\s*[:=]\s*['\"][^'\"\n]*['\"]\s*\+\s*\w", re.I)


def audit(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "graphql" not in text.lower() and "uiapi" not in text:
        return findings
    is_v1 = "lightning/uiGraphQLApi" in text
    templates = GQL_TEMPLATE_RE.findall(text)
    if is_v1 and any("${" in t for t in templates):
        findings.append(f"ERROR GQL-INTERP-01 {path}: ${{}} interpolation inside gql with lightning/uiGraphQLApi; v1 does not support it")
    elif any("${this." in t for t in templates):
        findings.append(f"WARN GQL-INTERP-02 {path}: gql interpolates component state; gql isn't reactive, pass the value in variables")
    if is_v1:
        findings.append(f"WARN GQL-V1-01 {path}: lightning/uiGraphQLApi import; use lightning/graphql (v2) unless the component must work in Mobile Offline")
    if "@wire(graphql" in text and re.search(r"\{\s*data\s*,\s*error\s*\}", text) and "errors" not in text:
        findings.append(f"WARN GQL-ERR-01 {path}: graphql wire handler reads `error`; the adapter returns `errors`")
    for m in FIRST_RE.finditer(text):
        value = int(m.group(1))
        window = text[max(0, m.start() - 200): m.end() + 200]
        if value > 2000:
            findings.append(f"ERROR GQL-PAGE-01 {path}: first: {value}; each subquery returns at most 2000 records (GraphQL guide, Query Limitations)")
            break
        if UPPER_RE.search(window) and value < 200:
            findings.append(f"ERROR GQL-PAGE-01 {path}: upperBound pagination with first: {value}; first must be 200 to 2000")
            break
    if re.search(r"lightning\.force\.com[^'\"\s]*/(services/data/v[\d.]+/graphql|services/oauth2)", text):
        findings.append(f"WARN GQL-HOST-01 {path}: lightning.force.com host for GraphQL or OAuth; use MyDomainName.my.salesforce.com")
    if "/lwc/" in str(path).replace("\\", "/") and re.search(r"fetch\s*\([^)]*/graphql", text):
        findings.append(f"WARN GQL-RAW-01 {path}: raw fetch to the GraphQL endpoint from LWC; prefer the wire adapter")
    if CONCAT_QUERY_RE.search(text):
        findings.append(f"WARN GQL-VARS-01 {path}: GraphQL query built by concatenation; pass runtime values in variables")
    return findings


def scan(root: Path) -> tuple[int, list[str]]:
    if not root.exists():
        return 0, [f"ERROR GQL-DIR-01 {root}: folder not found"]
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix.lower() in SUFFIXES and "node_modules" not in p.parts]
    findings: list[str] = []
    for p in files:
        findings.extend(audit(p))
    return len(files), findings


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    _, good = scan(here / "good")
    _, bad = scan(here / "bad")
    expected = {"GQL-INTERP-01", "GQL-V1-01", "GQL-ERR-01", "GQL-PAGE-01", "GQL-HOST-01"}
    seen = {f.split()[1] for f in bad}
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print(f"  unexpected: {f}")
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    return 0 if not good and expected <= seen else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Salesforce GraphQL API usage in LWC bundles and server code.")
    ap.add_argument("--manifest-dir", default=".", help="Root directory to scan (default: current directory).")
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
