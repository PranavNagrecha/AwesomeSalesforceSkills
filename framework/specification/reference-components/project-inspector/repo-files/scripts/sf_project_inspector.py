#!/usr/bin/env python3
"""Discover an optional Salesforce DX project and map one metadata component."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipelines.product.project_discover import (  # noqa: E402
    discover_salesforce_project,
    map_component_to_local_paths,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Discover a Salesforce DX project without assuming the SfSkills "
            "repository is the target project."
        )
    )
    parser.add_argument(
        "--project",
        help="Explicit Salesforce project path, descriptor path, or file inside the project",
    )
    parser.add_argument(
        "--workspace",
        action="append",
        default=[],
        help="Workspace root to scan (repeatable and bounded)",
    )
    parser.add_argument(
        "--cwd",
        help="Override the current directory used for ancestor discovery",
    )
    parser.add_argument("--component-type", help="Metadata type to map")
    parser.add_argument("--full-name", help="Metadata component full name to map")
    parser.add_argument("--line", type=int, help="Optional deployment-result line number")
    parser.add_argument("--column", type=int, help="Optional deployment-result column number")
    parser.add_argument(
        "--max-workspace-depth",
        type=int,
        default=4,
        help="Maximum recursive workspace depth (default: 4)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return nonzero for standalone or a component that is not mapped",
    )
    return parser


def _human_output(payload: dict[str, object]) -> str:
    discovery = payload["discovery"]
    assert isinstance(discovery, dict)
    lines = [
        f"status: {discovery.get('status')}",
        f"mode: {discovery.get('mode')}",
        f"project_root: {discovery.get('project_root') or '<none>'}",
    ]
    packages = discovery.get("package_directories") or []
    if packages:
        lines.append("package_directories:")
        for package in packages:
            lines.append(
                "  - {declared_path} (exists={exists}, default={default})".format(**package)
            )
    warnings = discovery.get("warnings") or []
    if warnings:
        lines.append("warnings:")
        lines.extend(f"  - {warning}" for warning in warnings)

    mapping = payload.get("mapping")
    if isinstance(mapping, dict):
        lines.append(f"mapping_status: {mapping.get('status')}")
        for match in mapping.get("matches") or []:
            lines.append(f"  - {match['path']}")
        for warning in mapping.get("warnings") or []:
            lines.append(f"  - {warning}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if bool(args.component_type) != bool(args.full_name):
        print(
            "--component-type and --full-name must be supplied together",
            file=sys.stderr,
        )
        return 2

    discovery = discover_salesforce_project(
        explicit_path=args.project,
        cwd=args.cwd,
        workspace_paths=args.workspace,
        max_workspace_depth=args.max_workspace_depth,
    )
    payload: dict[str, object] = {"discovery": discovery.to_dict()}

    mapping_status: str | None = None
    if args.component_type and args.full_name:
        mapping = map_component_to_local_paths(
            discovery,
            component_type=args.component_type,
            full_name=args.full_name,
            line=args.line,
            column=args.column,
        )
        payload["mapping"] = mapping.to_dict()
        mapping_status = mapping.status

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_human_output(payload))

    if discovery.status in {"invalid", "ambiguous"}:
        return 2
    if args.strict and discovery.status == "standalone":
        return 3
    if args.strict and mapping_status not in {None, "mapped"}:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
