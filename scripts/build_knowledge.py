#!/usr/bin/env python3
"""Rebuild knowledge mappings and retrieval chunks."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.sync_engine import build_state, write_state


def main() -> int:
    state = build_state(ROOT)
    changed = write_state(ROOT, state)
    print(f"Knowledge sync complete. Files touched: {len(changed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
