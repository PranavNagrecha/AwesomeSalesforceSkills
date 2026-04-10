#!/usr/bin/env python3
"""Entry-point alias for the subscription management architecture checker.

Delegates to check_subscription_arch.py in the same directory.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_subscription_management_architecture.py [--help]
    python3 check_subscription_management_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import sys
from pathlib import Path

# Delegate to the primary checker in the same directory
_checker = Path(__file__).parent / "check_subscription_arch.py"

if not _checker.exists():
    print(f"ERROR: Primary checker not found at {_checker}", file=sys.stderr)
    sys.exit(2)

# Execute the checker module directly
import importlib.util

spec = importlib.util.spec_from_file_location("check_subscription_arch", _checker)
module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
spec.loader.exec_module(module)  # type: ignore[union-attr]
sys.exit(module.main())
