#!/usr/bin/env python3
"""
check_slack_connect_patterns.py

Checks a Slack Connect governance document or notes file for required
compliance documentation elements.

Checks performed:
  1. Plan tier documented for both organizations
  2. DLP approach documented
  3. Data sovereignty / split-ownership acknowledgment present
  4. Retention policy documented
  5. eDiscovery export procedure referenced

Usage:
    python3 check_slack_connect_patterns.py <path-to-file>

Exit codes:
    0  All checks passed
    1  One or more checks failed
"""

import sys
import re
import os
import argparse


# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------

CHECKS = [
    {
        "id": "plan-tier",
        "description": "Plan tier documented for both organizations",
        "patterns": [
            r"(?i)(enterprise\s+grid|enterprise\+|business\+|pro\s+plan|paid\s+plan)",
            r"(?i)(plan\s+tier|subscription\s+tier|slack\s+plan)",
        ],
        "require_all": False,  # any pattern match is sufficient
        "advice": (
            "Document the Slack plan tier for BOTH the inviting and receiving organization. "
            "Native DLP availability depends on plan tier (Enterprise Grid/Enterprise+ only). "
            "Both orgs must be on a paid plan to use Slack Connect."
        ),
    },
    {
        "id": "dlp-approach",
        "description": "DLP approach documented",
        "patterns": [
            r"(?i)(dlp|data\s+loss\s+prevention|nightfall|purview|symantec\s+dlp|events\s+api)",
        ],
        "require_all": False,
        "advice": (
            "Document the DLP tooling for each organization. "
            "Enterprise Grid/Enterprise+ orgs: native Slack DLP (Admin Console > Policies > DLP). "
            "Pro/Business+ orgs: must use a third-party DLP vendor via the Slack Events API. "
            "Note that each organization's DLP rules apply only to its own members' messages."
        ),
    },
    {
        "id": "data-sovereignty",
        "description": "Data sovereignty / split-ownership acknowledgment present",
        "patterns": [
            r"(?i)(split.ownership|data\s+sovereignty|each\s+org(anization)?.*retain|"
            r"retention.*independent|asymmetric.*delet|delet.*asymmetric|"
            r"bilateral.*retention|own.*retention\s+polic)",
        ],
        "require_all": False,
        "advice": (
            "Acknowledge the split-ownership data model explicitly. "
            "Each organization retains its own members' messages under its own retention policy. "
            "Message deletion by one org does NOT propagate to the partner org. "
            "This asymmetry must be documented and acknowledged by legal/compliance."
        ),
    },
    {
        "id": "retention-policy",
        "description": "Retention policy documented",
        "patterns": [
            r"(?i)(retention\s+polic|retention\s+period|message\s+retention|"
            r"\d+[\s-]*(year|month|day)s?\s+retention|retention.*\d+\s*(year|month|day))",
        ],
        "require_all": False,
        "advice": (
            "Document the retention policy duration for each organization. "
            "Note any regulatory minimums (e.g., FINRA 3/6-year, SEC 17a-4 6-year). "
            "If organizations have agreed to matching retention policies, document that agreement "
            "and acknowledge it does not guarantee bilateral deletion."
        ),
    },
    {
        "id": "ediscovery",
        "description": "eDiscovery export procedure referenced",
        "patterns": [
            r"(?i)(ediscovery|e-discovery|compliance\s+export|legal\s+hold|litigation\s+hold|"
            r"export.*channel|channel.*export|parallel\s+export)",
        ],
        "require_all": False,
        "advice": (
            "Reference the eDiscovery export procedure. "
            "A single-organization export covers only that org's members' messages. "
            "A complete channel record requires parallel exports from all participating orgs, "
            "merged by timestamp. Inform legal/outside counsel of this requirement."
        ),
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file(path: str) -> str:
    """Read the file at path and return its text content."""
    if not os.path.isfile(path):
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def run_check(check: dict, content: str) -> bool:
    """Return True if the check passes, False otherwise."""
    patterns = check["patterns"]
    if check.get("require_all"):
        return all(re.search(p, content) for p in patterns)
    else:
        return any(re.search(p, content) for p in patterns)


def print_result(check: dict, passed: bool) -> None:
    status = "PASS" if passed else "FAIL"
    marker = "  [OK]" if passed else "  [!!]"
    print(f"{marker} [{status}] {check['id']}: {check['description']}")
    if not passed:
        print(f"        Advice: {check['advice']}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check a Slack Connect governance document for required compliance elements.",
    )
    parser.add_argument("file", help="Path to governance document to check")
    args = parser.parse_args()

    file_path = args.file
    content = read_file(file_path)

    print(f"Checking: {file_path}")
    print("=" * 60)

    failures = 0
    for check in CHECKS:
        passed = run_check(check, content)
        print_result(check, passed)
        if not passed:
            failures += 1

    print("=" * 60)
    if failures == 0:
        print(f"Result: PASSED — all {len(CHECKS)} checks passed.")
        return 0
    else:
        print(
            f"Result: FAILED — {failures} of {len(CHECKS)} check(s) failed. "
            "Add the missing documentation and re-run."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
