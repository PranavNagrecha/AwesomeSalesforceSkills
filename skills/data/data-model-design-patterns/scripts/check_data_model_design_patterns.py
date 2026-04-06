#!/usr/bin/env python3
"""Entry point shim for the data-model-design-patterns skill checker.

The full implementation lives in check_data_model.py (same directory).
This file satisfies the skill scaffolding convention of having a file
named check_<skill-name>.py while keeping the canonical logic in the
more descriptively named module.

Usage:
    python3 check_data_model_design_patterns.py --manifest-dir path/to/metadata
    python3 check_data_model.py --manifest-dir path/to/metadata  (equivalent)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Re-export the real implementation from check_data_model.py
_this_dir = Path(__file__).parent
sys.path.insert(0, str(_this_dir))

from check_data_model import main, run_all_checks  # noqa: E402


def check_data_model_design_patterns(manifest_dir: Path) -> list[str]:
    """Return issue strings for the given manifest directory."""
    issues = run_all_checks(manifest_dir)
    if issues:
        print(f"WARN: {len(issues)} data model issue(s) detected", file=sys.stderr)
    return issues


if __name__ == "__main__":
    sys.exit(main())
