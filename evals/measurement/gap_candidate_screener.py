#!/usr/bin/env python3
"""Bulk-screen gap candidates against the lexical index before authoring.

Reads a JSON list of candidate skill slugs + topic keywords. For each, runs
the keyword query through the in-process search engine and reports:
- DUPLICATE: top-1 score >= 3.0 — high-confidence existing coverage
- ADJACENT:  top-1 score in [1.5, 3.0) — partial coverage, may need scope
- GAP:       top-1 score < 1.5 OR no result — likely real gap

Use to triage a backlog of proposed skills WITHOUT calling new_skill.py
(which is interactive and slower).

Usage:
    python3 evals/measurement/gap_candidate_screener.py \\
        --candidates evals/measurement/gap_candidates.json \\
        --out evals/measurement/gap_screening_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import search_knowledge  # noqa: E402

CTX = search_knowledge.build_search_context(REPO)


def screen(candidates: list[dict]) -> list[dict]:
    out = []
    for c in candidates:
        topic = c["topic_keywords"]
        r = search_knowledge.run_search(topic, CTX)
        skills = r.get("skills") or []
        top1 = skills[0]["id"] if skills else ""
        top1_score = round(skills[0]["score"], 2) if skills else 0
        if top1_score >= 3.0:
            verdict = "DUPLICATE"
        elif top1_score >= 1.5:
            verdict = "ADJACENT"
        else:
            verdict = "GAP"
        out.append({
            **c,
            "verdict": verdict,
            "top1": top1,
            "top1_score": top1_score,
            "top3": [s["id"] for s in skills[:3]],
        })
    return out


def write_report(results: list[dict], path: Path):
    by_verdict = {"DUPLICATE": [], "ADJACENT": [], "GAP": []}
    for r in results:
        by_verdict[r["verdict"]].append(r)
    md = ["# Gap-candidate screening report\n"]
    md.append(f"- candidates screened: **{len(results)}**")
    md.append(f"- DUPLICATE (skip — coverage exists): **{len(by_verdict['DUPLICATE'])}**")
    md.append(f"- ADJACENT (partial coverage — may need scope rewrite): **{len(by_verdict['ADJACENT'])}**")
    md.append(f"- GAP (likely real, ready to scaffold): **{len(by_verdict['GAP'])}**")
    md.append("")
    for verdict in ("GAP", "ADJACENT", "DUPLICATE"):
        md.append(f"## {verdict} — {len(by_verdict[verdict])} candidates\n")
        for r in by_verdict[verdict]:
            md.append(f"- **`{r['proposed_slug']}`**")
            md.append(f"  - probe keywords: {r['topic_keywords']!r}")
            md.append(f"  - top-1: `{r['top1']}` (score {r['top1_score']})")
            md.append("")
    path.write_text("\n".join(md))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    cands = json.loads(Path(args.candidates).read_text())
    results = screen(cands)
    write_report(results, Path(args.out))

    counts = {"DUPLICATE": 0, "ADJACENT": 0, "GAP": 0}
    for r in results:
        counts[r["verdict"]] += 1
    print(f"DUPLICATE={counts['DUPLICATE']}  ADJACENT={counts['ADJACENT']}  GAP={counts['GAP']}", file=sys.stderr)
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
