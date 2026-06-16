#!/usr/bin/env python3
"""Checker for Agentforce Custom Lightning Types (LightningTypeBundle) metadata.

Validates a source-format metadata tree for the common mistakes documented in
references/gotchas.md and references/llm-anti-patterns.md. Stdlib only — no pip deps.

Usage:
    python3 check_agentforce_custom_lightning_types.py [--manifest-dir path]

It looks for `lightningTypes/<type>/schema.json` and channel-scoped
`editor.json` / `renderer.json` files, and reports concrete, actionable issues.
Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KNOWN_CHANNELS = {
    "lightningDesktopGenAi",
    "lightningMobileGenAi",
    "enhancedWebChat",
    "experienceBuilder",
}
OVERRIDE_PREFIXES = ("c/", "isv/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LightningTypeBundle metadata for common Agentforce custom-lightning-type issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source metadata (looks for a lightningTypes/ folder anywhere beneath it).",
    )
    return parser.parse_args()


def _load_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)


def _check_schema(schema_path: Path, issues: list[str]) -> None:
    data, err = _load_json(schema_path)
    if err is not None:
        issues.append(f"{schema_path}: not valid JSON ({err})")
        return
    if not isinstance(data, dict):
        issues.append(f"{schema_path}: expected a JSON object")
        return
    lt = data.get("lightning:type")
    if not lt:
        issues.append(
            f"{schema_path}: missing `lightning:type` — bind to the backing Apex class "
            f"with \"lightning:type\": \"@apexClassType/c__ClassName\""
        )
    elif isinstance(lt, str) and not lt.startswith("@apexClassType/"):
        issues.append(
            f"{schema_path}: `lightning:type` is '{lt}', expected an '@apexClassType/...' "
            f"binding (only Apex-class input/output can be overridden)"
        )
    if isinstance(data.get("properties"), dict) and len(data["properties"]) > 0:
        issues.append(
            f"{schema_path}: hand-authored `properties` block present — prefer projecting "
            f"fields from the Apex class via @apexClassType instead of re-declaring them"
        )


def _check_override(cfg_path: Path, root_key: str, channel: str, issues: list[str]) -> None:
    data, err = _load_json(cfg_path)
    if err is not None:
        issues.append(f"{cfg_path}: not valid JSON ({err})")
        return
    if not isinstance(data, dict) or root_key not in data:
        issues.append(f"{cfg_path}: expected a top-level '{root_key}' object")
        return
    overrides = (data.get(root_key) or {}).get("componentOverrides")
    if not isinstance(overrides, dict) or not overrides:
        issues.append(f"{cfg_path}: '{root_key}.componentOverrides' is missing or empty")
        return
    for scope, spec in overrides.items():
        definition = spec.get("definition") if isinstance(spec, dict) else None
        if not definition:
            issues.append(f"{cfg_path}: override '{scope}' is missing a 'definition' (e.g. 'c/myLwc')")
        elif not str(definition).startswith(OVERRIDE_PREFIXES):
            issues.append(
                f"{cfg_path}: definition '{definition}' should start with 'c/' (org) or "
                f"'isv/' (managed package)"
            )


def check(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    bundle_roots = sorted(manifest_dir.rglob("lightningTypes"))
    if not bundle_roots:
        return [f"No 'lightningTypes/' folder found under {manifest_dir} — nothing to check."]

    for lt_root in bundle_roots:
        if not lt_root.is_dir():
            continue
        for type_dir in sorted(p for p in lt_root.iterdir() if p.is_dir()):
            schema = type_dir / "schema.json"
            if not schema.exists():
                issues.append(f"{type_dir}: required schema.json is missing")
            else:
                _check_schema(schema, issues)

            for channel_dir in sorted(p for p in type_dir.iterdir() if p.is_dir()):
                channel = channel_dir.name
                if channel not in KNOWN_CHANNELS:
                    issues.append(
                        f"{channel_dir}: unrecognized channel folder '{channel}'. "
                        f"Expected one of: {', '.join(sorted(KNOWN_CHANNELS))}"
                    )
                editor = channel_dir / "editor.json"
                renderer = channel_dir / "renderer.json"
                if editor.exists():
                    _check_override(editor, "editor", channel, issues)
                if renderer.exists():
                    if channel == "experienceBuilder":
                        issues.append(
                            f"{renderer}: renderer.json is not supported in 'experienceBuilder' "
                            f"— use an editor override there"
                        )
                    _check_override(renderer, "renderer", channel, issues)
                if not editor.exists() and not renderer.exists():
                    issues.append(
                        f"{channel_dir}: channel folder has neither editor.json nor renderer.json"
                    )
    return issues


def main() -> int:
    args = parse_args()
    issues = check(Path(args.manifest_dir))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
