#!/usr/bin/env python3
"""Checker for Salesforce-anchored persona + journey artifacts.

Validates a JSON file (or directory of JSON files) of personas and journeys
against the canonical schema for `skills/admin/persona-and-journey-mapping-sf`.

Stdlib only — no pip dependencies.

Checks:
  * Every persona has `psg_assigned` (non-empty).
  * Every persona has at least one entry in `primary_record_types`.
  * Every persona has at least one entry in `primary_list_views`.
  * `mobile_pct` and `desktop_pct` are present and sum to 100 (±2).
  * Every journey has ≥3 steps.
  * Every friction `tag` is in the fixed enum.
  * Every journey has a non-empty `next_task`.
  * No journey step uses `surface: "system"` or describes a system event.
  * No persona is orphaned (every persona is referenced by ≥1 journey).
  * Persona count is ≤ 7.

Usage:
    python3 check_persona.py path/to/handoff.json
    python3 check_persona.py path/to/dir/        # walks .json files
    python3 check_persona.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

FRICTION_ENUM: set[str] = {
    "cognitive_load",
    "click_count",
    "mode_switch",
    "data_input",
    "search",
}

ALLOWED_SURFACES: set[str] = {"mobile", "desktop", "console"}

SYSTEM_KEYWORDS: tuple[str, ...] = (
    "trigger fires",
    "callout",
    "outbound message",
    "approval routes",
    "apex executes",
    "platform event published",
)

MAX_PERSONAS_PER_PHASE = 7


def load_artifact(path: Path) -> dict[str, Any]:
    """Load a JSON file and normalize to a dict with 'personas' and 'journeys'."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if isinstance(data, list):
        # Heuristic: list of records — split by presence of 'task' key.
        personas = [r for r in data if isinstance(r, dict) and "task" not in r]
        journeys = [r for r in data if isinstance(r, dict) and "task" in r]
        return {"personas": personas, "journeys": journeys}

    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON must be object or array")

    return {
        "personas": data.get("personas", []),
        "journeys": data.get("journeys", []),
    }


def check_persona(persona: dict[str, Any], idx: int) -> list[str]:
    issues: list[str] = []
    pid = persona.get("persona_id") or f"<index {idx}>"

    if not persona.get("psg_assigned"):
        issues.append(f"persona[{pid}]: missing or empty psg_assigned")

    rts = persona.get("primary_record_types") or []
    if not isinstance(rts, list) or len(rts) == 0:
        issues.append(f"persona[{pid}]: primary_record_types must be a non-empty list")

    lvs = persona.get("primary_list_views") or []
    if not isinstance(lvs, list) or len(lvs) == 0:
        issues.append(f"persona[{pid}]: primary_list_views must be a non-empty list")

    mobile = persona.get("mobile_pct")
    desktop = persona.get("desktop_pct")
    if mobile is None or desktop is None:
        issues.append(
            f"persona[{pid}]: mobile_pct and desktop_pct are required "
            "(use null + posture_source='UNAVAILABLE' if measurement pending)"
        )
    else:
        try:
            total = float(mobile) + float(desktop)
            if abs(total - 100) > 2:
                issues.append(
                    f"persona[{pid}]: mobile_pct + desktop_pct = {total} "
                    "(must be ~100, tolerance ±2)"
                )
        except (TypeError, ValueError):
            issues.append(
                f"persona[{pid}]: mobile_pct/desktop_pct must be numeric"
            )

    return issues


def check_journey(journey: dict[str, Any], idx: int, persona_ids: set[str]) -> list[str]:
    issues: list[str] = []
    pid = journey.get("persona_id") or f"<journey index {idx}>"
    task = journey.get("task") or "<no task>"
    label = f"journey[{pid}::{task}]"

    if pid not in persona_ids and journey.get("persona_id"):
        issues.append(f"{label}: persona_id '{pid}' not found in personas list")

    steps = journey.get("steps") or []
    if not isinstance(steps, list) or len(steps) < 3:
        issues.append(f"{label}: journey must have ≥3 steps (got {len(steps) if isinstance(steps, list) else 0})")

    if isinstance(steps, list):
        for s_idx, step in enumerate(steps):
            if not isinstance(step, dict):
                issues.append(f"{label}: step {s_idx} must be an object")
                continue
            surface = step.get("surface", "")
            if surface and surface not in ALLOWED_SURFACES and surface != "system":
                issues.append(
                    f"{label}: step {s_idx} has unknown surface '{surface}' "
                    f"(allowed: {sorted(ALLOWED_SURFACES)})"
                )
            if surface == "system":
                issues.append(
                    f"{label}: step {s_idx} uses surface='system' — "
                    "system events do not belong in a journey, route to process-flow-as-is-to-be"
                )
            step_text = (step.get("step") or "").lower()
            for kw in SYSTEM_KEYWORDS:
                if kw in step_text:
                    issues.append(
                        f"{label}: step {s_idx} contains system keyword '{kw}' "
                        "— journeys describe user actions only"
                    )
                    break
            if "friction" in step and step["friction"] not in FRICTION_ENUM:
                issues.append(
                    f"{label}: step {s_idx} has friction tag '{step['friction']}' "
                    f"not in enum {sorted(FRICTION_ENUM)}"
                )

    fps = journey.get("friction_points") or []
    if isinstance(fps, list):
        for fp_idx, fp in enumerate(fps):
            if not isinstance(fp, dict):
                issues.append(f"{label}: friction_points[{fp_idx}] must be an object")
                continue
            tag = fp.get("tag")
            if tag not in FRICTION_ENUM:
                issues.append(
                    f"{label}: friction_points[{fp_idx}] has tag '{tag}' "
                    f"not in enum {sorted(FRICTION_ENUM)}"
                )

    next_task = journey.get("next_task")
    if not next_task or not str(next_task).strip():
        issues.append(
            f"{label}: missing or empty next_task — journeys must not end at 'save'"
        )

    return issues


