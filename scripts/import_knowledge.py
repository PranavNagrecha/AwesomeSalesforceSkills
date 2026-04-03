#!/usr/bin/env python3
"""Import curated markdown knowledge from a local source path."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import local markdown knowledge into knowledge/imports/.")
    parser.add_argument("--source", required=True, help="Local file or directory to import")
    args = parser.parse_args()

    source = Path(args.source).expanduser()
    if not source.exists():
        raise SystemExit(f"Source not found: {source}")

    base_name = slugify(source.stem if source.is_file() else source.name) or "imported-source"
    destination_root = ROOT / "knowledge" / "imports" / base_name
    destination_root.mkdir(parents=True, exist_ok=True)

    copied = 0
    if source.is_file():
        if source.suffix.lower() == ".md":
            shutil.copy2(source, destination_root / source.name)
            copied += 1
    else:
        for path in source.rglob("*.md"):
            relative = path.relative_to(source)
            target = destination_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied += 1

    print(f"Imported {copied} markdown file(s) into {destination_root.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
