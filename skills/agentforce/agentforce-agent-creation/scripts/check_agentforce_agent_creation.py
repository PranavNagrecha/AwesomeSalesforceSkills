#!/usr/bin/env python3
"""Checker script for Agentforce Agent Creation skill.

Delegates to check_agent_creation.py in the same directory, which contains
the full implementation. This file is retained as the scaffolded entry point
for compatibility with skill_sync.py discovery conventions.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agentforce_agent_creation.py [--help]
    python3 check_agentforce_agent_creation.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add the scripts directory to the path so the real implementation is importable
_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from check_agent_creation import main  # noqa: E402

if __name__ == "__main__":
    result = main()
    if result:
        print(f"ERROR: {result} issue(s) found — see output above", file=sys.stderr)
    sys.exit(result)
