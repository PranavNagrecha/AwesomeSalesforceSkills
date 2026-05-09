#!/usr/bin/env python3
"""Retrieval eval harness for the three secondary corpora.

Mirrors evals/measurement/retrieval_eval.py but routes queries through the
MCP server's library.py functions (search_agents / search_templates /
search_decision_trees) instead of search_knowledge.run_search.

Why this lives separately from retrieval_eval.py:
- Skill retrieval uses FTS5 + optional embedding rerank.
- Agent/template/tree retrieval uses a hand-weighted keyword scorer in
  mcp/sfskills-mcp/src/sfskills_mcp/library.py.
- The two pipelines have different SearchContexts and different ground-truth
  shapes (skill_id vs agent name vs template path vs tree name).

Output schema:
    {
      "corpus": "agents",
      "fixture_count": 247,
      "hit_at_1": 0.83,
      "hit_at_3": 0.94,
      "coverage_rate": 0.99,
      "misses": [...],
      "no_coverage": [...]
    }

Usage:
    python3 evals/measurement/retrieval_eval_corpora.py \\
        --corpus agents \\
        --fixtures /tmp/nl_agents.json \\
        --out /tmp/agents_baseline.json \\
        --report /tmp/agents_baseline.md \\
        --label "agents NL baseline (trivial scorer)"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
# Add MCP src to path so we can import library.py
sys.path.insert(0, str(REPO / "mcp" / "sfskills-mcp" / "src"))

from sfskills_mcp import library, paths as _paths  # noqa: E402

# Pin paths to this repo (the MCP package autodetects from cwd otherwise).
_paths.repo_root = lambda: REPO  # type: ignore[assignment]


def _normalize_template_id(s: str) -> str:
    """Templates output as POSIX paths; queries store the same. Normalize separators."""
    return s.replace("\\", "/")


def _agent_top_ids(query: str, k: int) -> list[str]:
    res = library.search_agents(query, limit=max(k, 10))
    return [a["name"] for a in res.get("agents", [])][:k]


def _template_top_ids(query: str, k: int) -> list[str]:
    res = library.search_templates(query, limit=max(k, 10))
    return [_normalize_template_id(t["path"]) for t in res.get("templates", []) if t.get("path")][:k]


def _tree_top_ids(query: str, k: int) -> list[str]:
    res = library.search_decision_trees(query, limit=max(k, 10))
    return [tree["name"] for tree in res.get("trees", []) if tree.get("name")][:k]


SEARCHERS = {
    "agents": _agent_top_ids,
    "templates": _template_top_ids,
    "decision-trees": _tree_top_ids,
}


def run_eval(corpus: str, fixtures: list[dict], top_k: int = 3) -> dict:
    searcher = SEARCHERS[corpus]
    n = len(fixtures)
    hit1 = 0
    hit3 = 0
    has_cov = 0
    misses: list[dict] = []
    no_coverage: list[dict] = []
    by_expected: defaultdict = defaultdict(lambda: {"n": 0, "hit1": 0, "hit3": 0})

    # For templates: rel-path in fixtures uses '/'. Make sure templates retrieval
    # ids use '/' too (they ship as POSIX paths from library.py).
    for fx in fixtures:
        query = fx["query"]
        expected = (
            _normalize_template_id(fx["expected"])
            if corpus == "templates"
            else fx["expected"]
        )
        topk = searcher(query, top_k)
        if topk:
            has_cov += 1
        if topk and topk[0] == expected:
            hit1 += 1
            by_expected[expected]["hit1"] += 1
        if expected in topk:
            hit3 += 1
            by_expected[expected]["hit3"] += 1
        else:
            if not topk:
                no_coverage.append({"query": query, "expected": expected})
            else:
                misses.append({
                    "query": query,
                    "expected": expected,
                    "top1": topk[0] if topk else None,
                    "top3": topk[:3],
                })
        by_expected[expected]["n"] += 1

    return {
        "corpus": corpus,
        "fixture_count": n,
        "hit_at_1": hit1 / n if n else 0.0,
        "hit_at_3": hit3 / n if n else 0.0,
        "coverage_rate": has_cov / n if n else 0.0,
        "by_expected_summary": {
            k: {"n": v["n"], "hit_at_1": v["hit1"]/v["n"] if v["n"] else 0.0}
            for k, v in by_expected.items()
        },
        "misses": misses,
        "no_coverage": no_coverage,
    }


def write_report(out_md: Path, label: str, results: dict) -> None:
    lines = [f"# Retrieval eval — {label}", ""]
    lines.append(f"- corpus: **{results['corpus']}**")
    lines.append(f"- fixtures: **{results['fixture_count']}**")
    lines.append(f"- Hit@1: **{results['hit_at_1']:.1%}**")
    lines.append(f"- Hit@3: **{results['hit_at_3']:.1%}**")
    lines.append(f"- Coverage rate: **{results['coverage_rate']:.1%}**")
    lines.append("")

    miss_count = len(results["misses"])
    no_cov_count = len(results["no_coverage"])
    if miss_count:
        lines.append(f"## Misses (expected NOT in top-3) — {miss_count} cases")
        lines.append("")
        # Group by expected
        by_exp: defaultdict = defaultdict(list)
        for m in results["misses"]:
            by_exp[m["expected"]].append(m)
        worst = sorted(by_exp.items(), key=lambda x: -len(x[1]))[:30]
        lines.append("### Worst-retrieved (most missed queries)")
        lines.append("")
        lines.append("| Expected | # misses |")
        lines.append("|---|---:|")
        for exp, ms in worst:
            lines.append(f"| `{exp}` | {len(ms)} |")
        lines.append("")
    if no_cov_count:
        lines.append(f"## No coverage — {no_cov_count} cases")
        lines.append("")
        for nc in results["no_coverage"][:20]:
            lines.append(f"- `{nc['expected']}` ← {nc['query']!r}")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, choices=list(SEARCHERS))
    p.add_argument("--fixtures", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--label", default="")
    p.add_argument("--top-k", type=int, default=3)
    args = p.parse_args()

    fixtures = json.loads(Path(args.fixtures).read_text())
    if not isinstance(fixtures, list):
        print("fixtures must be a JSON list", file=sys.stderr)
        return 2

    label = args.label or f"{args.corpus} corpus eval"
    results = run_eval(args.corpus, fixtures, top_k=args.top_k)
    Path(args.out).write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    write_report(Path(args.report), label, results)
    print(
        f"label={label}  corpus={results['corpus']}  N={results['fixture_count']}  "
        f"Hit@1={results['hit_at_1']:.1%}  Hit@3={results['hit_at_3']:.1%}  "
        f"Coverage={results['coverage_rate']:.1%}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
