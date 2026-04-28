#!/usr/bin/env python3
"""
check_data_loader_batch_window_sizing.py

Pre-load sizing recommender for Data Loader / Bulk API V1 / Bulk API V2 /
Batch Apex jobs. Given an SObject name, record count, and a small set of
complexity flags, prints a recommended batch size, mode (parallel/serial),
API choice, and an estimated runtime range.

Implements the Decision Guidance table in
skills/data/data-loader-batch-window-sizing/SKILL.md.

stdlib only. Exit codes:
  0  recommendation produced and inputs look healthy
  1  recommendation produced BUT one or more high-risk warnings raised
     (row-skew, no External Id on >1M parent-child load, missing trigger
     bypass on one-time historical, etc.)
  2  invalid inputs (bad CLI usage)

Usage examples:
  python3 check_data_loader_batch_window_sizing.py \\
      --object Account --records 5000000 \\
      --owd private --hierarchy-depth 5 --triggers 6 \\
      --row-skew --one-time-historical

  python3 check_data_loader_batch_window_sizing.py \\
      --object Lead --records 250000 --owd public-rw --triggers 0

  python3 check_data_loader_batch_window_sizing.py \\
      --object Opportunity --records 1200000 --owd private \\
      --territories --triggers 4 --parent-child --no-external-id

  python3 check_data_loader_batch_window_sizing.py --json \\
      --object Case --records 800000 --owd public-rw \\
      --field-history-on-touched-fields
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Inputs / arg parsing
# ---------------------------------------------------------------------------

OWD_CHOICES = ("public-rw", "public-ro", "private")
API_CHOICES = ("bulk-v2", "bulk-v1", "rest-composite", "batch-apex")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recommend batch size, mode, and runtime for a Salesforce "
            "high-volume load. Prints the recommendation and any warnings."
        ),
    )
    parser.add_argument("--object", required=True, help="Target SObject API name (e.g., Account).")
    parser.add_argument("--records", type=int, required=True, help="Total record count for this load.")
    parser.add_argument(
        "--owd",
        choices=OWD_CHOICES,
        default="public-rw",
        help="Org-Wide Default for the target SObject. Default: public-rw.",
    )
    parser.add_argument(
        "--hierarchy-depth",
        type=int,
        default=0,
        help="Role-hierarchy depth above the load user (0 = none, 6+ = deep).",
    )
    parser.add_argument(
        "--sharing-rules",
        type=int,
        default=0,
        help="Number of active sharing rules on the target SObject.",
    )
    parser.add_argument(
        "--triggers",
        type=int,
        default=0,
        help="Count of Apex triggers + record-triggered Flows on the target SObject.",
    )
    parser.add_argument(
        "--validation-rules",
        type=int,
        default=0,
        help="Count of active validation rules.",
    )
    parser.add_argument(
        "--territories",
        action="store_true",
        help="Territory Management 2.0 active on this SObject (forces serial).",
    )
    parser.add_argument(
        "--row-skew",
        action="store_true",
        help="A single parent or owner has >10K children pointing at it.",
    )
    parser.add_argument(
        "--parent-child",
        action="store_true",
        help="Load is part of a parent-child mass migration.",
    )
    parser.add_argument(
        "--no-external-id",
        action="store_true",
        help="Parent-child load is NOT using External Id deferred linkage (warning).",
    )
    parser.add_argument(
        "--one-time-historical",
        action="store_true",
        help="One-time historical replay (recommend trigger bypass).",
    )
    parser.add_argument(
        "--field-history-on-touched-fields",
        action="store_true",
        help="Field history tracking is enabled on fields the load will modify.",
    )
    parser.add_argument(
        "--api-budget-remaining",
        type=int,
        default=None,
        help="Remaining daily API call budget (used to warn on budget exhaustion).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human text.",
    )
    args = parser.parse_args(argv)

    if args.records <= 0:
        parser.error("--records must be a positive integer")
    if args.hierarchy_depth < 0:
        parser.error("--hierarchy-depth cannot be negative")
    if args.triggers < 0 or args.sharing_rules < 0 or args.validation_rules < 0:
        parser.error("counts cannot be negative")

    return args


# ---------------------------------------------------------------------------
# Recommendation engine
# ---------------------------------------------------------------------------


def recommend_batch_size(args: argparse.Namespace) -> Tuple[int, str]:
    """Return (batch_size, reasoning) per the Decision Guidance table."""
    # Strongest signals first — territories and row-skew force the smallest
    # batch regardless of volume, because their failure modes are structural.
    if args.territories:
        return 200, "Territory Management 2.0 active — small batches reduce territory-rule lock contention"
    if args.row_skew:
        return 200, "row-skewed parent/owner detected — small batches contain lock contention"
    if args.owd == "private" and args.hierarchy_depth >= 3 and args.records > 100_000:
        return 200, "Private OWD + role hierarchy + >100K records — small batches reduce implicit-share fan-out cost"

    # Trigger / Flow load is the next strongest signal. The 200-row server
    # transaction is the trigger-CPU planning unit even on Bulk V2.
    automation_load = args.triggers + max(args.validation_rules - 2, 0)
    if automation_load >= 8:
        return 200, "very rich automation (>=8 triggers/Flows + many validation rules) — batch=200 keeps per-batch CPU under 60s sync limit"
    if automation_load >= 4:
        if args.records >= 1_000_000:
            return 500, "moderate automation + 1M+ records — batch=500 balances trigger CPU envelope vs API call count"
        return 1_000, "moderate automation, mid-volume — batch=1000 acceptable trigger-CPU/API-call tradeoff"

    # Simple, low-automation, larger-batch path
    if args.records < 10_000:
        return 2_000, "small volume + simple object — large batches save API calls without CPU risk"
    if args.records < 1_000_000:
        return 2_000, "mid volume + simple object — batch=2000 balances throughput and overhead"
    return 5_000, "large volume + simple object + Public R/W OWD — batch=5000 maximises throughput safely"


def recommend_mode(args: argparse.Namespace) -> Tuple[str, str]:
    """Return (mode, reasoning)."""
    if args.territories:
        return "serial", "Territory Management 2.0 mandates serial mode (parallel produces territory-rule lock contention)"
    if args.row_skew:
        return "serial", "row-skew shape will produce UNABLE_TO_LOCK_ROW under parallel mode"
    if args.owd == "private" and (args.hierarchy_depth >= 3 or args.sharing_rules > 0):
        return "serial", "Private OWD + (deep hierarchy or sharing rules) — serial avoids implicit-share lock contention"
    return "parallel", "no row-skew, no territory mgmt, no Private OWD with sharing — parallel is safe and faster"


def recommend_api(args: argparse.Namespace) -> Tuple[str, str]:
    """Return (api, reasoning)."""
    if args.records < 5_000:
        return "rest-composite", "small volume — REST Composite (200/request) is acceptable"
    if args.records < 100_000:
        return "bulk-v2", "mid volume — Bulk API V2 is the canonical choice (Bulk V1 via Data Loader UI is also fine)"
    return "bulk-v2", "large volume (>100K) — Bulk API V2 is the only correct choice; do NOT use REST Composite"


def estimate_runtime_minutes(
    record_count: int, batch_size: int, mode: str, automation_load: int
) -> Tuple[int, int]:
    """Very rough runtime range in minutes.

    Heuristic: each 200-row server transaction takes between 1 and 5 seconds
    depending on automation_load. Parallel mode reduces wall clock by ~3x for
    safe shapes; serial mode does not. Sharing recalc tail and async work
    are NOT included here — those are reported separately.
    """
    server_chunks = max(1, record_count // 200)
    seconds_per_chunk_min = 1 + automation_load * 0.5
    seconds_per_chunk_max = 3 + automation_load * 1.5

    parallelism = 3 if mode == "parallel" else 1
    low_seconds = (server_chunks * seconds_per_chunk_min) / parallelism
    high_seconds = (server_chunks * seconds_per_chunk_max) / parallelism

    return int(low_seconds // 60), int(high_seconds // 60) + 1


def estimate_api_calls(record_count: int, batch_size: int) -> int:
    batches = max(1, record_count // batch_size + (1 if record_count % batch_size else 0))
    return batches * 2  # ~2 API calls per batch including state polls


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------


def collect_warnings(args: argparse.Namespace, recommendation: dict) -> List[str]:
    warnings: List[str] = []

    # Row-skew without serial would already be caught by the recommender, but
    # surface it explicitly so the user sees WHY the recommendation is what it is.
    if args.row_skew and recommendation["mode"] != "serial":
        warnings.append(
            "ROW-SKEW: a row-skewed parent/owner is present but recommendation is not serial — manual override; expect UNABLE_TO_LOCK_ROW"
        )

    # Private OWD + role hierarchy + no Defer Sharing Calculations plan
    if args.owd == "private" and args.hierarchy_depth >= 3 and args.records >= 100_000:
        warnings.append(
            "DEFER SHARING: Private OWD + hierarchy + >=100K records — enable Defer Sharing Calculations for the load window or expect a multi-hour async sharing-recalc tail"
        )

    # One-time historical without trigger bypass plan
    if args.one_time_historical and args.triggers >= 1:
        warnings.append(
            "TRIGGER BYPASS: one-time historical load with active triggers — design a TriggerControl__mdt bypass + post-load enrich Batch Apex pass; do NOT replay history through real-time triggers"
        )

    # Parent-child without External Id
    if args.parent_child and args.no_external_id and args.records >= 100_000:
        warnings.append(
            "EXTERNAL ID: parent-child load >=100K records without External Id deferred linkage — strict parent-first ordering is brittle on retry; add External Id"
        )

    # Field history on touched fields
    if args.field_history_on_touched_fields and args.records >= 500_000:
        warnings.append(
            "HISTORY EXPLOSION: field history tracking is enabled on fields the load will modify — temporarily disable for the load window or expect millions of immutable history rows"
        )

    # API call budget exhaustion
    if args.api_budget_remaining is not None:
        estimated = recommendation["estimated_api_calls"]
        if estimated > args.api_budget_remaining:
            warnings.append(
                f"API BUDGET: estimated {estimated:,} calls exceeds remaining quota {args.api_budget_remaining:,} — schedule load for next budget cycle or coordinate with other consumers"
            )
        elif estimated > 0.7 * args.api_budget_remaining:
            warnings.append(
                f"API BUDGET TIGHT: estimated {estimated:,} calls is >70% of remaining quota {args.api_budget_remaining:,}"
            )

    # REST Composite for >5K records (caller forced by hand)
    if args.records >= 5_000 and recommendation["api"] == "rest-composite":
        warnings.append(
            "API CHOICE: REST Composite at this volume is suboptimal — switch to Bulk API V2"
        )

    return warnings


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def build_recommendation(args: argparse.Namespace) -> dict:
    batch_size, batch_reason = recommend_batch_size(args)
    mode, mode_reason = recommend_mode(args)
    api, api_reason = recommend_api(args)
    automation_load = args.triggers + max(args.validation_rules - 2, 0)
    runtime_low, runtime_high = estimate_runtime_minutes(
        args.records, batch_size, mode, automation_load
    )
    api_calls = estimate_api_calls(args.records, batch_size)

    return {
        "object": args.object,
        "records": args.records,
        "batch_size": batch_size,
        "batch_size_reason": batch_reason,
        "mode": mode,
        "mode_reason": mode_reason,
        "api": api,
        "api_reason": api_reason,
        "estimated_runtime_minutes": [runtime_low, runtime_high],
        "estimated_api_calls": api_calls,
        "automation_load": automation_load,
    }


def render_human(rec: dict, warnings: List[str]) -> str:
    out: List[str] = []
    out.append(f"Sizing recommendation for {rec['object']} ({rec['records']:,} records)")
    out.append("=" * 70)
    out.append(f"  batch size      : {rec['batch_size']:,}")
    out.append(f"      reason      : {rec['batch_size_reason']}")
    out.append(f"  mode            : {rec['mode']}")
    out.append(f"      reason      : {rec['mode_reason']}")
    out.append(f"  API             : {rec['api']}")
    out.append(f"      reason      : {rec['api_reason']}")
    out.append(
        f"  est. runtime    : {rec['estimated_runtime_minutes'][0]}–"
        f"{rec['estimated_runtime_minutes'][1]} minutes (excludes async sharing recalc tail)"
    )
    out.append(f"  est. API calls  : {rec['estimated_api_calls']:,}")
    out.append("")

    if warnings:
        out.append(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            out.append(f"  - {w}")
    else:
        out.append("No high-risk warnings.")
    out.append("")
    out.append("See skills/data/data-loader-batch-window-sizing/SKILL.md for the full Decision Guidance table.")
    return "\n".join(out)


def main(argv: List[str]) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        # argparse exits 2 on bad usage already
        return int(exc.code) if exc.code is not None else 2

    rec = build_recommendation(args)
    warnings = collect_warnings(args, rec)

    if args.json:
        print(json.dumps({"recommendation": rec, "warnings": warnings}, indent=2))
    else:
        print(render_human(rec, warnings))

    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
