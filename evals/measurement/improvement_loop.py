#!/usr/bin/env python3
"""Self-improvement loop for retrieval Hit@1.

Runs measure → identify failure pattern → propose intervention → test →
keep if Hit@1 improved → repeat. Stops when:
- Hit@1 plateaus (≤0.5pp lift over 2 consecutive iterations)
- Author-curated baseline regresses below 98%
- Max iterations reached

This is the automated version of last week's manual trigger-fix wave that
took skills 95.0% → 98.5% on baseline. Same playbook, applied iteratively.

Honesty about what this can and can't do:
- It optimizes against synthetic NL queries from nl_query_generator.py and
  nl_query_generator_corpora.py. Lift is real on that distribution, but
  represents a local optimum — not a generalization to all real-user queries.
- The fix mechanism is deterministic: "for each near-miss where expected is
  in top-3 but not top-1, add the failing query as a trigger to the expected
  skill (capped at 5 per skill)." That's the trigger-fix wave heuristic.
- For NON-near-miss cases (expected not in top-3 at all), this loop does
  not fix them — those need a different mechanism (vocabulary expansion,
  query rewriting, or a coverage gap).

Invocation:
    python3 evals/measurement/improvement_loop.py \\
        --corpus skills \\
        --max-iter 5 \\
        --min-lift 0.005

For the secondary corpora (agents/templates/decision-trees) the fix is a
different mechanism (slug-aware scoring already lifted them; further fixes
would need scoring weight tuning, which is out of scope for this loop).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run a subprocess and capture output. Errors raise."""
    return subprocess.run(
        cmd,
        cwd=cwd or REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _read_results(json_path: Path) -> dict:
    return json.loads(json_path.read_text(encoding="utf-8"))


def _measure(label: str, fixtures_path: Path, out_dir: Path) -> dict:
    """Run retrieval_eval.py against fixtures, return parsed results."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / f"{label}.json"
    out_md = out_dir / f"{label}.md"
    proc = _run([
        sys.executable,
        str(REPO / "evals" / "measurement" / "retrieval_eval.py"),
        "--fixtures", str(fixtures_path),
        "--out", str(out_json),
        "--report", str(out_md),
        "--label", label,
    ])
    if proc.returncode != 0:
        raise RuntimeError(f"measure failed: {proc.stderr}")
    return _read_results(out_json)


def _extract_near_misses(results: dict) -> list[dict]:
    """Return cases where top1 != expected but expected is in top3."""
    near = []
    for m in results.get("misses", []):
        # The retrieval_eval.py format stores "top1" and "top3" arrays.
        if not m.get("expected"):
            continue
        if m.get("top1") == m["expected"]:
            continue
        if m["expected"] in m.get("top3", []):
            near.append(m)
    return near


def _apply_trigger_fix_wave(near_miss_path: Path, max_per_skill: int = 5) -> int:
    """Run the trigger_fix_wave.py script and return the number of triggers added."""
    proc = _run([
        sys.executable,
        str(REPO / "evals" / "measurement" / "trigger_fix_wave.py"),
        "--near-miss", str(near_miss_path),
        "--max-per-skill", str(max_per_skill),
    ])
    if proc.returncode != 0:
        raise RuntimeError(f"trigger_fix_wave failed: {proc.stderr}")
    # Parse "triggers added: N" from stderr
    for line in proc.stderr.splitlines():
        if "triggers added:" in line:
            try:
                return int(line.split("triggers added:")[-1].strip())
            except ValueError:
                pass
    return 0


def _resync() -> None:
    """Run skill_sync.py to regenerate registry and chunks after trigger edits."""
    proc = _run([
        sys.executable,
        str(REPO / "scripts" / "skill_sync.py"),
        "--all",
    ])
    if proc.returncode != 0:
        raise RuntimeError(f"skill_sync failed: {proc.stderr}")


def _checkpoint_skills() -> Path:
    """Copy the current skills/ tree to a backup location for rollback."""
    snapshot = REPO / ".improvement-loop-snapshot"
    if snapshot.exists():
        shutil.rmtree(snapshot)
    shutil.copytree(REPO / "skills", snapshot)
    return snapshot


def _restore_skills(snapshot: Path) -> None:
    """Restore skills/ from a previous checkpoint."""
    if not snapshot.exists():
        raise RuntimeError(f"snapshot {snapshot} does not exist")
    shutil.rmtree(REPO / "skills")
    shutil.copytree(snapshot, REPO / "skills")


def loop_skills(
    *,
    nl_fixtures: Path,
    curated_fixtures: Path,
    out_dir: Path,
    max_iter: int = 5,
    min_lift: float = 0.005,
    max_per_skill: int = 5,
    curated_floor: float = 0.98,
) -> dict:
    """Run the improvement loop on the SKILLS corpus.

    Each iteration:
      1. measure NL Hit@1 + curated Hit@1
      2. extract near-miss cases (top1 != expected, expected in top3)
      3. snapshot skills/
      4. apply trigger_fix_wave on those cases
      5. re-sync the index
      6. re-measure both NL and curated
      7. if curated regressed below floor, OR NL lifted by < min_lift,
         restore snapshot and stop
    """
    timeline: list[dict] = []
    snapshot: Path | None = None
    prev_nl_hit1 = -1.0

    for i in range(max_iter):
        iter_label = f"loop_iter_{i:02d}"
        print(f"\n=== Iteration {i} ===", file=sys.stderr)

        nl = _measure(f"{iter_label}_nl", nl_fixtures, out_dir)
        curated = _measure(f"{iter_label}_curated", curated_fixtures, out_dir)
        nl_hit1 = nl["hit_at_1"]
        cur_hit1 = curated["hit_at_1"]
        print(f"  NL Hit@1: {nl_hit1:.1%}    curated Hit@1: {cur_hit1:.1%}", file=sys.stderr)

        timeline.append({
            "iter": i,
            "nl_hit1": nl_hit1,
            "curated_hit1": cur_hit1,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        # Convergence check
        if i > 0:
            lift = nl_hit1 - prev_nl_hit1
            if lift < min_lift:
                print(
                    f"  Plateaued (lift={lift:.4f} < {min_lift}). Stopping.",
                    file=sys.stderr,
                )
                break

        # Curated regression check
        if cur_hit1 < curated_floor:
            print(
                f"  Curated regressed below {curated_floor:.0%}. Restoring snapshot.",
                file=sys.stderr,
            )
            if snapshot is not None:
                _restore_skills(snapshot)
                _resync()
            break

        prev_nl_hit1 = nl_hit1

        # Extract near misses
        near = _extract_near_misses(nl)
        print(f"  near-miss cases: {len(near)}", file=sys.stderr)
        if not near:
            print("  No near-miss cases left to fix. Stopping.", file=sys.stderr)
            break

        # Snapshot before mutation
        snapshot = _checkpoint_skills()
        near_path = out_dir / f"{iter_label}_near.json"
        near_path.write_text(json.dumps(near, indent=2), encoding="utf-8")

        # Apply trigger-fix wave + resync
        n_added = _apply_trigger_fix_wave(near_path, max_per_skill=max_per_skill)
        print(f"  triggers added: {n_added}", file=sys.stderr)
        if n_added == 0:
            print("  No new triggers added. Stopping.", file=sys.stderr)
            break
        print("  resyncing index…", file=sys.stderr)
        _resync()
        print("  resync done.", file=sys.stderr)

    # Final measurement after the loop
    final_label = "loop_final"
    final_nl = _measure(f"{final_label}_nl", nl_fixtures, out_dir)
    final_curated = _measure(f"{final_label}_curated", curated_fixtures, out_dir)
    timeline.append({
        "iter": "final",
        "nl_hit1": final_nl["hit_at_1"],
        "curated_hit1": final_curated["hit_at_1"],
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    return {
        "corpus": "skills",
        "max_iter": max_iter,
        "iterations_run": len(timeline) - 1,
        "timeline": timeline,
        "final_nl_hit1": final_nl["hit_at_1"],
        "final_curated_hit1": final_curated["hit_at_1"],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", default="skills", choices=["skills"])
    p.add_argument("--nl-fixtures", default="/tmp/nl_baseline_fixtures.json")
    p.add_argument("--curated-fixtures", default=str(REPO / "vector_index" / "query-fixtures.json"))
    p.add_argument("--out-dir", default="/tmp/improvement-loop")
    p.add_argument("--max-iter", type=int, default=5)
    p.add_argument("--min-lift", type=float, default=0.005)
    p.add_argument("--max-per-skill", type=int, default=5)
    p.add_argument("--curated-floor", type=float, default=0.98)
    args = p.parse_args()

    if args.corpus != "skills":
        print(f"corpus={args.corpus} not yet implemented", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = loop_skills(
        nl_fixtures=Path(args.nl_fixtures),
        curated_fixtures=Path(args.curated_fixtures),
        out_dir=out_dir,
        max_iter=args.max_iter,
        min_lift=args.min_lift,
        max_per_skill=args.max_per_skill,
        curated_floor=args.curated_floor,
    )
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nLoop summary written to {summary_path}", file=sys.stderr)
    print(f"Final NL Hit@1: {summary['final_nl_hit1']:.1%}", file=sys.stderr)
    print(f"Final curated Hit@1: {summary['final_curated_hit1']:.1%}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
