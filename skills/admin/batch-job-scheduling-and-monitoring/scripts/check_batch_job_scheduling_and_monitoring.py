#!/usr/bin/env python3
"""Checker script for Batch Job Scheduling And Monitoring skill.

Checks org metadata or configuration relevant to Batch Job Scheduling And Monitoring.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_batch_job_scheduling_and_monitoring.py [--help]
    python3 check_batch_job_scheduling_and_monitoring.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Batch Job Scheduling And Monitoring configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_batch_job_scheduling_and_monitoring(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks Batch Apex classes for missing finish() notification patterns
    and empty exception handling in execute().
    """
    import re

    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Find Apex class directories
    classes_dirs = []
    for candidate in [
        manifest_dir / "force-app" / "main" / "default" / "classes",
        manifest_dir / "src" / "classes",
        manifest_dir / "classes",
    ]:
        if candidate.exists():
            classes_dirs.append(candidate)

    for classes_dir in classes_dirs:
        for cls_file in classes_dir.glob("*.cls"):
            try:
                content = cls_file.read_text(encoding="utf-8", errors="replace")

                # Check for Database.Batchable implementation
                is_batch = "Database.Batchable" in content

                if not is_batch:
                    continue

                # Check if finish() method checks NumberOfErrors
                has_finish = "void finish(" in content or "global finish(" in content
                has_number_of_errors = "NumberOfErrors" in content
                has_send_email = "sendEmail" in content or "Messaging" in content

                if has_finish and not has_number_of_errors:
                    issues.append(
                        f"{cls_file.name}: Batch class has finish() method but does not check "
                        "NumberOfErrors. Salesforce does not send failure alerts automatically. "
                        "Query AsyncApexJob by bc.getJobId() in finish() and send a notification "
                        "when NumberOfErrors > 0."
                    )
                elif not has_finish:
                    issues.append(
                        f"{cls_file.name}: Batch class has no finish() method. "
                        "The finish() method is the only hook for failure notification. "
                        "Without it, batch failures are silent. Add finish() with NumberOfErrors check."
                    )

                # Check for catch(Exception e) without re-throw in execute()
                # Look for try/catch in execute that doesn't re-throw
                execute_match = re.search(
                    r'void execute\s*\([^)]+\)\s*\{(.*?)(?=\nvoid |\nstatic |\nglobal |$)',
                    content, re.DOTALL
                )
                if execute_match:
                    execute_body = execute_match.group(1)
                    has_catch = "catch" in execute_body
                    has_rethrow = "throw" in execute_body

                    if has_catch and not has_rethrow:
                        issues.append(
                            f"{cls_file.name}: Batch execute() catches exceptions without re-throwing. "
                            "This causes chunks to report as successful even when records fail, "
                            "making NumberOfErrors=0 an unreliable indicator. "
                            "Re-throw exceptions or log to a persistent object before continuing."
                        )

            except OSError:
                pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_batch_job_scheduling_and_monitoring(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
