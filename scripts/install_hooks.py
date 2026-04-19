#!/usr/bin/env python3
"""Install repo-local git hooks for validation and sync.

Two hooks ship under ``.githooks/``:

- ``pre-commit`` — fast per-file check. Runs ``skill_sync --changed-only``
  and ``validate_repo --changed-only``. Catches problems inside files you
  just edited. Typical runtime: <5s.

- ``pre-push`` — full shard sweep. Runs the same 4-shard validation CI
  runs. Catches cross-cutting drift that ``--changed-only`` can't see:
  stale generated artifacts, schema-enum drift (e.g. 'Performance
  Efficiency' from AWS WAF that doesn't match our enum), missing query
  fixtures. Typical runtime: 10–20s. Bypass with ``git push --no-verify``
  for WIP branches; CI will still gate merge.

Install once:

    python3 scripts/install_hooks.py

Uninstall (revert to .git/hooks):

    git config --unset core.hooksPath
"""

from __future__ import annotations

import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = ROOT / ".githooks"


def main() -> int:
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        print("No .git directory found. Install hooks manually once this repo is initialized as a git repository.")
        print("Suggested command:")
        print("  git config core.hooksPath .githooks")
        return 0

    # 1. Point git at .githooks/.
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT, check=True)
    print("✔ Configured git hooks to use .githooks/")

    # 2. Ensure every hook is executable — git silently ignores
    #    non-executable hook files, which has bitten us before.
    made_exec = 0
    if HOOKS_DIR.exists():
        for hook in HOOKS_DIR.iterdir():
            if hook.is_file() and not hook.name.endswith((".md", ".sample")):
                mode = hook.stat().st_mode
                if not (mode & stat.S_IXUSR):
                    hook.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    made_exec += 1
                    print(f"  chmod +x .githooks/{hook.name}")

    if made_exec == 0:
        print("✔ All hooks already executable.")

    # 3. Report what's active.
    if HOOKS_DIR.exists():
        hooks = sorted(
            h.name for h in HOOKS_DIR.iterdir()
            if h.is_file() and not h.name.endswith(".md")
        )
        print(f"\nActive hooks ({len(hooks)}):")
        for h in hooks:
            print(f"  - {h}")
    print("\nBypass any hook with --no-verify (git commit --no-verify / git push --no-verify).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
