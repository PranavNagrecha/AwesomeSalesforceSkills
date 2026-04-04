#!/usr/bin/env python3
"""Entry point for sandbox-refresh-and-templates checker.

Delegates to check_sandbox_refresh.py in the same directory.

Usage:
    python3 check_sandbox_refresh_and_templates.py [--manifest-dir path/to/metadata]
"""
import runpy
import sys
from pathlib import Path

if __name__ == '__main__':
    # Run the real implementation in the same scripts/ directory
    real_script = Path(__file__).parent / 'check_sandbox_refresh.py'
    if not real_script.exists():
        print("ERROR: check_sandbox_refresh.py not found", file=sys.stderr)
        sys.exit(1)
    sys.argv[0] = str(real_script)
    runpy.run_path(str(real_script), run_name='__main__')
