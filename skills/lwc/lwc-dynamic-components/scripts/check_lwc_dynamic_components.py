#!/usr/bin/env python3
"""Entry point alias for the LWC Dynamic Components checker.

The canonical checker is check_lwc_dynamic.py in this directory.
This file delegates to it so both names work.

Usage:
    python3 check_lwc_dynamic_components.py [--manifest-dir path/to/lwc]
"""

import sys
from pathlib import Path

# Add this directory to the path and run the canonical checker
sys.path.insert(0, str(Path(__file__).parent))

from check_lwc_dynamic import main, check_dynamic_components  # noqa: E402


def check_lwc_dynamic_components(manifest_dir):
    """Return issue strings for the given manifest directory."""
    issues = check_dynamic_components(manifest_dir)
    if issues:
        print(f"WARN: {len(issues)} dynamic component issue(s) detected", file=sys.stderr)
    return issues


if __name__ == '__main__':
    sys.exit(main())
