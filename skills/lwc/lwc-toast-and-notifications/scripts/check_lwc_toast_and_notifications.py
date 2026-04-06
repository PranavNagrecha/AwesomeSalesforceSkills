#!/usr/bin/env python3
"""Entry point alias for the LWC Toast And Notifications checker.

The canonical checker implementation is check_lwc_toasts.py in this directory.
This file exists for compatibility with the skill_sync scaffold naming convention.

Usage:
    python3 check_lwc_toast_and_notifications.py [--source-dir path] [--verbose]

Delegates directly to check_lwc_toasts.main().
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add this directory to the path so check_lwc_toasts is importable
sys.path.insert(0, str(Path(__file__).parent))

from check_lwc_toasts import main, check_file  # noqa: E402


def check_lwc_toast_and_notifications(source_dir):
    """Return issue strings for the given source directory."""
    js_files = sorted(source_dir.rglob("*.js"))
    issues = []
    for js_file in js_files:
        issues.extend(check_file(js_file))
    if issues:
        print(f"WARN: {len(issues)} toast/notification issue(s) detected", file=sys.stderr)
    return issues


if __name__ == "__main__":
    sys.exit(main())
