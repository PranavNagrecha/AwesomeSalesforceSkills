#!/usr/bin/env python3
"""Static orphan-candidate detector for Apex source.

Scans `force-app/main/default/classes/*.cls` files and flags classes that:

- have no references in any other Apex source file (.cls / .trigger)
- have no reference in flow / flexipage / weblink metadata
- are NOT annotated with @RestResource / @HttpGet / @HttpPost / etc.
- are NOT annotated with @deprecated already (already triaged)

Output is a candidate list. Coverage data is NOT consulted by this script —
pair it with a Tooling API query against `ApexCodeCoverageAggregate`.

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CLASS_DECL = re.compile(r"\b(?:public|global|private)\s+(?:abstract\s+|virtual\s+|with\s+sharing\s+|without\s+sharing\s+)*class\s+([A-Za-z_][A-Za-z0-9_]*)")
HTTP_ANNOTATION = re.compile(r"@(RestResource|HttpGet|HttpPost|HttpPut|HttpPatch|HttpDelete)\b")
DEPRECATED = re.compile(r"@deprecated\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Find orphan-candidate Apex classes.")
    p.add_argument("--manifest-dir", default=".", help="Salesforce DX project root.")
    return p.parse_args()


def collect_classes(root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for cls_path in (root / "force-app").rglob("*.cls"):
        text = cls_path.read_text(encoding="utf-8", errors="ignore")
        m = CLASS_DECL.search(text)
        if not m:
            continue
        if HTTP_ANNOTATION.search(text):
            continue
        if DEPRECATED.search(text):
            continue
        out[m.group(1)] = cls_path
    return out


def has_external_reference(name: str, root: Path, own_path: Path) -> bool:
    pattern = re.compile(r"\b" + re.escape(name) + r"\b")
    for ext in ("*.cls", "*.trigger", "*.flow-meta.xml", "*.flexipage-meta.xml",
                "*.weblink-meta.xml", "*.permissionset-meta.xml"):
        for p in (root / "force-app").rglob(ext):
            if p == own_path:
                continue
            try:
                if pattern.search(p.read_text(encoding="utf-8", errors="ignore")):
                    return True
            except OSError:
                continue
    return False


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not (root / "force-app").exists():
        print(f"ERROR: no force-app/ directory under {root}", file=sys.stderr)
        return 1

    candidates = collect_classes(root)
    orphan: list[str] = []
    for name, path in candidates.items():
        if not has_external_reference(name, root, path):
            orphan.append(f"{name}  ({path.relative_to(root)})")

    if not orphan:
        print("[code-coverage-orphan-class-cleanup] no orphan candidates found")
        return 0

    print("# Orphan-candidate classes (no source/metadata refs found):")
    for line in sorted(orphan):
        print(f"  - {line}")
    print(f"\nTotal: {len(orphan)}. Cross-check with ApexCodeCoverageAggregate before deleting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
