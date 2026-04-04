#!/usr/bin/env python3
"""
check_well_architected_review.py

Validates a Salesforce Well-Architected Framework review document.

Checks:
  1. All three WAF pillar sections are present (Trusted, Easy, Adaptable)
  2. A summary scorecard table is present (Red/Amber/Green)
  3. At least one recommendation per pillar is documented

Usage:
  python3 check_well_architected_review.py <path-to-review-file.md>
  python3 check_well_architected_review.py          # scans current directory for *review*.md files

Exit codes:
  0 — all checks passed
  1 — one or more checks failed
"""

import sys
import os
import re
import glob


def find_review_files(directory):
    """Find markdown files containing 'review' in the name within the given directory."""
    pattern = os.path.join(directory, "**", "*review*.md")
    return glob.glob(pattern, recursive=True)


def load_file(path):
    """Read file content, return None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        print(f"ERROR: Cannot read file '{path}': {e}")
        return None


def check_pillar_sections(content, filepath):
    """Check that all three WAF pillar sections are present."""
    results = []
    pillars = [
        ("Trusted", r"##[#]?\s+Trusted"),
        ("Easy", r"##[#]?\s+Easy"),
        ("Adaptable", r"##[#]?\s+Adaptable"),
    ]
    for pillar_name, pattern in pillars:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        results.append((pillar_name, found))
    return results


def check_scorecard(content):
    """Check that a summary scorecard table with Red/Amber/Green is present."""
    # Look for a table row containing at least one of the score values
    score_values = re.compile(r"\b(Red|Amber|Green)\b", re.IGNORECASE)
    # A scorecard table will have multiple rows; require at least 2 score value matches
    # close together (within 500 characters) to distinguish from scattered mentions
    matches = list(score_values.finditer(content))
    if len(matches) < 2:
        return False
    # Check that the term "scorecard" or a table header with "Score" exists
    has_scorecard_label = bool(
        re.search(r"\b(scorecard|score card|summary score)\b", content, re.IGNORECASE)
    )
    has_score_column = bool(re.search(r"\|\s*Score\s*\|", content, re.IGNORECASE))
    return has_scorecard_label or has_score_column


def check_recommendations(content):
    """Check that at least one recommendation exists per pillar."""
    results = {}
    pillars = ["Trusted", "Easy", "Adaptable"]

    # Split content into sections by pillar heading
    # Strategy: find each pillar heading and extract text until the next heading of same level
    for pillar in pillars:
        # Find the pillar section
        section_pattern = re.compile(
            r"##[#]?\s+" + re.escape(pillar) + r".*?(?=\n##[^#]|\Z)",
            re.IGNORECASE | re.DOTALL,
        )
        section_match = section_pattern.search(content)
        if not section_match:
            results[pillar] = False
            continue

        section_text = section_match.group(0)

        # A recommendation can appear as:
        # - A table row with content in the Recommendation column
        # - A line starting with "Recommendation:" or "- Recommend"
        # - A heading "Prioritized Recommendations" is global and counts for all pillars
        recommendation_in_section = bool(
            re.search(
                r"(Recommendation|recommend|action required|suggested fix)",
                section_text,
                re.IGNORECASE,
            )
        )
        results[pillar] = recommendation_in_section

    # Also check if there is a global Recommendations section
    has_global_recommendations = bool(
        re.search(
            r"##[#]?\s+(Prioritized\s+)?Recommendations?",
            content,
            re.IGNORECASE,
        )
    )

    # If global recommendations exist, all pillars benefit
    if has_global_recommendations:
        for pillar in pillars:
            if not results[pillar]:
                results[pillar] = True

    return results


def validate_file(filepath):
    """Run all checks against a single file. Returns (passed, failed) counts."""
    print(f"\nChecking: {filepath}")
    print("-" * 60)

    content = load_file(filepath)
    if content is None:
        return 0, 1

    all_passed = True

    # Check 1: Pillar sections
    pillar_results = check_pillar_sections(content, filepath)
    for pillar_name, found in pillar_results:
        status = "PASS" if found else "FAIL"
        if not found:
            all_passed = False
        print(f"  [{status}] Pillar section present: {pillar_name}")

    # Check 2: Scorecard
    has_scorecard = check_scorecard(content)
    status = "PASS" if has_scorecard else "FAIL"
    if not has_scorecard:
        all_passed = False
    print(f"  [{status}] Summary scorecard (Red/Amber/Green) present")

    # Check 3: Recommendations per pillar
    rec_results = check_recommendations(content)
    for pillar_name, has_rec in rec_results.items():
        status = "PASS" if has_rec else "FAIL"
        if not has_rec:
            all_passed = False
        print(f"  [{status}] At least one recommendation for: {pillar_name} pillar")

    if all_passed:
        print(f"\n  RESULT: All checks passed for {os.path.basename(filepath)}")
    else:
        print(f"\n  RESULT: One or more checks FAILED for {os.path.basename(filepath)}")

    return (1, 0) if all_passed else (0, 1)


def main():
    files_to_check = []

    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        sys.exit(0)

    if len(sys.argv) > 1:
        # File path(s) provided as arguments
        for arg in sys.argv[1:]:
            if os.path.isfile(arg):
                files_to_check.append(arg)
            else:
                print(f"ERROR: File not found: {arg}")
                sys.exit(1)
    else:
        # Scan current directory for *review*.md files
        files_to_check = find_review_files(os.getcwd())
        if not files_to_check:
            print("No review markdown files found in current directory.")
            print(
                "Usage: python3 check_well_architected_review.py <path-to-review.md>"
            )
            sys.exit(0)

    print("Salesforce WAF Review Validator")
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
