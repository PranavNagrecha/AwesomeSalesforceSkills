#!/usr/bin/env python3
"""Entry point for the data-model-design-patterns skill checker.

The implementation lives in check_data_model.py in this directory; this file keeps
the check_<skill-name>.py naming convention. Same arguments and exit codes:

    python3 check_data_model_design_patterns.py --manifest-dir force-app/main/default [--strict]

Exit codes: 0 clean or WARN only; 1 on ERROR, a missing directory, or WARN with
--strict. An empty directory prints a WARN and exits 0. Stdlib only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from check_data_model import main  # noqa: E402
except ImportError as exc:
    print(f"ERROR: cannot load check_data_model.py next to this file ({exc})")
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
