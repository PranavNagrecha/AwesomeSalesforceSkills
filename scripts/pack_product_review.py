#!/usr/bin/env python3
"""Thin wrapper around pack_v2_review.main for product review packaging."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def main() -> int:
    target = Path(__file__).with_name("pack_v2_review.py")
    spec = importlib.util.spec_from_file_location("pack_v2_review", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
