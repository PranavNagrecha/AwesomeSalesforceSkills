#!/usr/bin/env python3
"""Retrieval eval harness for the SfSkills library.

Takes a JSON file of query fixtures, runs each through the in-process search
engine, and scores Hit@1 / Hit@3 / Coverage. Writes both a JSON results file
and a markdown summary.

Fixture schema (input):
    [
      {"query": "...", "expected_skill": "domain/slug", "domain": "apex"},
      ...
    ]

OR the existing format used in vector_index/query-fixtures.json:
    {"queries": [ {"query": "...", "expected_skill": "...", "domain": "...", "top_k": 3}, ... ]}

Output (JSON):
    {
      "fixture_count": 1270,
      "hit_at_1": 0.83,
      "hit_at_3": 0.91,
      "coverage_rate": 0.95,
      "by_domain": { "apex": {...}, ... },
      "misses": [ {"query": "...", "expected": "apex/x", "top1": "apex/y", ...}, ... ],
      "no_coverage": [ {"query": "..."}, ... ]
    }

Usage:
    python3 evals/measurement/retrieval_eval.py \
        --fixtures vector_index/query-fixtures.json \
        --out evals/measurement/loop1_baseline.json \
        --report evals/measurement/loop1_baseline.md \
        --label "Loop 1 (baseline, 1270 existing fixtures)"
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import search_knowledge  # noqa: E402

_CTX = None


def _ctx():
    global _CTX
    if _CTX is None:
        _CTX = search_knowledge.build_search_context(REPO_ROOT)
    return _CTX


import re as _re

_KEEP = _re.compile(r"[^A-Za-z0-9\-]+")


def _sanitize(query: str) -> str:
    """Reduce a query to alphanum + hyphen tokens for FTS5 safety.

    NB: This is identical to the natural-language path real users would hit
    if their phrasing contained punctuation, since search_knowledge.py
    does NOT itself sanitize — meaning users typing 'foo + bar' currently
    crash retrieval. Captured as a separate retrieval-bug finding.
    """
    return " ".join(t for t in _KEEP.sub(" ", query).split() if t)


def _search(query: str, domain: str | None = None) -> dict:
    return search_knowledge.run_search(_sanitize(query), _ctx(), domain=domain)


def normalize_skill_id(s: str) -> str:
    """`apex/foo` and `apex__foo` and `skills/apex/foo/SKILL.md` all collapse to `apex/foo`."""
    if not s:
        return ""
    s = s.replace("\\", "/")
    if s.startswith("skills/"):
        s = s[len("skills/"):]
    if s.endswith("/SKILL.md"):
        s = s[: -len("/SKILL.md")]
    s = s.replace("__", "/")
    return s


def load_fixtures(path: Path) -> list[dict]:
    raw = json.loads(path.read_text())
    if isinstance(raw, dict) and "queries" in raw:
        return raw["queries"]
    if isinstance(raw, list):
        return raw
    raise SystemExit(f"unexpected fixture shape in {path}")


def evaluate(fixtures: list[dict], top_k: int = 5) -> dict:
    by_domain: dict[str, dict] = defaultdict(
        lambda: {"n": 0, "hit1": 0, "hit3": 0, "coverage": 0}
    )
    misses: list[dict] = []
    no_coverage: list[dict] = []
    weak_top1: list[dict] = []

    n = 0
    hit1 = 0
    hit3 = 0
    cov = 0

    for fx in fixtures:
        query = fx["query"]
        expected = normalize_skill_id(fx.get("expected_skill", ""))
        domain = fx.get("domain", "?")

        result = _search(query, domain=fx.get("domain"))

        skills = result.get("skills") or []
        # run_search returns "skills" as a list of dicts. Normalize id field.
        for s in skills:
            if "id" not in s:
                s["id"] = s.get("slug") or s.get("path") or ""
        chunks = result.get("chunks") or []
        has_cov = bool(result.get("has_coverage"))

        top1_id = normalize_skill_id(skills[0]["id"]) if skills else ""
        top1_score = skills[0]["score"] if skills else 0.0
        top_ids = [normalize_skill_id(s["id"]) for s in skills[:3]]

        n += 1
        by_domain[domain]["n"] += 1
        if has_cov:
            cov += 1
            by_domain[domain]["coverage"] += 1
        else:
            no_coverage.append({"query": query, "domain": domain, "expected": expected})

        if expected:
            if top1_id == expected:
                hit1 += 1
                by_domain[domain]["hit1"] += 1
            if expected in top_ids:
                hit3 += 1
                by_domain[domain]["hit3"] += 1
            else:
                # genuine miss: expected skill not in top 3
                misses.append(
                    {
                        "query": query,
                        "domain": domain,
                        "expected": expected,
                        "top1": top1_id,
                        "top1_score": round(top1_score, 3),
                        "top3": top_ids,
                        "top_chunk_path": chunks[0]["path"] if chunks else "",
                    }
                )

        # weak retrieval signal: skill found but score < 1.0 means the query
        # didn't strongly match — worth flagging even when expected is hit.
        if skills and top1_score < 1.0:
            weak_top1.append(
                {"query": query, "top1": top1_id, "score": round(top1_score, 3)}
            )

    summary = {
        "fixture_count": n,
        "hit_at_1": round(hit1 / n, 4) if n else 0,
        "hit_at_3": round(hit3 / n, 4) if n else 0,
        "coverage_rate": round(cov / n, 4) if n else 0,
        "by_domain": {
            d: {
                "n": v["n"],
                "hit_at_1": round(v["hit1"] / v["n"], 4) if v["n"] else 0,
                "hit_at_3": round(v["hit3"] / v["n"], 4) if v["n"] else 0,
                "coverage_rate": round(v["coverage"] / v["n"], 4) if v["n"] else 0,
            }
            for d, v in sorted(by_domain.items())
        },
        "misses": misses,
        "no_coverage": no_coverage,
        "weak_top1_count": len(weak_top1),
    }
    return summary


def write_markdown(summary: dict, label: str, path: Path) -> None:
    lines = []
    lines.append(f"# Retrieval eval — {label}\n")
    lines.append(f"- fixtures: **{summary['fixture_count']}**")
    lines.append(f"- Hit@1: **{summary['hit_at_1'] * 100:.1f}%**")
    lines.append(f"- Hit@3: **{summary['hit_at_3'] * 100:.1f}%**")
    lines.append(f"- Coverage rate: **{summary['coverage_rate'] * 100:.1f}%**")
    lines.append(f"- Weak top-1 (score<1.0): {summary['weak_top1_count']}")
    lines.append("")
    lines.append("## By domain\n")
    lines.append("| Domain | N | Hit@1 | Hit@3 | Coverage |")
    lines.append("|---|---:|---:|---:|---:|")
    for d, v in summary["by_domain"].items():
        lines.append(
            f"| {d} | {v['n']} | {v['hit_at_1']*100:.1f}% | {v['hit_at_3']*100:.1f}% | {v['coverage_rate']*100:.1f}% |"
        )
    lines.append("")

    misses = summary.get("misses", [])
    if misses:
        lines.append(f"## Misses (expected NOT in top-3) — {len(misses)} cases\n")
        # Group by expected skill so we can see which skills retrieve poorly.
        by_expected: dict[str, list] = defaultdict(list)
        for m in misses:
            by_expected[m["expected"]].append(m)
        # Show worst offenders first.
        worst = sorted(by_expected.items(), key=lambda kv: -len(kv[1]))[:30]
        lines.append("### Worst-retrieved skills (most missed queries)\n")
        lines.append("| Expected skill | # misses |")
        lines.append("|---|---:|")
        for sk, lst in worst:
            lines.append(f"| `{sk}` | {len(lst)} |")
        lines.append("")
        lines.append("### Sample miss cases (first 25)\n")
        for m in misses[:25]:
            lines.append(f"- **Q:** {m['query']!r}")
            lines.append(f"  - expected: `{m['expected']}`")
            lines.append(f"  - top-1: `{m['top1']}` (score {m['top1_score']})")
            lines.append(f"  - top-3: {m['top3']}")
            lines.append("")

    no_cov = summary.get("no_coverage", [])
    if no_cov:
        lines.append(f"## Queries with no coverage signal — {len(no_cov)} cases\n")
        for q in no_cov[:25]:
            lines.append(f"- {q['query']!r} (domain: {q['domain']}, expected: `{q['expected']}`)")
        lines.append("")

    path.write_text("\n".join(lines))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fixtures", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--label", default="run")
    p.add_argument("--top-k", type=int, default=5)
    args = p.parse_args()

    fx = load_fixtures(Path(args.fixtures))
    print(f"loaded {len(fx)} fixtures from {args.fixtures}", file=sys.stderr)
    summary = evaluate(fx, top_k=args.top_k)
    Path(args.out).write_text(json.dumps(summary, indent=2))
    write_markdown(summary, args.label, Path(args.report))
    print(
        f"label={args.label}  N={summary['fixture_count']}  "
        f"Hit@1={summary['hit_at_1']*100:.1f}%  Hit@3={summary['hit_at_3']*100:.1f}%  "
        f"Coverage={summary['coverage_rate']*100:.1f}%",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
