#!/usr/bin/env python3
"""End-to-end skill-batch shipper.

Runs: skill_forge → skill_sync --changed-only → validate_repo --changed-only
      → test_checkers --changed-only

Stops at the first non-zero step. Each step's output is streamed so failures
are diagnosable. Intended as the one-shot command a human runs after authoring
a batch spec.

Usage:
    python3 scripts/ship_skills.py --batch batches/my-batch.yaml
    python3 scripts/ship_skills.py --batch batches/my-batch.yaml --skip-tests
    python3 scripts/ship_skills.py --batch batches/my-batch.yaml --dry-run-forge
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(label: str, cmd: list[str]) -> int:
    print(f"\n┌─ {label}")
    print(f"│  $ {' '.join(cmd)}")
    print("└─")
    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        print(f"\n❌ {label} failed with exit {proc.returncode}. Stopping.")
    else:
        print(f"\n✔  {label} passed.")
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Ship a skill batch end-to-end.")
    parser.add_argument("--batch", required=True, help="Batch YAML to ship.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip checker fixture tests.")
    parser.add_argument("--skip-sync", action="store_true", help="Skip skill_sync (use if generated artifacts are managed separately).")
    parser.add_argument("--dry-run-forge", action="store_true", help="Run forge in dry-run; skip later steps.")
    args = parser.parse_args()

    py = sys.executable

    forge_cmd = [py, "scripts/skill_forge.py", "--batch", args.batch]
    if args.dry_run_forge:
        forge_cmd.append("--dry-run")
    rc = _run("forge", forge_cmd)
    if rc != 0 or args.dry_run_forge:
        return rc

    if not args.skip_sync:
        rc = _run("skill_sync (changed)", [py, "scripts/skill_sync.py", "--changed-only"])
        if rc != 0:
            return rc

    rc = _run("validate_repo (changed)", [py, "scripts/validate_repo.py", "--changed-only"])
    if rc != 0:
        return rc

    if not args.skip_tests:
        rc = _run("test_checkers (changed)", [py, "scripts/test_checkers.py", "--changed-only"])
        if rc != 0:
            return rc

    print("\n🚢  All steps passed. Ready to commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
