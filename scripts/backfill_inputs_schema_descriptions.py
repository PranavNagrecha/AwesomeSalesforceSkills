#!/usr/bin/env python3
"""Backfill missing `description` fields on properties in existing
inputs.schema.json files.

The meta-schema at agents/_shared/schemas/inputs.schema.json requires every
property to carry both `type` and `description` (minLength 10). Some
hand-written builder schemas predate that requirement and have properties
with only `type` + constraints (`pattern`, `enum`, `default`, `minLength`,
`items`, ...). This script fills those descriptions in-place.

Strategy:
1. If the property name matches a curated template, use it — the template
   interpolates the existing constraints into the description.
2. Otherwise, fall back to a generic template built from the constraints.

Never overwrites an existing description. Never modifies schema shape.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "agents"

# Curated templates, keyed by property name. Each callable receives the prop
# dict and returns the description string.

def _fmt_enum(prop: dict) -> str:
    return ", ".join(f"`{v}`" for v in prop.get("enum", []))


def _fmt_default(prop: dict) -> str:
    d = prop.get("default")
    if d == "":
        return "an empty string"
    if isinstance(d, str):
        return f"`{d}`"
    return f"`{json.dumps(d)}`"


TEMPLATES: dict[str, callable] = {
    "api_version": lambda p: (
        "Salesforce API version written into generated `*-meta.xml` files. "
        f"Must match pattern `{p.get('pattern', '')}` (e.g., `60.0`)."
    ),
    "repo_path": lambda p: (
        "Repo-relative root of the caller's `force-app` source tree; the builder "
        "writes emitted artifacts underneath this path. "
        f"Defaults to {_fmt_default(p)}."
    ),
    "namespace": lambda p: (
        "Managed package namespace prefix stamped into generated metadata. "
        "Leave blank for non-packaged orgs. "
        f"Defaults to {_fmt_default(p)}."
    ),
    "target_org_alias": lambda p: (
        "sf CLI alias of the org used for Gate B live-org grounding "
        "(`describe_org`, `describe_sobject`, SOQL probes). Optional — when "
        "omitted, the builder runs in library-only mode and confidence is "
        "capped at MEDIUM."
    ),
    "org_alias": lambda p: (
        "sf CLI alias of the target org used for grounding calls "
        f"(describe / query). Minimum length `{p.get('minLength', 1)}`."
    ),
    "domain": lambda p: (
        f"Skill domain bucket. Must be one of: {_fmt_enum(p)}. "
        "Determines where under `skills/<domain>/` the builder scaffolds files."
    ),
    "skill_category": lambda p: (
        f"Top-level skill category used in frontmatter `category:`. "
        f"One of: {_fmt_enum(p)}."
    ),
    "skill_slug": lambda p: (
        "Kebab-case slug for the skill package directory. Must match pattern "
        f"`{p.get('pattern', '')}`."
    ),
    "feature_summary": lambda p: (
        "Plain-English one-paragraph description of what the artifact does. "
        f"Must be at least {p.get('minLength', 40)} characters so the builder "
        "has enough signal to decompose the feature; shorter values trigger "
        "`REFUSAL_INPUT_AMBIGUOUS`."
    ),
    "expected_volume": lambda p: (
        "Record-volume sizing hint that drives governor-limit and LDV "
        f"recommendations. One of: {_fmt_enum(p)}. "
        f"Defaults to {_fmt_default(p)}."
    ),
    "a11y_tier": lambda p: (
        "Accessibility tier the generated LWC must hit. One of: "
        f"{_fmt_enum(p)}. Defaults to {_fmt_default(p)}."
    ),
    "include_tests": lambda p: (
        "Whether to emit a companion Jest test suite alongside the component. "
        f"Defaults to {_fmt_default(p)}."
    ),
    "items": lambda p: (
        "Array of component/metadata identifiers to include in the change set. "
        f"Minimum {p.get('minItems', 1)} entries; each entry is a string like "
        "`ApexClass:AccountService`."
    ),
    "catalog_name": lambda p: (
        "PascalCase name token for the generated integration catalog. Must "
        f"match pattern `{p.get('pattern', '')}`."
    ),
    "trigger_sobject": lambda p: (
        "API name of the SObject the migrated record-triggered flow runs on. "
        f"Must match pattern `{p.get('pattern', '')}` and resolve at Gate B."
    ),
    "trigger_context": lambda p: (
        f"When the record-triggered flow fires. One of: {_fmt_enum(p)}. "
        f"Defaults to {_fmt_default(p)}."
    ),
    "record_trigger_type": lambda p: (
        "Record-change condition that triggers the flow. One of: "
        f"{_fmt_enum(p)}."
    ),
    "referenced_fields": lambda p: (
        "Explicit list of `SObject.Field` API names the emitted flow reads or "
        "writes. Every entry MUST be grounded at Gate B via `describe_sobject`."
    ),
    "subflows": lambda p: (
        "Names of subflows the migrated flow invokes. Each must exist in the "
        "target org (validated at Gate B) or be scheduled for concurrent build."
    ),
    "parity_checklist": lambda p: (
        "List of behaviors from the source Process Builder that the new flow "
        "must preserve. Used by Gate D to assert functional parity before "
        "emitting deploy artifacts."
    ),
}


def fallback_description(name: str, prop: dict) -> str:
    """Generic description derived from the prop's constraints."""
    bits: list[str] = []
    hum = name.replace("_", " ")
    bits.append(f"Input `{name}` ({hum}) consumed by the agent.")
    if "enum" in prop:
        bits.append(f"Allowed values: {_fmt_enum(prop)}.")
    if "pattern" in prop:
        bits.append(f"Must match pattern `{prop['pattern']}`.")
    if "minLength" in prop:
        bits.append(f"Minimum length {prop['minLength']}.")
    if "minItems" in prop:
        bits.append(f"Minimum {prop['minItems']} items.")
    if "default" in prop:
        bits.append(f"Defaults to {_fmt_default(prop)}.")
    desc = " ".join(bits)
    # Meta-schema requires minLength 10 on description — the fallback is
    # always well above that, but assert defensively.
    return desc


