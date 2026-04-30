#!/usr/bin/env python3
"""Static checker for navigation patterns in LWC.

Scans `force-app/.../lwc/<component>/*.js` files for:

- `NavigationMixin.Navigate(...)` followed by `.catch(` as the only error path
- `window.location.assign` / `window.location.href = ` near a NavigationMixin import
- Navigation calls in files containing record IDs but no `getRecord` wire

Stdlib only. The checks are heuristic; treat output as candidates to review.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAV_CALL = re.compile(r"NavigationMixin\.Navigate")
NAV_CATCH = re.compile(r"NavigationMixin\.Navigate[^;]*\)\.catch\b")
GET_RECORD = re.compile(r"\bgetRecord\b")
WINDOW_LOC = re.compile(r"window\.location\.(assign|replace|href)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lint LWC navigation patterns.")
    p.add_argument("--manifest-dir", default=".", help="Project root.")
    return p.parse_args()


def lwc_js_files(root: Path) -> list[Path]:
    return [p for p in (root / "force-app").rglob("lwc/*/*.js") if "__tests__" not in p.parts]


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return issues

    if not NAV_CALL.search(text):
        return issues

    if NAV_CATCH.search(text):
        issues.append(
            f"{path}: NavigationMixin.Navigate followed by .catch — pre-check the target instead"
        )
    if WINDOW_LOC.search(text):
        issues.append(
            f"{path}: window.location.* alongside NavigationMixin — bypasses Lightning routing"
        )
    if "recordId" in text and not GET_RECORD.search(text):
        issues.append(
            f"{path}: navigates by recordId without a getRecord pre-check"
        )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not (root / "force-app").exists():
        print(f"ERROR: no force-app/ directory under {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for f in lwc_js_files(root):
        issues.extend(check_file(f))

    if not issues:
        print("[lightning-navigation-dead-link-handling] no issues found")
        return 0
    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
