#!/usr/bin/env python3
"""Check list-view and compact-layout metadata for common UX smells."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check list views and compact layouts for common usability issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def child_texts(root: ET.Element, name: str) -> list[str]:
    return [(element.text or "").strip() for element in root.iter() if local_name(element.tag) == name]


def object_name_from_child_metadata(path: Path) -> str:
    try:
        return path.parent.parent.name
    except IndexError:
        return "unknown-object"


def check_list_views_and_compact_layouts(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    object_list_views: dict[str, list[Path]] = defaultdict(list)
    object_compact_layouts: dict[str, list[Path]] = defaultdict(list)

    for list_view_path in sorted(manifest_dir.rglob("*.listView-meta.xml")):
        object_name = object_name_from_child_metadata(list_view_path)
        object_list_views[object_name].append(list_view_path)

        root = parse_xml(list_view_path)
        if root is None:
            issues.append(f"{list_view_path}: unable to parse list view metadata.")
            continue

        columns = child_texts(root, "columns")
        filters = child_texts(root, "filters")
        boolean_filters = child_texts(root, "booleanFilter")
        filter_scope = " ".join(child_texts(root, "filterScope"))

        if len(columns) > 10:
            issues.append(
                f"{list_view_path}: list view has {len(columns)} columns; review whether the triage surface is too dense."
            )

        if not filters and not boolean_filters and filter_scope.lower() in {"everything", "all"}:
            issues.append(
                f"{list_view_path}: broad list view uses an all-records scope with no additional filters; review whether it should be narrowed or admin-only."
            )

    for compact_layout_path in sorted(manifest_dir.rglob("*.compactLayout-meta.xml")):
        object_name = object_name_from_child_metadata(compact_layout_path)
        object_compact_layouts[object_name].append(compact_layout_path)

        root = parse_xml(compact_layout_path)
        if root is None:
            issues.append(f"{compact_layout_path}: unable to parse compact layout metadata.")
            continue

        fields = child_texts(root, "fields")
        if len(fields) > 8:
            issues.append(
                f"{compact_layout_path}: compact layout exposes {len(fields)} fields; review whether the highlights panel is overloaded."
            )

    for object_name, list_views in sorted(object_list_views.items()):
        if len(list_views) > 15:
            issues.append(
                f"{object_name}: found {len(list_views)} list views; review for public view sprawl and near-duplicate working queues."
            )
        if len(list_views) >= 3 and not object_compact_layouts.get(object_name):
            issues.append(
                f"{object_name}: has multiple list views but no compact layout metadata was found; review whether highlights and mobile scan paths are missing."
            )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_list_views_and_compact_layouts(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
