#!/usr/bin/env python3
"""Score the SHIPPED model-driven routing path (router gloss → roster pick).

Unlike ``run_heldout.py``, this harness does NOT use ``vector_index/`` — that
directory is gitignored and does not ship. On a fresh install Claude reads:

  1. The 11 ``.claude/skills/salesforce-*/SKILL.md`` router descriptions
  2. The chosen router's ``references/skill-index.md`` roster glosses

Live re-routing requires an LLM agent (see ``README-model-routing.md`` and the
``sfskills-model-routing-benchmark`` workflow). This script scores *saved*
routing runs, validates benchmark labels, and applies documented relabels.

Usage:
  python3 evals/measurement/run_model_routing.py --check
  python3 evals/measurement/run_model_routing.py \\
      --results .overhaul-2026-08/research/routing-benchmark-routed.json
  python3 evals/measurement/run_model_routing.py --apply-relabels --dry-run
  python3 evals/measurement/run_model_routing.py --apply-relabels
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUERIES = ROOT / "evals/measurement/heldout-queries.json"
DEFAULT_RESULTS = ROOT / ".overhaul-2026-08/research/routing-benchmark-routed.json"
DEFAULT_RELABELS = ROOT / ".overhaul-2026-08/research/routing-relabels.json"
DEFAULT_DEFECTS = ROOT / ".overhaul-2026-08/research/routing-benchmark-defects.json"

# Query -> new expected_skill extracted from routing-relabels.json concrete_fix
# (only rows where label_is_wrong and a relabel is the primary fix).
RELABEL_MAP: dict[str, str] = {
    "manage picklist values": "admin/picklist-and-value-sets",
    "the org is a mess where do I start": "architect/technical-debt-assessment",
    "how do I decide between platform events and change data capture": (
        "integration/event-driven-architecture-patterns"
    ),
    "our deployment keeps failing on test coverage": "devops/deployment-error-troubleshooting",
    "integrate with an external rest api": "apex/callouts-and-http-integrations",
    "write apex unit tests": "apex/test-class-standards",
    "when do I need a queueable instead of a future method": "apex/async-apex",
    "notify an outside system the moment a record changes": (
        "integration/outbound-webhook-from-salesforce"
    ),
    "one page layout per record type is unmanageable": "admin/dynamic-forms-migration",
    "encrypt sensitive fields": "security/platform-encryption",
    "handle retries when a callout fails": "apex/apex-callout-retry-and-resilience",
    "post a message into slack when a deal closes": "flow/flow-for-slack",
    "planning a multi org consolidation": "architect/migration-architecture-patterns",
    "move changes from sandbox to production safely": "devops/pre-deployment-checklist",
    "make a field required only for one record type": "admin/validation-rules",
    "write a test that actually catches bulk problems": "apex/test-class-standards",
    "keep an external system and Salesforce in sync both ways": (
        "integration/real-time-vs-batch-integration"
    ),
    "expose Salesforce data to an external app securely": "integration/rest-api-patterns",
    "pick between mulesoft and point to point callouts": (
        "integration/middleware-integration-patterns"
    ),
    "set up CI for a Salesforce project": "devops/github-actions-for-salesforce",
}


def load_json(path: Path) -> list | dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def skill_exists(skill_id: str) -> bool:
    domain, slug = skill_id.split("/", 1)
    return (ROOT / "skills" / domain / slug / "SKILL.md").is_file()


def missing_labels(entries: list[dict], key: str = "expected_skill") -> list[str]:
    missing: list[str] = []
    for entry in entries:
        skill_id = entry.get(key) or entry.get("expected", "")
        if skill_id and not skill_exists(skill_id):
            missing.append(skill_id)
    return sorted(set(missing))


def score_results(results: list[dict]) -> dict:
    n = len(results) or 1
    hit1 = sum(1 for r in results if r.get("correct"))
    hit3 = sum(1 for r in results if r.get("correct") or r.get("expected_in_top3"))
    router_ok = sum(1 for r in results if r.get("router_correct"))
    misses = [r for r in results if not r.get("correct")]
    by_reason: dict[str, int] = {}
    for r in misses:
        reason = r.get("miss_reason") or "UNKNOWN"
        by_reason[reason] = by_reason.get(reason, 0) + 1
    return {
        "n": len(results),
        "hit_at_1": hit1 / n,
        "hit_at_3": hit3 / n,
        "router_correct_rate": router_ok / n,
        "misses_count": len(misses),
        "misses_by_reason": dict(sorted(by_reason.items(), key=lambda kv: -kv[1])),
        "misses": [
            {
                "query": r["query"],
                "expected": r.get("expected"),
                "picked": r.get("skill_picked"),
                "reason": r.get("miss_reason"),
            }
            for r in misses
        ],
    }


def check_relabels_applied(queries: list[dict]) -> list[str]:
    """Return queries where heldout label still differs from RELABEL_MAP."""
    by_query = {e["query"]: e for e in queries}
    pending: list[str] = []
    for query, new_skill in RELABEL_MAP.items():
        entry = by_query.get(query)
        if entry is None:
            pending.append(f"missing query in heldout: {query!r}")
        elif entry["expected_skill"] != new_skill:
            pending.append(
                f"{query!r}: have {entry['expected_skill']}, want {new_skill}"
            )
    return pending


def apply_relabels(queries_path: Path, dry_run: bool) -> tuple[int, list[str]]:
    data = load_json(queries_path)
    if not isinstance(data, dict) or "queries" not in data:
        print(f"FAIL: {queries_path} is not a benchmark envelope", file=sys.stderr)
        return 1, []

    changed: list[str] = []
    by_query = {e["query"]: e for e in data["queries"]}
    for query, new_skill in RELABEL_MAP.items():
        entry = by_query.get(query)
        if entry is None:
            print(f"WARN: query not in heldout: {query!r}", file=sys.stderr)
            continue
        if entry["expected_skill"] == new_skill:
            continue
        if not skill_exists(new_skill):
            print(f"FAIL: relabel target missing: {new_skill}", file=sys.stderr)
            return 2, []
        old = entry["expected_skill"]
        entry["expected_skill"] = new_skill
        entry["domain"] = new_skill.split("/")[0]
        changed.append(f"{query!r}: {old} -> {new_skill}")

    if changed and not dry_run:
        data["updated"] = "2026-08-14"
        with queries_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    return 0, changed


def rescore_with_relabels(results: list[dict]) -> dict:
    """Re-score a saved run as if benchmark relabels had been applied."""
    adjusted = []
    for r in results:
        row = dict(r)
        new_expected = RELABEL_MAP.get(row["query"])
        if new_expected:
            row["expected"] = new_expected
            row["correct"] = row.get("skill_picked") == new_expected
            picked = row.get("skill_picked", "")
            if row["correct"]:
                row["expected_in_top3"] = True
            elif picked and new_expected in picked:
                row["expected_in_top3"] = True
        adjusted.append(row)
    out = score_results(adjusted)
    out["note"] = "re-scored with RELABEL_MAP applied to expected labels"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--queries", default=str(DEFAULT_QUERIES))
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--relabels", default=str(DEFAULT_RELABELS))
    parser.add_argument("--defects", default=str(DEFAULT_DEFECTS))
    parser.add_argument("--check", action="store_true", help="Validate files and relabel status only")
    parser.add_argument("--apply-relabels", action="store_true", help="Write RELABEL_MAP into heldout-queries.json")
    parser.add_argument("--dry-run", action="store_true", help="With --apply-relabels, print changes only")
    parser.add_argument("--rescore-relabels", action="store_true", help="Re-score saved run with relabels applied")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--min-hit1", type=float)
    parser.add_argument("--min-hit3", type=float)
    args = parser.parse_args()

    queries_path = Path(args.queries)
    if not queries_path.is_absolute():
        queries_path = (ROOT / queries_path).resolve()

    queries_data = load_json(queries_path)
    queries = queries_data["queries"] if isinstance(queries_data, dict) else queries_data

    missing = missing_labels(queries)
    if missing:
        print(f"FAIL: {len(missing)} heldout label(s) missing on disk:", file=sys.stderr)
        for skill_id in missing:
            print(f"  {skill_id}", file=sys.stderr)
        return 2

    if args.apply_relabels:
        code, changed = apply_relabels(queries_path, dry_run=args.dry_run)
        if code:
            return code
        prefix = "Would apply" if args.dry_run else "Applied"
        print(f"{prefix} {len(changed)} relabel(s):")
        for line in changed:
            print(f"  {line}")
        if not changed:
            print("No relabels pending.")
        return 0

    pending = check_relabels_applied(queries)
    if args.check:
        problems: list[str] = []
        if len(queries) < 120:
            problems.append(f"only {len(queries)} queries, need >= 120")
        if pending:
            problems.append(f"{len(pending)} benchmark relabel(s) not yet applied")
        results_path = Path(args.results)
        if not results_path.is_absolute():
            results_path = (ROOT / results_path).resolve()
        if not results_path.exists():
            problems.append(f"no saved routing results at {results_path}")
        else:
            results = load_json(results_path)
            if len(results) != len(queries):
                problems.append(
                    f"results count {len(results)} != queries count {len(queries)}"
                )
        if problems:
            print(f"CHECK: {len(problems)} issue(s):", file=sys.stderr)
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            if pending:
                print("\nPending relabels:", file=sys.stderr)
                for p in pending[:10]:
                    print(f"  {p}", file=sys.stderr)
            return 1
        print(
            f"OK: {len(queries)} queries, all labels resolve, "
            f"{len(RELABEL_MAP)} documented relabels applied."
        )
        return 0

    results_path = Path(args.results)
    if not results_path.is_absolute():
        results_path = (ROOT / results_path).resolve()
    if not results_path.exists():
        print(f"FAIL: no results file at {results_path}", file=sys.stderr)
        print("Run the sfskills-model-routing-benchmark workflow to produce one.", file=sys.stderr)
        return 1

    results = load_json(results_path)
    if args.rescore_relabels:
        result = rescore_with_relabels(results)
    else:
        result = score_results(results)
    result["results_file"] = str(
        results_path.relative_to(ROOT) if results_path.is_relative_to(ROOT) else results_path
    )
    result["relabels_pending"] = len(pending)

    breaches: list[str] = []
    if args.min_hit1 is not None and result["hit_at_1"] < args.min_hit1:
        breaches.append(f"Hit@1 {result['hit_at_1']:.4f} < floor {args.min_hit1}")
    if args.min_hit3 is not None and result["hit_at_3"] < args.min_hit3:
        breaches.append(f"Hit@3 {result['hit_at_3']:.4f} < floor {args.min_hit3}")
    result["breaches"] = breaches

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        mode = "re-scored (relabels applied)" if args.rescore_relabels else "raw saved run"
        print(f"Model routing benchmark ({mode}): {result['results_file']}")
        print(f"  n              : {result['n']}")
        print(f"  Hit@1          : {result['hit_at_1']:.1%}")
        print(f"  Hit@3          : {result['hit_at_3']:.1%}")
        print(f"  Router correct : {result['router_correct_rate']:.1%}")
        print(f"  Misses         : {result['misses_count']}")
        if result["misses_by_reason"]:
            print(f"  By reason      : {result['misses_by_reason']}")
        if pending and not args.rescore_relabels:
            print(f"  Relabels pending: {len(pending)} (use --rescore-relabels to estimate post-fix)")
        if result["misses"]:
            print("\n  --- misses ---")
            for miss in result["misses"][:20]:
                print(
                    f"  {miss['query'][:58]:<58} "
                    f"want {miss['expected']}  got {miss['picked']}  ({miss['reason']})"
                )
            if len(result["misses"]) > 20:
                print(f"  ... and {len(result['misses']) - 20} more")

    for breach in breaches:
        print(f"FAIL: {breach}", file=sys.stderr)
    return 1 if breaches else 0


if __name__ == "__main__":
    sys.exit(main())
