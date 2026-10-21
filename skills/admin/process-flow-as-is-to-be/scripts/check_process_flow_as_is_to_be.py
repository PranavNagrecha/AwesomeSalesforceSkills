#!/usr/bin/env python3
"""Checker for As-Is / To-Be process map JSON handoffs.

Validates a process-map JSON file produced by the
`process-flow-as-is-to-be` skill against the canonical schema.

Stdlib only.

Usage:
    python3 check_process_flow_as_is_to_be.py --map path/to/process-map.json
    python3 check_process_flow_as_is_to_be.py --manifest-dir path/to/maps [--strict]

Exit codes:
    0 — no ERROR findings (WARN findings exit 0 unless --strict; an empty
        --manifest-dir prints one WARN and exits 0)
    1 — an ERROR finding (schema break: missing key, invalid tier enum,
        unparseable JSON), a missing path, or any WARN under --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ALLOWED_TIERS = {
    "FLOW",
    "APEX",
    "APPROVAL",
    "PLATFORM_EVENT",
    "INTEGRATION",
    "MANUAL",
    "OPEN",
}

# When the tier is INTEGRATION, the handoff may suffix it with a
# colon-separated sub-tier such as INTEGRATION:REST. We accept those.
INTEGRATION_SUB_TIERS = {"REST", "BULK", "PE", "CDC", "PUBSUB", "CONNECT", "MULESOFT"}

EXCEPTION_KEYWORDS = {"timeout", "fallback", "retry", "fail", "error", "reject"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an As-Is / To-Be process-map JSON handoff.",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--map",
        dest="map_path",
        help="Path to one process-map JSON file.",
    )
    target.add_argument(
        "--manifest-dir",
        dest="manifest_dir",
        help="Directory whose *.json files (recursive) are process-map handoffs.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit 1 on any issue, including warnings).",
    )
    return parser.parse_args()


def _normalise_tier(tier: str) -> str:
    """Strip optional sub-tier qualifier (e.g. INTEGRATION:REST -> INTEGRATION)."""
    if not isinstance(tier, str):
        return ""
    return tier.split(":", 1)[0].strip().upper()


def _sub_tier(tier: str) -> str | None:
    if not isinstance(tier, str) or ":" not in tier:
        return None
    return tier.split(":", 1)[1].strip().upper()


def validate_map(data: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for the given process-map dict."""
    errors: list[str] = []
    warnings: list[str] = []

    # --- top-level shape ---------------------------------------------------
    required_top = ["process_id", "scope", "as_is_steps", "to_be_steps"]
    for key in required_top:
        if key not in data:
            errors.append(f"missing top-level key: {key}")
    if errors:
        return errors, warnings  # cannot continue without shape

    scope = data.get("scope") or {}
    declared_actors = set(scope.get("actors") or [])
    if not declared_actors:
        errors.append("scope.actors is empty — every map needs declared swim lanes")

    if not scope.get("start_trigger"):
        errors.append("scope.start_trigger is missing — every map needs an explicit start")
    if not scope.get("end_state"):
        errors.append("scope.end_state is missing — every map needs an explicit end")

    # --- actors used vs declared ------------------------------------------
    as_is_steps = data.get("as_is_steps") or []
    to_be_steps = data.get("to_be_steps") or []
    used_actors: set[str] = set()
    for step in as_is_steps + to_be_steps:
        actor = step.get("actor")
        if actor:
            used_actors.add(actor)

    undeclared = used_actors - declared_actors
    for actor in sorted(undeclared):
        errors.append(
            f"actor '{actor}' used in steps but not declared in scope.actors"
        )

    unused = declared_actors - used_actors
    for actor in sorted(unused):
        warnings.append(
            f"actor '{actor}' declared in scope.actors but never appears in any step"
        )

    # --- as_is steps -------------------------------------------------------
    if not as_is_steps:
        errors.append(
            "as_is_steps[] is empty — a To-Be without an As-Is is not a process map"
        )
    for i, step in enumerate(as_is_steps):
        sid = step.get("step_id") or f"as_is_steps[{i}]"
        if not step.get("actor"):
            errors.append(f"As-Is step {sid} has no actor")
        if not step.get("description"):
            errors.append(f"As-Is step {sid} has no description")
        if "pain_points" not in step:
            warnings.append(
                f"As-Is step {sid} has no pain_points field — explicitly mark [] if no pain"
            )

    # --- to_be steps -------------------------------------------------------
    if not to_be_steps:
        errors.append("to_be_steps[] is empty — every map needs a To-Be")

    open_steps_seen = 0
    integration_step_ids: list[str] = []
    for i, step in enumerate(to_be_steps):
        sid = step.get("step_id") or f"to_be_steps[{i}]"
        if not step.get("actor"):
            errors.append(f"To-Be step {sid} has no actor")
        if not step.get("description"):
            errors.append(f"To-Be step {sid} has no description")
        tier_raw = step.get("automation_tier")
        if not tier_raw:
            errors.append(f"To-Be step {sid} is missing automation_tier")
            continue
        base = _normalise_tier(tier_raw)
        if base not in ALLOWED_TIERS:
            errors.append(
                f"To-Be step {sid} has automation_tier '{tier_raw}' "
                f"not in enum {sorted(ALLOWED_TIERS)}"
            )
            continue
        sub = _sub_tier(tier_raw)
        if base == "INTEGRATION":
            integration_step_ids.append(sid)
            if sub and sub not in INTEGRATION_SUB_TIERS:
                warnings.append(
                    f"To-Be step {sid} uses INTEGRATION sub-tier '{sub}' "
                    f"not in known set {sorted(INTEGRATION_SUB_TIERS)}"
                )
        if base == "OPEN":
            open_steps_seen += 1
        if base != "MANUAL" and base != "OPEN":
            if not step.get("decision_tree_branch"):
                warnings.append(
                    f"To-Be step {sid} (tier={base}) has no decision_tree_branch citation"
                )
        if base != "MANUAL" and not step.get("recommended_agents"):
            warnings.append(
                f"To-Be step {sid} has no recommended_agents — downstream handoff is unclear"
            )

    if open_steps_seen and not data.get("open_questions"):
        errors.append(
            f"{open_steps_seen} step(s) tagged [OPEN] but open_questions log is empty"
        )

    # --- manual residue ----------------------------------------------------
    manual_steps_in_to_be = [
        s
        for s in to_be_steps
        if _normalise_tier(s.get("automation_tier") or "") == "MANUAL"
    ]
    manual_residue = data.get("manual_residue") or []
    residue_ids = {row.get("step_id") for row in manual_residue if row.get("step_id")}
    for step in manual_steps_in_to_be:
        sid = step.get("step_id")
        if sid and sid not in residue_ids:
            warnings.append(
                f"To-Be step {sid} is [MANUAL] but has no row in manual_residue"
            )
    for row in manual_residue:
        if not row.get("reason"):
            errors.append(
                f"manual_residue row {row.get('step_id')} is missing 'reason' "
                "(allowed: judgement / regulatory / low_volume / high_change_cost)"
            )

    # --- exception paths ---------------------------------------------------
    exception_paths = data.get("exception_paths") or []
    for ex in exception_paths:
        did = ex.get("decision_id") or "<unknown>"
        branches = ex.get("branches") or []
        if len(branches) < 2:
            errors.append(
                f"decision '{did}' has fewer than 2 outgoing branches "
                "(every decision diamond needs a Yes / No or multi-way split)"
            )
        for b in branches:
            if not b.get("condition"):
                errors.append(
                    f"decision '{did}' has a branch with no 'condition' label"
                )
            if not b.get("next_step"):
                warnings.append(
                    f"decision '{did}' branch '{b.get('condition')}' has no next_step "
                    "(implicit branches are not allowed)"
                )

    # Every integration handshake must have at least one exception branch
    # whose condition reads like a fault path.
    if integration_step_ids:
        integration_decision_coverage: set[str] = set()
        for ex in exception_paths:
            for b in ex.get("branches") or []:
                cond = (b.get("condition") or "").lower()
                if any(k in cond for k in EXCEPTION_KEYWORDS):
                    integration_decision_coverage.add(ex.get("decision_id") or "")
                ns = b.get("next_step")
                if ns in integration_step_ids:
                    integration_decision_coverage.add(ex.get("decision_id") or "")
        if not integration_decision_coverage:
            warnings.append(
                "no exception_paths branch references an integration step or a "
                "fault keyword (timeout / retry / fail / fallback) — "
                "integration handshakes must have explicit sad paths"
            )

    return errors, warnings


def _check_file(map_path: Path) -> tuple[list[str], list[str]]:
    try:
        data = json.loads(map_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return [f"{map_path}: invalid JSON: {e}"], []
    if not isinstance(data, dict):
        return [f"{map_path}: top-level JSON must be an object"], []
    errors, warnings = validate_map(data)
    return [f"{map_path}: {e}" for e in errors], [f"{map_path}: {w}" for w in warnings]


def main() -> int:
    args = parse_args()
    if args.map_path:
        target = Path(args.map_path)
        if not target.is_file():
            print(f"ERROR: map file not found: {target}")
            return 1
        files = [target]
    else:
        target = Path(args.manifest_dir)
        if not target.is_dir():
            print(f"ERROR: manifest directory not found: {target}")
            return 1
        files = sorted(target.rglob("*.json"))
        if not files:
            print(f"WARN: no *.json process maps under {target}; nothing was checked.")
            return 0

    errors: list[str] = []
    warnings: list[str] = []
    for f in files:
        e, w = _check_file(f)
        errors.extend(e)
        warnings.extend(w)

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        return 1
    if warnings and args.strict:
        return 1
    if not errors and not warnings:
        print("OK: process map validates against schema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
