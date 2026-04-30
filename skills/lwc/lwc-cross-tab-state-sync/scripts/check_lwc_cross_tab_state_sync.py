#!/usr/bin/env python3
"""Static checker for cross-tab sync code in LWC.

Scans `force-app/.../lwc/<component>/*.js` files for:

- `new BroadcastChannel(` without a paired `.close()` somewhere in the file
- `addEventListener('storage'` without `removeEventListener('storage'`
- `localStorage.setItem` calls that look like they store object/PII fields

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NEW_BROADCAST = re.compile(r"new\s+BroadcastChannel\s*\(")
CHANNEL_CLOSE = re.compile(r"\.close\s*\(\s*\)")
ADD_STORAGE = re.compile(r"addEventListener\s*\(\s*['\"]storage['\"]")
REMOVE_STORAGE = re.compile(r"removeEventListener\s*\(\s*['\"]storage['\"]")
LOCAL_PUT = re.compile(r"localStorage\.setItem\s*\(\s*[^,]+,\s*JSON\.stringify\s*\(")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lint LWC cross-tab sync code.")
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

    if NEW_BROADCAST.search(text) and not CHANNEL_CLOSE.search(text):
        issues.append(f"{path}: BroadcastChannel created without a .close() call")
    if ADD_STORAGE.search(text) and not REMOVE_STORAGE.search(text):
        issues.append(f"{path}: storage listener added without matching removeEventListener")
    if LOCAL_PUT.search(text):
        issues.append(
            f"{path}: localStorage.setItem with JSON.stringify(object) — verify no PII is stored"
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
        print("[lwc-cross-tab-state-sync] no issues found")
        return 0
    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
