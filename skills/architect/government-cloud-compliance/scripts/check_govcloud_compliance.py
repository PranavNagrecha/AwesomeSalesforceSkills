#!/usr/bin/env python3
"""
check_govcloud_compliance.py

Validates a Government Cloud Compliance Assessment document produced from
the government-cloud-compliance skill template.

Checks:
  1. Authorization level is explicitly stated (FedRAMP Moderate, FedRAMP High, IL2, IL4, or IL5)
  2. Offering selection section is present (GovCloud vs GovCloud Plus vs Hyperforce)
  3. Data residency section is present
  4. Control inheritance or NIST 800-53 mapping is present
  5. Integration FedRAMP authorization status is addressed
  6. Continuous monitoring / FISMA section is present
  7. Feature availability gap analysis is present

Usage:
  python3 check_govcloud_compliance.py <path-to-assessment-file.md>
  python3 check_govcloud_compliance.py   # scans cwd for *govcloud* or *government*cloud*.md files

Exit codes:
  0 — all checks passed
  1 — one or more checks failed
"""

import sys
import os
import re
import glob


def find_assessment_files(directory):
    """Find markdown files matching government cloud assessment naming patterns."""
    patterns = [
        os.path.join(directory, "**", "*govcloud*.md"),
        os.path.join(directory, "**", "*government*cloud*.md"),
        os.path.join(directory, "**", "*fedramp*.md"),
        os.path.join(directory, "**", "*gov*compliance*.md"),
    ]
    found = set()
    for pattern in patterns:
        found.update(glob.glob(pattern, recursive=True))
    return sorted(found)


def load_file(path):
    """Read file content; return None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        print(f"ERROR: Cannot read file '{path}': {e}")
        return None


def check_authorization_level(content):
    """Check that an authorization level is explicitly stated."""
    patterns = [
        r"\bFedRAMP\s+(High|Moderate|Low)\b",
        r"\bFedRAMP-(High|Moderate|Low)\b",
        r"\bIL[2-5]\b",
        r"\bImpact Level [2-5]\b",
        r"\bFISMA (High|Moderate|Low)\b",
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_offering_selection(content):
    """Check that a GovCloud offering selection is documented."""
    patterns = [
        r"\bGovCloud Plus\b",
        r"\bGovernment Cloud Plus\b",
        r"\bHyperforce\b.*[Gg]ov",
        r"\b[Gg]ov[Cc]loud\b",
        r"offering selection",
        r"GovCloud.*vs.*GovCloud Plus",
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_data_residency(content):
    """Check that data residency is addressed."""
    patterns = [
        r"data residen",
        r"US.only (data|processing|storage)",
        r"United States.*(process|store|reside)",
        r"data sover",
        r"geographic restriction",
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_control_mapping(content):
    """Check that NIST 800-53 controls or inheritance is addressed."""
    patterns = [
        r"NIST 800-53",
        r"NIST SP 800-53",
        r"control (family|baseline|inheritance|mapping)",
        r"\b(AC|AU|IA|SC|SI|CM|CP)-\d+",
        r"inherited control",
        r"customer.owned control",
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_integration_fedramp(content):
    """Check that integration FedRAMP authorization is addressed."""
    patterns = [
        r"(integration|middleware|external system).*(FedRAMP|authorized)",
        r"FedRAMP.*(integration|middleware|authorized)",
        r"authorization boundary",
        r"non.FedRAMP",
        r"authorized integration",
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_continuous_monitoring(content):
    """Check that continuous monitoring or FISMA ongoing authorization is addressed."""
    patterns = [
        r"continuous monitor",
        r"FISMA",
        r"POA.?M",
        r"Plan of Action",
        r"ongoing (ATO|authorization|monitoring)",
        r"monthly (reporting|scan|review)",
        r"significant change",
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_feature_availability(content):
    """Check that feature availability gap analysis is addressed."""
    patterns = [
        r"feature (availability|gap|lag)",
        r"(not|un).?available in GovCloud",
        r"GovCloud.*feature",
        r"feature.*GovCloud",
        r"AppExchange.*authorized",
        r"authorized product",
        r"Government Cloud.*feature",
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def validate_file(filepath):
    """Run all checks on a single file. Returns (all_passed: bool)."""
    print(f"\nChecking: {filepath}")
    print("-" * 70)

    content = load_file(filepath)
    if content is None:
        return False

    checks = [
        ("Authorization level explicitly stated (FedRAMP High/Moderate, IL2-IL5)", check_authorization_level(content)),
        ("Salesforce GovCloud offering selection documented", check_offering_selection(content)),
        ("Data residency / US-only processing addressed", check_data_residency(content)),
        ("NIST 800-53 control mapping or inheritance documented", check_control_mapping(content)),
        ("Integration FedRAMP authorization boundary addressed", check_integration_fedramp(content)),
        ("Continuous monitoring / FISMA ongoing authorization addressed", check_continuous_monitoring(content)),
        ("Feature availability gap analysis present", check_feature_availability(content)),
    ]

    all_passed = True
    for description, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {description}")

    result_label = "All checks passed" if all_passed else "One or more checks FAILED"
    print(f"\n  RESULT: {result_label} for {os.path.basename(filepath)}")
    return all_passed


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        sys.exit(0)

    files_to_check = []

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if os.path.isfile(arg):
                files_to_check.append(arg)
            else:
                print(f"ERROR: File not found: {arg}")
                sys.exit(1)
    else:
        files_to_check = find_assessment_files(os.getcwd())
        if not files_to_check:
            print("No government cloud compliance markdown files found in current directory.")
            print("Usage: python3 check_govcloud_compliance.py <path-to-assessment.md>")
            sys.exit(0)

    print("Salesforce Government Cloud Compliance Assessment Validator")
    print("=" * 70)

    total_passed = 0
    total_failed = 0

    for filepath in files_to_check:
        passed = validate_file(filepath)
        if passed:
            total_passed += 1
        else:
            total_failed += 1

    print("\n" + "=" * 70)
    print(f"Files checked: {total_passed + total_failed}")
    print(f"Passed: {total_passed}  |  Failed: {total_failed}")

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
