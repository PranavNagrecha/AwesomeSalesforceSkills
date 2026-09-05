#!/usr/bin/env python3
"""Backward-compatible alias for check_apex_scheduled_jobs.py.

The canonical implementation and the rule documentation live in
``check_apex_scheduled_jobs.py`` in this directory. This module exists so that older
references to ``check_apex_scheduled.py`` keep working; it delegates every argument
(including ``--manifest-dir`` and ``--strict``) and returns the same exit code.

Usage:
    python3 check_apex_scheduled.py --manifest-dir force-app/main/default/classes [--strict]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from check_apex_scheduled_jobs import main  # noqa: E402
except ImportError:
    print("ERROR: check_apex_scheduled_jobs.py is missing beside this alias; run the canonical checker directly", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
