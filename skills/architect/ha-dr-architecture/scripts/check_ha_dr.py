#!/usr/bin/env python3
"""
check_ha_dr.py — stdlib-only checker for HA/DR Architecture skill usage.

Validates that a completed HA/DR architecture document covers the required
sections and flags common omissions before review.

Usage:
    python3 check_ha_dr.py <path-to-completed-template.md>

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import sys
import re


# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = [
    ("Shared Responsibility", r"shared responsibility", "Missing shared responsibility boundary section"),
    ("Trust Site Monitoring", r"trust.*site|api\.status\.salesforce|instance.*key", "Missing Trust site monitoring configuration"),
    ("RTO definition", r"\bRTO\b", "RTO not defined"),
    ("RPO definition", r"\bRPO\b", "RPO not defined"),
    ("Backup strategy", r"backup|own.*backup|veeam|backup and restore", "Backup strategy not documented"),
    ("Integration failover", r"circuit.*breaker|durable.*queue|sqs|service bus|anypoint|fallback|failover", "Integration failover pattern not documented"),
    ("Drain procedure", r"drain", "Queue drain procedure not mentioned"),
    ("Incident commander", r"incident.*commander|commander", "Incident commander not assigned"),
    ("Runbook", r"runbook", "DR runbook section not present"),
    ("Post-incident review", r"post.incident|post incident", "Post-incident review step not documented"),
]

TODO_PATTERN = re.compile(r"\bTODO\b", re.IGNORECASE)

RTO_RPO_TARGET_PATTERN = re.compile(
    r"\|\s*(RTO Target|RPO Target)\s*\|\s*\|",  # empty table cell next to RTO/RPO Target
    re.IGNORECASE,
)

INSTANCE_KEY_PLACEHOLDER = re.compile(
    r"Production Instance Key\s*\|\s*\(e\.g\.,|Production Instance Key\s*\|\s*$",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_document(path: str) -> list[str]:
    """Return a list of failure messages. Empty list means all checks passed."""
    try:
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
    except FileNotFoundError:
        return [f"File not found: {path}"]
    except OSError as exc:
        return [f"Could not read file: {exc}"]

    failures = []
    content_lower = content.lower()

    # 1. Required section checks
    for label, pattern, message in REQUIRED_SECTIONS:
        if not re.search(pattern, content_lower):
            failures.append(f"[MISSING] {message} (expected pattern: '{pattern}')")

    # 2. Unfilled TODO markers
    todo_count = len(TODO_PATTERN.findall(content))
    if todo_count > 0:
        failures.append(
            f"[INCOMPLETE] {todo_count} TODO marker(s) remain — fill in all placeholders before finalizing"
        )

    # 3. RTO/RPO targets appear to be blank
    if RTO_RPO_TARGET_PATTERN.search(content):
        failures.append(
            "[INCOMPLETE] RTO or RPO target cells appear to be empty in the table — define values from business requirements"
        )

    # 4. Production instance key is still a placeholder
    if INSTANCE_KEY_PLACEHOLDER.search(content):
        failures.append(
            "[INCOMPLETE] Production instance key not filled in — identify the org instance from Setup > Company Information"
        )

    # 5. Restore test date check
    if re.search(r"last restore test date\s*\|\s*\|", content_lower):
        failures.append(
            "[INCOMPLETE] Last restore test date is blank — a backup that has never been tested is not a validated backup strategy"
        )

    # 6. Warn if Big Objects are mentioned but backup coverage not confirmed
    if re.search(r"big object", content_lower):
        if not re.search(r"big object.*backup|backup.*big object", content_lower):
            failures.append(
                "[WARNING] Big Objects are referenced but backup coverage is not explicitly confirmed — "
                "most backup tools do not support Big Object backup; verify with your vendor"
            )

    return failures


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("Usage: python3 check_ha_dr.py <path-to-completed-template.md>")
        print()
        print("Validates a completed HA/DR architecture document for required sections,")
        print("unfilled placeholders, and common omissions.")
        return 0

    path = sys.argv[1]
    failures = check_document(path)

    if failures:
        print(f"HA/DR Architecture Check — FAILED ({len(failures)} issue(s) found)")
        print("=" * 60)
        for msg in failures:
            print(f"  {msg}")
        print()
        print("Fix the issues above before treating this document as review-ready.")
        return 1

    print("HA/DR Architecture Check — PASSED")
    print("All required sections present and no unfilled placeholders detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
