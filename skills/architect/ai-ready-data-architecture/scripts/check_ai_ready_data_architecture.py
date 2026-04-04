#!/usr/bin/env python3
"""
check_ai_ready_data_architecture.py

Validates an AI-Ready Data Architecture assessment document against structural
and content requirements.

Checks:
  1. All required top-level sections are present
  2. Data quality gate checklist is present and not entirely blank
  3. At least one AI feature is declared in the scope section
  4. Official sources are referenced in the well-architected file (if provided)
  5. No unresolved placeholder text remains (e.g., "[Enter", "TODO", "[TBD]")

Usage:
  python3 check_ai_ready_data_architecture.py <path-to-assessment.md>
  python3 check_ai_ready_data_architecture.py          # scans cwd for *ai-ready*.md or *assessment*.md

Exit codes:
  0 — all checks passed
  1 — one or more checks failed
"""

import sys
import os
import re
import glob


REQUIRED_SECTIONS = [
    ("Scope and AI Features", r"##[#]?\s+\d*\.?\s*Scope"),
    ("Data Completeness Audit", r"##[#]?\s+\d*\.?\s*Data Completeness"),
    ("Data Placement", r"##[#]?\s+\d*\.?\s*Data Placement"),
    ("Data Freshness", r"##[#]?\s+\d*\.?\s*Data Freshness"),
    ("Data Quality Gate", r"##[#]?\s+\d*\.?\s*Data Quality Gate"),
]

PLACEHOLDER_PATTERNS = [
    r"\[Enter\s",
    r"\bTODO\b",
    r"\[TBD\]",
    r"\[PLACEHOLDER\]",
    r"\[Insert\s",
]


def find_assessment_files(directory):
    """Find markdown files that look like AI-readiness assessments."""
    patterns = [
        os.path.join(directory, "**", "*ai-ready*.md"),
        os.path.join(directory, "**", "*ai_ready*.md"),
        os.path.join(directory, "**", "*assessment*.md"),
    ]
    found = []
    for pattern in patterns:
        found.extend(glob.glob(pattern, recursive=True))
    # Deduplicate
    return list(dict.fromkeys(found))


def load_file(path):
    """Read file content; return None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        print(f"ERROR: Cannot read file '{path}': {e}")
        return None


def check_required_sections(content, filepath):
    """Check that all required top-level sections are present."""
    results = []
    for section_name, pattern in REQUIRED_SECTIONS:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        results.append((section_name, found))
    return results


def check_quality_gate_populated(content):
    """Check that the data quality gate checklist has at least one non-blank status."""
    # Look for Red, Amber, or Green status values in a table row
    gate_status_pattern = re.compile(r"\|\s*(Red|Amber|Green)\s*\|", re.IGNORECASE)
    matches = gate_status_pattern.findall(content)
    return len(matches) >= 1, len(matches)


def check_ai_feature_declared(content):
    """Check that at least one AI feature is declared (not just the template placeholder)."""
    # Look for a table row with a feature type that has been filled in
    feature_pattern = re.compile(
        r"\|\s*(Predictive scoring|RAG|Classification|Recommendation|Einstein|Agentforce|scoring|grounding)\s*\|",
        re.IGNORECASE,
    )
    return bool(feature_pattern.search(content))


def check_no_placeholders(content):
    """Check that no unresolved placeholder text remains."""
    found_placeholders = []
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            found_placeholders.extend(matches)
    return found_placeholders


def check_official_sources(content):
    """Check that at least one official Salesforce URL is referenced."""
    url_pattern = re.compile(
        r"https?://(architect\.salesforce\.com|help\.salesforce\.com|developer\.salesforce\.com)"
    )
    matches = url_pattern.findall(content)
    return len(matches) >= 1, len(matches)


def run_checks(filepath):
    """Run all checks against the given file. Return (passed, total) counts."""
    print(f"\nChecking: {filepath}")
    print("-" * 60)

    content = load_file(filepath)
    if content is None:
        return 0, 1

    passed = 0
    total = 0

    # Check 1: Required sections
    section_results = check_required_sections(content, filepath)
    for section_name, found in section_results:
        total += 1
        status = "PASS" if found else "FAIL"
        if found:
            passed += 1
        print(f"  [{status}] Required section present: {section_name}")

    # Check 2: Quality gate populated
    total += 1
    gate_populated, gate_count = check_quality_gate_populated(content)
    if gate_populated:
        passed += 1
        print(f"  [PASS] Data quality gate checklist has {gate_count} status value(s)")
    else:
        print("  [FAIL] Data quality gate checklist has no populated status values (Red/Amber/Green)")

    # Check 3: AI feature declared
    total += 1
    if check_ai_feature_declared(content):
        passed += 1
        print("  [PASS] At least one AI feature type is declared in scope section")
    else:
        print("  [FAIL] No AI feature type found in scope table — template may be unfilled")

    # Check 4: No placeholder text
    total += 1
    placeholders = check_no_placeholders(content)
    if not placeholders:
        passed += 1
        print("  [PASS] No unresolved placeholder text found")
    else:
        print(f"  [FAIL] Unresolved placeholder text found: {placeholders[:5]}")

    # Check 5: Official sources referenced
    total += 1
    has_sources, source_count = check_official_sources(content)
    if has_sources:
        passed += 1
        print(f"  [PASS] {source_count} official Salesforce URL(s) referenced")
    else:
        print("  [FAIL] No official Salesforce URLs found — add sources to well-architected.md or assessment doc")

    return passed, total


def main():
    args = sys.argv[1:]
    if args and args[0] == "--help":
        print(__doc__)
        sys.exit(0)
    args = [a for a in args if not a.startswith("-")]

    if args:
        files_to_check = args
    else:
        cwd = os.getcwd()
        files_to_check = find_assessment_files(cwd)
        if not files_to_check:
            print("No AI-readiness assessment files found in current directory.")
            print("Usage: python3 check_ai_ready_data_architecture.py <path-to-assessment.md>")
            sys.exit(0)

    total_passed = 0
    total_checks = 0

    for filepath in files_to_check:
        p, t = run_checks(filepath)
        total_passed += p
        total_checks += t

    print("\n" + "=" * 60)
    print(f"Results: {total_passed}/{total_checks} checks passed")

    if total_passed == total_checks:
        print("All checks passed.")
        sys.exit(0)
    else:
        print(f"{total_checks - total_passed} check(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
