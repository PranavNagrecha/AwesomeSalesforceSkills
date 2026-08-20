#!/usr/bin/env python3
"""Validate SfSkills V2 framework adoption in this repository.

Runs:
  - imported SFAEF specification package checks;
  - live migration-ledger reconciliation against skills/agents/commands/MCP tools;
  - optional traceability report generation.

Usage:
  python3 scripts/validate_framework.py
  python3 scripts/validate_framework.py --json
  python3 scripts/validate_framework.py --write-traceability
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = ROOT / "framework" / "specification"
TRACEABILITY_OUT = ROOT / "docs" / "product-v2" / "requirement-traceability.csv"
RECONCILE_REPORT = ROOT / "docs" / "product-v2" / "migration-reconciliation.md"


def _run_step(identifier: str, command: list[str], cwd: Path) -> dict:
    proc = subprocess.run(  # noqa: S603
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "id": identifier,
        "command": command,
        "cwd": str(cwd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _copy_traceability() -> None:
    source = SPEC_ROOT / "implementation" / "requirements.csv"
    if not source.is_file():
        raise FileNotFoundError(source)
    TRACEABILITY_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, TRACEABILITY_OUT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument(
        "--write-traceability",
        action="store_true",
        help="Copy implementation/requirements.csv to docs/product-v2/requirement-traceability.csv",
    )
    parser.add_argument(
        "--skip-spec-checks",
        action="store_true",
        help="Skip framework/specification/scripts/run_all_checks.py",
    )
    args = parser.parse_args(argv)

    if not SPEC_ROOT.is_dir():
        print(f"ERROR: specification not imported at {SPEC_ROOT}", file=sys.stderr)
        return 1

    sys.path.insert(0, str(ROOT))
    from pipelines.framework.migration_reconcile import (  # noqa: PLC0415
        reconcile_migration_ledgers,
        write_reconciliation_report,
    )

    steps: list[dict] = []
    if not args.skip_spec_checks:
        steps.append(
            _run_step(
                "spec-run-all-checks",
                [sys.executable, "-B", "scripts/run_all_checks.py"],
                SPEC_ROOT,
            )
        )

    reconcile = reconcile_migration_ledgers(ROOT, SPEC_ROOT / "migration" / "catalogs")
    write_reconciliation_report(reconcile, RECONCILE_REPORT)
    steps.append(
        {
            "id": "migration-reconcile",
            "command": ["pipelines.framework.migration_reconcile"],
            "cwd": str(ROOT),
            "exit_code": 0 if reconcile.valid else 1,
            "stdout": json.dumps(reconcile.to_dict(), indent=2, sort_keys=True),
            "stderr": "",
        }
    )

    if args.write_traceability:
        _copy_traceability()
        steps.append(
            {
                "id": "traceability-copy",
                "command": ["copy", str(SPEC_ROOT / "implementation" / "requirements.csv")],
                "cwd": str(ROOT),
                "exit_code": 0,
                "stdout": f"Wrote {TRACEABILITY_OUT}",
                "stderr": "",
            }
        )

    valid = all(step["exit_code"] == 0 for step in steps)
    report = {
        "valid": valid,
        "spec_root": str(SPEC_ROOT),
        "reconciliation_report": str(RECONCILE_REPORT),
        "steps": steps,
        "migration": reconcile.to_dict(),
    }

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"SfSkills V2 framework valid: {valid}")
        for step in steps:
            status = "OK" if step["exit_code"] == 0 else "FAIL"
            print(f"  [{status}] {step['id']} (exit={step['exit_code']})")
        if not reconcile.valid:
            print("Migration reconciliation deltas:")
            for item in reconcile.deltas:
                print(f"  - {item.artifact_class}/{item.artifact_id}: {item.delta_kind}")
        if args.write_traceability:
            print(f"Traceability: {TRACEABILITY_OUT}")

    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
