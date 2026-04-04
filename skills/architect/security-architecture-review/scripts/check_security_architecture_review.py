#!/usr/bin/env python3
"""
check_security_architecture_review.py

Validates a Salesforce Security Architecture Review document produced from
the security-architecture-review skill template.

Checks:
  1. All five review domains are present as sections
  2. A summary scorecard table with Red/Amber/Green scores is present
  3. A severity-rated findings table is present (Critical/High/Medium/Low)
  4. The Shield Needs Assessment section is present
  5. A prioritized remediation backlog section is present

Usage:
  python3 check_security_architecture_review.py <path-to-review-file.md>
  python3 check_security_architecture_review.py   # scans cwd for *security*review*.md files

Exit codes:
  0 — all checks passed
  1 — one or more checks failed
"""

import sys
import os
import re
import glob


def find_review_files(directory):
    """Find markdown files with 'security' and 'review' in the name."""
    pattern_1 = os.path.join(directory, "**", "*security*review*.md")
    pattern_2 = os.path.join(directory, "**", "*review*security*.md")
    found = set(glob.glob(pattern_1, recursive=True)) | set(glob.glob(pattern_2, recursive=True))
    return sorted(found)


def load_file(path):
    """Read file content; return None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        print(f"ERROR: Cannot read file '{path}': {e}")
        return None


def check_domain_sections(content):
    """Check that all five review domains are present."""
    domains = [
        ("Sharing Model", r"##[#]?\s+.*[Ss]haring\s+[Mm]odel"),
        ("FLS / CRUD", r"##[#]?\s+.*\b(FLS|CRUD|[Ff]ield.?[Ll]evel)\b"),
        ("Apex Security", r"##[#]?\s+.*[Aa]pex\s+[Ss]ecurity"),
        ("API / Connected Apps", r"##[#]?\s+.*(API|[Cc]onnected\s+[Aa]pp)"),
        ("Shield", r"##[#]?\s+.*[Ss]hield"),
    ]
    results = []
    for domain_name, pattern in domains:
        found = bool(re.search(pattern, content))
        results.append((domain_name, found))
    return results


def check_scorecard(content):
    """Check that a summary scorecard table with Red/Amber/Green values exists."""
    score_pattern = re.compile(r"\b(Red|Amber|Green)\b", re.IGNORECASE)
    matches = list(score_pattern.finditer(content))
    if len(matches) < 3:
        return False
    # Require a table structure and a "scorecard" or "score" label nearby
    has_table = bool(re.search(r"\|.*\|.*\|", content))
    has_label = bool(
        re.search(r"\b(scorecard|score card|summary score|score\s*key)\b", content, re.IGNORECASE)
    )
    return has_table and has_label


def check_severity_ratings(content):
    """Check that severity ratings (Critical/High/Medium/Low) appear in a findings context."""
    severities = ["Critical", "High", "Medium", "Low"]
    found_count = 0
    for severity in severities:
        if re.search(r"\b" + severity + r"\b", content):
            found_count += 1
    # All four severity labels must be present
    return found_count == 4


def check_shield_section(content):
    """Check that a Shield Needs Assessment section exists."""
    return bool(re.search(r"##[#]?\s+.*[Ss]hield", content))


def check_remediation_backlog(content):
    """Check that a remediation backlog section exists."""
    return bool(
        re.search(
            r"##[#]?\s+.*(remediation|backlog|remediation\s+backlog|prioritized)",
            content,
            re.IGNORECASE,
        )
    )


def validate_file(filepath):
    """Run all checks on a single file. Returns (passed_count, failed_count)."""
    print(f"\nChecking: {filepath}")
    print("-" * 60)

    content = load_file(filepath)
    if content is None:
        return 0, 1

    all_passed = True

    # Check 1: Domain sections
    domain_results = check_domain_sections(content)
    for domain_name, found in domain_results:
        status = "PASS" if found else "FAIL"
        if not found:
            all_passed = False
        print(f"  [{status}] Domain section present: {domain_name}")

    # Check 2: Summary scorecard
    has_scorecard = check_scorecard(content)
    status = "PASS" if has_scorecard else "FAIL"
    if not has_scorecard:
        all_passed = False
    print(f"  [{status}] Summary scorecard with Red/Amber/Green present")

    # Check 3: Severity ratings
    has_severity = check_severity_ratings(content)
    status = "PASS" if has_severity else "FAIL"
    if not has_severity:
        all_passed = False
    print(f"  [{status}] All four severity ratings (Critical/High/Medium/Low) present")

    # Check 4: Shield section
    has_shield = check_shield_section(content)
    status = "PASS" if has_shield else "FAIL"
    if not has_shield:
        all_passed = False
    print(f"  [{status}] Shield Needs Assessment section present")

    # Check 5: Remediation backlog
    has_backlog = check_remediation_backlog(content)
    status = "PASS" if has_backlog else "FAIL"
    if not has_backlog:
        all_passed = False
    print(f"  [{status}] Prioritized remediation backlog section present")

    result_label = "All checks passed" if all_passed else "One or more checks FAILED"
    print(f"\n  RESULT: {result_label} for {os.path.basename(filepath)}")

    return (1, 0) if all_passed else (0, 1)


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
        files_to_check = find_review_files(os.getcwd())
        if not files_to_check:
            print("No security review markdown files found in current directory.")
            print(
                "Usage: python3 check_security_architecture_review.py <path-to-review.md>"
            )
            sys.exit(0)

    print("Salesforce Security Architecture Review Validator")
    print("=" * 60)

    total_passed = 0
    total_failed = 0

    for filepath in files_to_check:
        passed, failed = validate_file(filepath)
        total_passed += passed
        total_failed += failed

    print("\n" + "=" * 60)
    print(f"Files checked: {total_passed + total_failed}")
    print(f"Passed: {total_passed}  |  Failed: {total_failed}")

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
