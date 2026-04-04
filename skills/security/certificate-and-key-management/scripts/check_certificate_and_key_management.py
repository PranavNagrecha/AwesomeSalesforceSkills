#!/usr/bin/env python3
"""Checker script for Certificate and Key Management skill.

Delegates to check_certificate.py in the same directory for the full implementation.
This file satisfies the skill framework's naming convention requirement.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_certificate_and_key_management.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Re-use the implementation from check_certificate.py in the same directory.
_IMPL = Path(__file__).parent / "check_certificate.py"

if _IMPL.exists():
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_certificate", _IMPL)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    sys.exit(module.main())
else:
    print(f"ERROR: Implementation script not found at {_IMPL}", file=sys.stderr)
    sys.exit(2)
