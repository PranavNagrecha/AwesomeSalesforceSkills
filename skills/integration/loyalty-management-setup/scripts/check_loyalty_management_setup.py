#!/usr/bin/env python3
"""Check a project for Loyalty Management configuration and integration mistakes.

Stdlib only. Rules are grounded on the Loyalty Management Developer Guide object and
resource pages (LoyaltyMemberCurrency, LoyaltyProgramCurrency, Transaction Journals
Execution, Eligible Promotions List), fetched 2026-10-03, and the Metadata API Developer
Guide v67.0 (LoyaltyProgramSetup).

Correction (2026-10-03): the previous stub flagged any LoyaltyMemberCurrency query that
did not filter on CurrencyType. CurrencyType is a field of LoyaltyProgramCurrency, not of
LoyaltyMemberCurrency, so the filter has to go through the LoyaltyProgramCurrency
relationship. The rule is now the reverse of the old one.

Rules
  LM-CUR-01    ERROR  A LoyaltyMemberCurrency query filters on CurrencyType directly; use
                      LoyaltyProgramCurrency.CurrencyType.
  LM-CUR-02    ERROR  A CurrencyType filter uses a value other than Qualifying or NonQualifying.
  LM-SETUP-01  WARN   A LoyaltyProgramSetup file's <label> differs from its file name (after decoding
                      %20); a label that matches no program creates a new LoyaltyProgram record on
                      deploy. Heuristic: the retrieve names the file after the program, so a mismatch
                      usually means the label was edited by hand.
  LM-SETUP-02  WARN   A LoyaltyProgramSetup file with no Active process; only active processes
                      process transaction journals (informational for deploys meant to go live).
  LM-TJ-01     WARN   Code posts to the Transaction Journals Execution resource with appliedPromotions
                      but never calls Eligible Promotions List; promotion limits are not enforced.

Usage
  python3 check_loyalty_management_setup.py --manifest-dir force-app/main/default [--strict]
  python3 check_loyalty_management_setup.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CODE_SUFFIXES = {".cls", ".trigger", ".soql", ".js", ".ts", ".py", ".java"}
LMC_QUERY_RE = re.compile(r"FROM\s+LoyaltyMemberCurrency\b(.*?)(\]|'|\"|;|$)", re.I | re.S)
BARE_CURRENCYTYPE_RE = re.compile(r"(?<![.\w])CurrencyType\b", re.I)
CURRENCYTYPE_VALUE_RE = re.compile(r"CurrencyType\s*(=|!=|IN)\s*\(?\s*'([^']*)'", re.I)
VALID_TYPES = {"qualifying", "nonqualifying"}


def audit_code(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    for m in LMC_QUERY_RE.finditer(text):
        clause = m.group(1)
        if BARE_CURRENCYTYPE_RE.search(clause):
            findings.append(f"ERROR LM-CUR-01 {path}: LoyaltyMemberCurrency has no CurrencyType field; filter on "
                            f"LoyaltyProgramCurrency.CurrencyType")
            break
    for m in CURRENCYTYPE_VALUE_RE.finditer(text):
        if m.group(2).lower() not in VALID_TYPES:
            findings.append(f"ERROR LM-CUR-02 {path}: CurrencyType value '{m.group(2)}'; the picklist values are "
                            f"Qualifying and NonQualifying")
            break
    if "/connect/realtime/loyalty/programs/" in text and "appliedPromotions" in text and "eligible-promotions" not in text:
        findings.append(f"WARN LM-TJ-01 {path}: appliedPromotions sent to Transaction Journals Execution without an "
                        f"Eligible Promotions List call; PromotionLimit is not enforced by that resource")
    return findings


def audit_setup(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    label = re.search(r"<label>\s*([^<]+?)\s*</label>", text)
    stem = path.name.split(".")[0].replace("%20", " ")
    if label and label.group(1) != stem:
        findings.append(f"WARN LM-SETUP-01 {path}: <label>{label.group(1)}</label> differs from the file name '{stem}'; "
                        f"a label that matches no program creates a new LoyaltyProgram on deploy")
    process_status = re.findall(r"</rules>\s*<status>\s*(\w+)\s*</status>", text)
    if process_status and "Active" not in process_status:
        findings.append(f"WARN LM-SETUP-02 {path}: no Active program process; only active processes process transaction journals")
    return findings


def scan(root: Path) -> tuple[int, list[str]]:
    if not root.exists():
        return 0, [f"ERROR LM-DIR-01 {root}: folder not found"]
    findings: list[str] = []
    count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.name.endswith(".loyaltyProgramSetup-meta.xml") or path.name.endswith(".loyaltyProgramSetup"):
            count += 1
            findings.extend(audit_setup(path, text))
        elif path.suffix.lower() in CODE_SUFFIXES:
            count += 1
            findings.extend(audit_code(path, text))
    return count, findings


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    _, good = scan(here / "good")
    _, bad = scan(here / "bad")
    expected = {"LM-CUR-01", "LM-CUR-02", "LM-SETUP-01", "LM-TJ-01"}
    seen = {f.split()[1] for f in bad}
    good_errors = [f for f in good if not f.split()[1] == "LM-SETUP-02"]
    print(f"good fixtures: {len(good_errors)} finding(s) besides LM-SETUP-02 (expected 0)")
    for f in good_errors:
        print(f"  unexpected: {f}")
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    return 0 if not good_errors and expected <= seen else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check a project for Loyalty Management configuration and integration mistakes.")
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
