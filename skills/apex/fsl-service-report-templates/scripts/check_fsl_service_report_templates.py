#!/usr/bin/env python3
"""Entry point for FSL Service Report Templates skill checker.

All real validation logic lives in check_service_report.py.
This module imports and re-exports it so both filenames work.

Usage:
    python3 check_fsl_service_report_templates.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the directory containing the real checker is importable
sys.path.insert(0, str(Path(__file__).parent))

from check_service_report import main  # noqa: E402

if __name__ == "__main__":
    result = main()
    if result:
        sys.exit(1)
    sys.exit(0)
