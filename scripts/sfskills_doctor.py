#!/usr/bin/env python3
"""Focused doctor for the SfSkills Cursor product."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.product.doctor import run_doctor


def main() -> int:
    parser = argparse.ArgumentParser(description="SfSkills doctor (Cursor product)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    report = run_doctor(args.root or ROOT)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"overall: {report['overall']}")
        for name, row in report["checks"].items():
            print(f"- {name}: {row.get('status')} — {row.get('detail')}")
        if report["checks"].get("search_index", {}).get("status") == "index_missing":
            print("\nindex_missing is not 'zero skills'. Run: python3 scripts/bootstrap.py")
    overall = report.get("overall")
    if overall == "error" or report["checks"].get("search_index", {}).get("status") == "index_missing":
        return 2
    if overall == "warn":
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
