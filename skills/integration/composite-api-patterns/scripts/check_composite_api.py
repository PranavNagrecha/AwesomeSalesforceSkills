#!/usr/bin/env python3
"""Checker script for Composite API Patterns skill.

Scans .json and .py files in a project directory for Salesforce Composite API
usage and flags common structural problems:
  - Composite requests with more than 25 subrequests
  - Use of /composite/batch/ URLs where referenceId cross-references are also present
  - Missing per-subrequest httpStatusCode inspection in Python files

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_composite_api.py [--project-dir PATH]
    python3 check_composite_api.py --project-dir /path/to/integration/project
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Maximum subrequests allowed by the Composite API platform limit
MAX_SUBREQUESTS = 25

# Regex patterns for scanning Python source files
_RE_COMPOSITE_URL = re.compile(
    r"/services/data/v[\d.]+/composite(?:/batch|/sobjects|/tree)?",
    re.IGNORECASE,
)
_RE_BATCH_URL = re.compile(
    r"/services/data/v[\d.]+/composite/batch",
    re.IGNORECASE,
)
_RE_REFERENCE_ID_USE = re.compile(
    r"@\{[A-Za-z_][A-Za-z0-9_]*\.",
)
_RE_OUTER_STATUS_ONLY = re.compile(
    r"status_code\s*==\s*200",
)
_RE_SUBREQUEST_CHECK = re.compile(
    r"httpStatusCode|compositeResponse|batchResponses",
    re.IGNORECASE,
)


def _check_json_file(path: Path) -> list[str]:
    """Check a JSON file for Composite API structural issues."""
    issues: list[str] = []
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        # Not parseable or unreadable — skip silently
        return issues

    # Check /composite/ requests: compositeRequest array length
    if isinstance(data, dict):
        composite_reqs = data.get("compositeRequest")
        if isinstance(composite_reqs, list):
            count = len(composite_reqs)
            if count > MAX_SUBREQUESTS:
                issues.append(
                    f"{path}: compositeRequest has {count} subrequests "
                    f"(platform limit is {MAX_SUBREQUESTS})"
                )

        # Check /composite/batch/ requests: batchRequests array length
        batch_reqs = data.get("batchRequests")
        if isinstance(batch_reqs, list):
            count = len(batch_reqs)
            if count > MAX_SUBREQUESTS:
                issues.append(
                    f"{path}: batchRequests has {count} subrequests "
                    f"(platform limit is {MAX_SUBREQUESTS})"
                )

            # Warn if referenceId cross-references appear in a batch request
            batch_text = json.dumps(batch_reqs)
            if _RE_REFERENCE_ID_USE.search(batch_text):
                issues.append(
                    f"{path}: /composite/batch/ request appears to contain "
                    "@{referenceId} cross-references, which are not supported "
                    "in batch subrequests — use /composite/ instead"
                )

    return issues


def _check_python_file(path: Path) -> list[str]:
    """Check a Python file for Composite API usage anti-patterns."""
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return issues

    if not _RE_COMPOSITE_URL.search(text):
        # File does not use the Composite API — nothing to check
        return issues

    # Flag files that call /composite/ or /composite/batch/ but only check the
    # outer HTTP status without inspecting per-subrequest results
    has_outer_status_check = bool(_RE_OUTER_STATUS_ONLY.search(text))
    has_subrequest_check = bool(_RE_SUBREQUEST_CHECK.search(text))

    if has_outer_status_check and not has_subrequest_check:
        issues.append(
            f"{path}: Composite API call detected but only outer status_code == 200 "
            "is checked. Per-subrequest 'httpStatusCode' or 'compositeResponse' "
            "inspection is required — outer HTTP 200 does not mean all subrequests succeeded."
        )

    # Flag files that use /composite/batch/ URL but also reference @{...} tokens
    if _RE_BATCH_URL.search(text) and _RE_REFERENCE_ID_USE.search(text):
        issues.append(
            f"{path}: /composite/batch/ URL detected alongside @{{referenceId}} "
            "cross-reference syntax. Batch subrequests cannot reference each other's "
            "results — use /composite/ for dependent subrequests."
        )

    return issues


def scan_project(project_dir: Path) -> list[str]:
    """Scan all .json and .py files under project_dir for issues."""
    issues: list[str] = []

    if not project_dir.exists():
        issues.append(f"Project directory not found: {project_dir}")
        return issues

    for json_path in sorted(project_dir.rglob("*.json")):
        issues.extend(_check_json_file(json_path))

    for py_path in sorted(project_dir.rglob("*.py")):
        issues.extend(_check_python_file(py_path))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check .json and .py files for Salesforce Composite API structural issues: "
            "subrequest count limits, referenceId misuse in batch requests, and "
            "missing per-subrequest error inspection."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    issues = scan_project(project_dir)

    if not issues:
        print("No Composite API issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
