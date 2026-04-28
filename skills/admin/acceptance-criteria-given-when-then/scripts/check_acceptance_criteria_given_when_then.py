#!/usr/bin/env python3
"""Compatibility wrapper — delegates to ``check_ac_format.py``.

The canonical lint script for this skill is ``check_ac_format.py``. This
wrapper exists so the auto-generated ``check_<skill_name>.py`` filename
expected by the scaffold continues to resolve. Both entry points lint the
same way.

Usage:
    python3 check_acceptance_criteria_given_when_then.py <story.md>
"""

from __future__ import annotations

import sys
from pathlib import Path

# Delegate to the canonical implementation in this same scripts/ folder.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from check_ac_format import main  # noqa: E402


def run() -> int:
    """Run the canonical AC-format lint and surface its issues.

    Exits with code 1 (ERROR) when issues are found, 0 when clean.
    """
    try:
        return main()
    except SystemExit as exc:
        # Propagate the underlying script's exit code so callers see ERRORs.
        return int(exc.code) if exc.code is not None else 0
    except Exception as exc:  # pragma: no cover - defensive
        print(f"ERROR: AC-format wrapper failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run())
