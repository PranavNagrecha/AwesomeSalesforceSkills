#!/usr/bin/env python3
"""Alias entrypoint — see check_process_flow_as_is_to_be.py.

The skill spec references this script name. It defers to the canonical
checker module so behaviour stays in one place.
"""

from __future__ import annotations

import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

# Delegate to the canonical checker module.
import check_process_flow_as_is_to_be as _impl  # noqa: E402

if __name__ == "__main__":
    rc = _impl.main()
    if rc != 0:
        # ERROR-path indicator so the repo lint that scans for sys.exit(1)
        # / "ERROR" / "WARN" prints recognises this script's failure modes.
        print(f"ERROR: process-map check exited with code {rc}", file=sys.stderr)
    sys.exit(rc)
