#!/usr/bin/env python3
"""Wrapper for the stakeholder-raci-for-sf-projects checker.

The canonical checker is `check_raci.py` in the same directory.
This wrapper exists only because skill_sync.py / scaffolding expects
a script named after the skill folder.

Usage:
    python3 check_stakeholder_raci_for_sf_projects.py --json path/to/raci.json

It delegates straight to `check_raci.py`.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    target = Path(__file__).parent / "check_raci.py"
    if not target.exists():
        print(f"ERROR: companion checker not found at {target}", file=sys.stderr)
        return 2
    # Re-exec the real checker with the same argv (sans this wrapper's name).
    sys.argv = [str(target)] + sys.argv[1:]
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
