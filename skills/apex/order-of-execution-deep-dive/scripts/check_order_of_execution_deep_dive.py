#!/usr/bin/env python3
"""Alias entry point for the order-of-execution checker.

Delegates to check_order_of_execution.py in the same directory.
Kept for backward compatibility with skill_sync.py naming conventions.

Usage:
    python3 check_order_of_execution_deep_dive.py [--manifest-dir path] [--verbose]
"""
import runpy
import sys
from pathlib import Path

_main = Path(__file__).parent / "check_order_of_execution.py"
if not _main.exists():
    print(f"ERROR: delegate script not found: {_main}", file=sys.stderr)
    sys.exit(1)
sys.argv[0] = str(_main)
runpy.run_path(str(_main), run_name="__main__")
