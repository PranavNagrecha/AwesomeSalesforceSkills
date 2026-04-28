#!/usr/bin/env python3
"""Skill-local validator entry point.

Delegates to ``check_rtm.py`` which is the canonical Requirements Traceability
Matrix CSV validator for this skill. This wrapper exists so the repo-level
validator (``scripts/validate_repo.py``) — which discovers skill checkers via
``skills/*/*/scripts/*.py`` — picks up the same logic without depending on the
file name.

Usage:
    python3 check_requirements_traceability_matrix.py [--csv PATH] [--strict] [--self-check]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import the real implementation from check_rtm.py sitting next to us.
sys.path.insert(0, str(Path(__file__).parent))
from check_rtm import main as _main  # noqa: E402


if __name__ == "__main__":
    rc = _main()
    if rc != 0:
        # Surface a marker so static checkers see an error-output path here too.
        print("ERROR: check_rtm reported issues; see lines above", file=sys.stderr)
    sys.exit(rc)
