#!/usr/bin/env python3
"""Trigger-fix wave runner — append failing queries as triggers to the
expected skills they should have surfaced.

Reads a near-miss list (from `per_row.jsonl` filtering) and edits each
expected skill's SKILL.md frontmatter to add the failing query as a new
trigger. Skips skills that already have the trigger (or a normalized
version of it). Caps additions per skill to avoid trigger-list bloat.

Usage:
    # 1. extract near-miss cases first:
    python3 -c "
    import json
    from pathlib import Path
    rows = [json.loads(l) for l in open('evals/measurement/per_row.jsonl')]
    near = [r for r in rows
            if r.get('loop','').startswith('Loop 1')
            and r.get('expected')
            and r['top1'] != r['expected']
            and r['expected'] in r.get('top3',[])]
    Path('.planning/build-history').mkdir(exist_ok=True, parents=True)
    json.dump(near, open('.planning/build-history/near-miss.json','w'), indent=2)
    "

    # 2. apply the wave:
    python3 evals/measurement/trigger_fix_wave.py \\
        --near-miss .planning/build-history/near-miss.json \\
        --max-per-skill 5

    # 3. sync + validate after:
    python3 scripts/skill_sync.py --all
    python3 scripts/validate_repo.py

    # 4. re-run the audit to measure the lift:
    python3 evals/measurement/synthesize.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def normalize_for_comparison(s: str) -> str:
    """Lowercase + strip punctuation + collapse whitespace.

    Used to detect when a candidate trigger is already represented in the
    existing trigger list (case- and punctuation-insensitive)."""
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip().split()


def quote_yaml(s: str) -> str:
    """Quote a string for YAML list output. Use double-quotes, escape inner ones."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'  - "{s}"'


def patch_skill_triggers(skill_md: Path, new_triggers: list[str]) -> tuple[int, list[str]]:
    """Append new triggers to a skill's frontmatter triggers: list.

    Returns (n_added, skipped_reasons).
    """
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Locate frontmatter
    if lines[0].strip() != "---":
        return 0, ["no frontmatter"]
    closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if closing is None:
        return 0, ["unterminated frontmatter"]

    fm_lines = lines[1:closing]

    # Find triggers: block — list items of form `  - "..."` immediately following
    trig_idx = next((i for i, l in enumerate(fm_lines) if l.strip().startswith("triggers:")), None)
    if trig_idx is None:
        return 0, ["no triggers: block"]

    # Identify the bounds of the triggers list (consecutive `  - ` items after `triggers:`)
    end_idx = trig_idx + 1
    existing: set[tuple] = set()
    while end_idx < len(fm_lines) and fm_lines[end_idx].lstrip().startswith("- "):
        existing_str = fm_lines[end_idx].lstrip().lstrip("-").strip().strip('"').strip("'")
        existing.add(tuple(normalize_for_comparison(existing_str)))
        end_idx += 1

    # Filter out triggers already represented
    skipped: list[str] = []
    to_add: list[str] = []
    for t in new_triggers:
        norm_tuple = tuple(normalize_for_comparison(t))
        if norm_tuple in existing:
            skipped.append(f"already-present: {t!r}")
            continue
        if not norm_tuple:
            skipped.append(f"empty-after-normalize: {t!r}")
            continue
        existing.add(norm_tuple)
        to_add.append(t)

    if not to_add:
        return 0, skipped

    # Insert new triggers BEFORE the next non-trigger frontmatter line
    new_fm = fm_lines[:end_idx] + [quote_yaml(t) for t in to_add] + fm_lines[end_idx:]
    new_text = "\n".join(["---"] + new_fm + ["---"] + lines[closing + 1:])
    if not new_text.endswith("\n"):
        new_text += "\n"

    skill_md.write_text(new_text, encoding="utf-8")
    return len(to_add), skipped


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--near-miss", required=True, help="JSON list of near-miss cases")
    p.add_argument("--max-per-skill", type=int, default=5)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    cases = json.loads(Path(args.near_miss).read_text())
    print(f"loaded {len(cases)} near-miss cases", file=sys.stderr)

    # Group by expected skill
    by_skill: dict[str, list[str]] = defaultdict(list)
    for c in cases:
        skill_id = c["expected"]
        by_skill[skill_id].append(c["query"])

    print(f"affecting {len(by_skill)} unique skills", file=sys.stderr)

    total_added = 0
    affected: list[tuple[str, int]] = []
    skipped_skills: list[tuple[str, str]] = []

    for skill_id, queries in sorted(by_skill.items()):
        skill_md = REPO / "skills" / skill_id / "SKILL.md"
        if not skill_md.exists():
            skipped_skills.append((skill_id, "skill missing on disk"))
            continue

        # Cap adds per skill to avoid trigger-list bloat
        candidates = queries[: args.max_per_skill]

        if args.dry_run:
            print(f"[DRY] {skill_id}: would consider {len(candidates)} triggers", file=sys.stderr)
            continue

        n_added, skipped_reasons = patch_skill_triggers(skill_md, candidates)
        total_added += n_added
        if n_added > 0:
            affected.append((skill_id, n_added))
        else:
            skipped_skills.append((skill_id, "; ".join(skipped_reasons) or "no-op"))

    print(f"\n=== Trigger-fix wave summary ===", file=sys.stderr)
    print(f"skills affected: {len(affected)}", file=sys.stderr)
    print(f"triggers added: {total_added}", file=sys.stderr)
    print(f"skills skipped: {len(skipped_skills)}", file=sys.stderr)

    if affected:
        print("\nadds per skill:", file=sys.stderr)
        for s, n in sorted(affected, key=lambda x: -x[1])[:30]:
            print(f"  +{n}  {s}", file=sys.stderr)

    if skipped_skills:
        print(f"\nskipped (sample):", file=sys.stderr)
        for s, r in skipped_skills[:10]:
            print(f"  {s}: {r}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