def check_orphans(
    personas: list[dict[str, Any]], journeys: list[dict[str, Any]]
) -> list[str]:
    issues: list[str] = []
    referenced = {j.get("persona_id") for j in journeys if isinstance(j, dict)}
    for p in personas:
        if not isinstance(p, dict):
            continue
        pid = p.get("persona_id")
        if pid and pid not in referenced:
            issues.append(
                f"persona[{pid}]: orphan — no journey references this persona_id"
            )
    return issues


def check_count(personas: list[dict[str, Any]]) -> list[str]:
    if len(personas) > MAX_PERSONAS_PER_PHASE:
        return [
            f"too many personas: {len(personas)} > {MAX_PERSONAS_PER_PHASE} "
            "(merge personas sharing PSG + primary tasks)"
        ]
    return []


def check_artifact(payload: dict[str, Any]) -> list[str]:
    personas = payload.get("personas") or []
    journeys = payload.get("journeys") or []
    issues: list[str] = []

    if not isinstance(personas, list):
        return ["personas must be a list"]
    if not isinstance(journeys, list):
        return ["journeys must be a list"]

    persona_ids: set[str] = set()
    for idx, p in enumerate(personas):
        if not isinstance(p, dict):
            issues.append(f"persona[{idx}]: must be an object")
            continue
        if p.get("persona_id"):
            persona_ids.add(p["persona_id"])
        issues.extend(check_persona(p, idx))

    for idx, j in enumerate(journeys):
        if not isinstance(j, dict):
            issues.append(f"journey[{idx}]: must be an object")
            continue
        issues.extend(check_journey(j, idx, persona_ids))

    issues.extend(check_orphans(personas, journeys))
    issues.extend(check_count(personas))

    return issues


def gather_paths(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(target.rglob("*.json"))
    return []


def self_test() -> int:
    """Run a tiny self-test on a synthetic payload."""
    good = {
        "personas": [
            {
                "persona_id": "outside_sales_rep",
                "psg_assigned": "PSG_Sales_Field",
                "primary_record_types": ["Account.Customer"],
                "primary_list_views": ["My_Open_Opps"],
                "dashboards": ["Field_Sales_Daily"],
                "mobile_pct": 70,
                "desktop_pct": 30,
            }
        ],
        "journeys": [
            {
                "persona_id": "outside_sales_rep",
                "task": "Log a visit",
                "frequency": "daily",
                "steps": [
                    {"step": "Open app", "surface": "mobile"},
                    {"step": "Tap list view", "surface": "mobile"},
                    {"step": "Save", "surface": "mobile"},
                ],
                "friction_points": [
                    {"step_index": 1, "tag": "data_input", "note": "no default"}
                ],
                "next_task": "Drive to next account",
            }
        ],
    }
    bad = {
        "personas": [
            {
                "persona_id": "vague_user",
                "primary_record_types": [],
                "primary_list_views": [],
            }
        ],
        "journeys": [
            {
                "persona_id": "vague_user",
                "task": "Do thing",
                "steps": [{"step": "Trigger fires after save", "surface": "system"}],
                "friction_points": [{"tag": "annoying"}],
            }
        ],
    }
    good_issues = check_artifact(good)
    bad_issues = check_artifact(bad)
    if good_issues:
        print("SELF-TEST FAILED: good payload reported issues:")
        for i in good_issues:
            print(f"  - {i}")
        return 1
    if not bad_issues:
        print("SELF-TEST FAILED: bad payload reported no issues")
        return 1
    print(f"SELF-TEST OK: good=0 issues, bad={len(bad_issues)} issues detected.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Salesforce persona + journey artifacts.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Path to a JSON file or a directory of JSON files.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run an internal self-test on synthetic payloads and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.self_test:
        return self_test()

    if not args.target:
        print("ERROR: provide a target path or --self-test", file=sys.stderr)
        return 2

    target = Path(args.target)
    paths = gather_paths(target)
    if not paths:
        print(f"ERROR: no JSON files found at {target}", file=sys.stderr)
        return 2

    total_issues = 0
    for path in paths:
        try:
            payload = load_artifact(path)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            total_issues += 1
            continue

        issues = check_artifact(payload)
        if issues:
            print(f"--- {path}")
            for issue in issues:
                print(f"  WARN: {issue}", file=sys.stderr)
            total_issues += len(issues)
        else:
            print(f"OK: {path}")

    if total_issues:
        print(f"\n{total_issues} issue(s) found.", file=sys.stderr)
        return 1

    print("All artifacts pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