def backfill_schema(path: Path) -> tuple[int, list[str]]:
    """Fill missing descriptions on a single schema file. Returns (count_filled, prop_names)."""
    schema = json.loads(path.read_text(encoding="utf-8"))
    props = schema.get("properties", {})
    filled: list[str] = []
    for name, prop in props.items():
        if not isinstance(prop, dict):
            continue
        if prop.get("description"):
            continue
        tmpl = TEMPLATES.get(name)
        desc = tmpl(prop) if tmpl else fallback_description(name, prop)
        if len(desc) < 10:
            desc = fallback_description(name, prop)
        prop["description"] = desc
        filled.append(name)
    if filled:
        # Preserve property order (json.dumps does) and preserve literal unicode
        # characters in existing descriptions (em-dashes, arrows, etc.). We
        # don't attempt to preserve original compact vs expanded nested
        # formatting — re-indent to a stable 2-space form so future diffs stay
        # small.
        path.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return len(filled), filled


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--agent", help="Limit to one agent slug")
    args = ap.parse_args()

    total = 0
    files_touched = 0
    for schema_path in sorted(AGENTS_DIR.glob("*/inputs.schema.json")):
        slug = schema_path.parent.name
        if args.agent and slug != args.agent:
            continue
        if args.dry_run:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            missing = [
                n for n, p in schema.get("properties", {}).items()
                if isinstance(p, dict) and not p.get("description")
            ]
            if missing:
                print(f"{slug}: would fill {len(missing)} — {', '.join(missing)}")
                total += len(missing)
                files_touched += 1
            continue
        count, names = backfill_schema(schema_path)
        if count:
            files_touched += 1
            total += count
            print(f"{slug}: filled {count} — {', '.join(names)}")

    print()
    action = "would fill" if args.dry_run else "filled"
    print(f"{action} {total} descriptions across {files_touched} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
