#!/usr/bin/env python3
"""Compatibility shim — delegates to ``check_uat_case.py``.

The canonical checker for this skill is ``check_uat_case.py`` (matches the
schema field name 'case'). This shim exists because the scaffold creates
``check_<skill_name>.py`` by default; we keep both so either name works.

Stdlib only.

Usage:
    python3 check_uat_test_case_design.py --help
    python3 check_uat_test_case_design.py --file cases.json
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "check_uat_case.py"


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: canonical checker not found: {TARGET}", file=sys.stderr)
        return 2
    # Delegate by re-executing the target script under its own __name__ so
    # argparse sees the expected program name.
    saved_argv = sys.argv[:]
    try:
        sys.argv = [str(TARGET), *saved_argv[1:]]
        runpy.run_path(str(TARGET), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = saved_argv
    return 0


if __name__ == "__main__":
    sys.exit(main())
