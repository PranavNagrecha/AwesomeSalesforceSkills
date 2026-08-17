#!/usr/bin/env python3
"""Assert a skill is reachable on BOTH retrieval surfaces, not just one.

The recurring failure this guards against: a package is authored, reads well,
passes `validate_repo.py`, and is still unreachable — because the two surfaces
that find it are fed by two different fields and only one of them was filled in.

    Surface 1  the shipped gloss roster   fed by  `description`  (frontmatter)
    Surface 2  the local lexical index    fed by  `triggers:`    (frontmatter)

Surface 1 is the one that ships. `vector_index/` is gitignored, so a normal
install has no FTS5 database and no embeddings; Claude reads
`.claude/skills/salesforce-<domain>/references/skill-index.md` and picks from
one-line glosses built by `build_plugin.build_gloss()` from the description
alone — never from the body, and clipped to 220 characters with the lead paid
LAST. A term added to the lead is exactly the term that gets clipped, silently.

Surface 2 is optional and local. `pipelines/sync_engine` appends the `triggers:`
array to the indexed document as a `## Trigger Scenarios` chunk, which FTS5 then
indexes. It only exists after `python3 scripts/build_index.py`, so this script
SKIPS surface 2 rather than failing when the index is absent — an install
without one is a supported state, not a broken one.

    python3 scripts/check_routing_acceptance.py
    python3 scripts/check_routing_acceptance.py --fixture evals/routing-acceptance.json
    python3 scripts/check_routing_acceptance.py --skill admin/sharing-rules
    python3 scripts/check_routing_acceptance.py --json

Exit 1 if any assertion fails, so it can gate a wave.

Fixture shape (`evals/routing-acceptance.json`):

    {"cases": [
      {"skill": "admin/sharing-rules",
       "must_carry": ["sharing rule", "criteria-based"],
       "probes": ["criteria based sharing rule setup", "owner based sharing rule"],
       "top_n": 3}
    ]}

`must_carry` is checked against the CLIPPED gloss, not the raw description —
that is the whole point. `probes` are natural-language phrasings a practitioner
would type; each must return `skill` within `top_n`.

Stdlib only, apart from the repo's own modules.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_plugin as bp  # noqa: E402

DEFAULT_FIXTURE = ROOT / "evals" / "routing-acceptance.json"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _load_frontmatter(skill_id: str) -> dict:
    path = ROOT / "skills" / skill_id / "SKILL.md"
    if not path.is_file():
        raise FileNotFoundError(f"no SKILL.md for {skill_id}")
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{skill_id}: unparseable frontmatter")
    import yaml  # deferred: repo tooling already depends on it

    return yaml.safe_load(match.group(1)) or {}


def check_gloss(skill_id: str, must_carry: list[str]) -> tuple[list[str], str]:
    """Return (failures, gloss). A term is only 'carried' if it survives the clip."""
    fm = _load_frontmatter(skill_id)
    description = fm.get("description", "") or ""
    gloss = bp.build_gloss(description)
    low = gloss.lower()
    failures = [t for t in must_carry if t.lower() not in low]
    return failures, gloss


def check_triggers(skill_id: str, minimum: int) -> list[str]:
    fm = _load_frontmatter(skill_id)
    triggers = fm.get("triggers") or []
    problems = []
    if len(triggers) < minimum:
        problems.append(f"only {len(triggers)} triggers, expected >= {minimum} (surface 2 is fed by this array)")
    placeholders = [t for t in triggers if "TODO" in str(t)]
    if placeholders:
        problems.append(f"{len(placeholders)} trigger(s) still hold TODO text")
    return problems


def index_available() -> bool:
    return (ROOT / "vector_index" / "lexical.sqlite").is_file()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--skill", action="append", help="Restrict to one skill id; repeatable.")
    parser.add_argument("--min-triggers", type=int, default=6)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    if not fixture_path.is_file():
        print(f"fixture not found: {fixture_path}", file=sys.stderr)
        return 1
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))["cases"]
    if args.skill:
        wanted = set(args.skill)
        cases = [c for c in cases if c["skill"] in wanted]
    if not cases:
        print("no cases selected", file=sys.stderr)
        return 1

    have_index = index_available()
    ctx = None
    if have_index:
        import scripts.search_knowledge as sk  # noqa: E402

        ctx = sk.build_search_context(ROOT)

    results = []
    failed = 0
    for case in cases:
        skill_id = case["skill"]
        row: dict = {"skill": skill_id, "gloss_failures": [], "trigger_problems": [], "probe_failures": []}

        row["gloss_failures"], row["gloss"] = check_gloss(skill_id, case.get("must_carry", []))
        row["gloss_len"] = len(row["gloss"])
        row["trigger_problems"] = check_triggers(skill_id, args.min_triggers)

        if have_index:
            import scripts.search_knowledge as sk

            top_n = case.get("top_n", 3)
            for probe in case.get("probes", []):
                payload = sk.run_search(probe, ctx, domain=None)
                ids = [s["id"] for s in payload.get("skills", [])]
                if skill_id not in ids[:top_n]:
                    row["probe_failures"].append({"probe": probe, "got": ids[:top_n]})

        bad = bool(row["gloss_failures"] or row["trigger_problems"] or row["probe_failures"])
        failed += bad
        row["ok"] = not bad
        results.append(row)

    if args.json:
        print(json.dumps({"index_available": have_index, "results": results}, indent=1))
        return 1 if failed else 0

    print(f"Routing acceptance — {len(cases)} skill(s)")
    print(f"  surface 1 (shipped gloss roster): checked")
    print(f"  surface 2 (local lexical index):  {'checked' if have_index else 'SKIPPED — no vector_index/lexical.sqlite; run scripts/build_index.py to include it'}")
    print()
    for row in results:
        mark = "OK  " if row["ok"] else "FAIL"
        print(f"[{mark}] {row['skill']}  (gloss {row['gloss_len']} ch)")
        for term in row["gloss_failures"]:
            print(f"         gloss is missing {term!r} — move it into the 'Trigger keywords:' segment,")
            print(f"         which build_gloss pays FIRST; the lead is paid last and clips.")
        for problem in row["trigger_problems"]:
            print(f"         triggers: {problem}")
        for pf in row["probe_failures"]:
            print(f"         probe {pf['probe']!r} did not return it in top-N; got {pf['got']}")
    print()
    print(f"{len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
