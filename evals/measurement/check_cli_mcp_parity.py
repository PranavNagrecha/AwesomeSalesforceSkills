#!/usr/bin/env python3
"""Prove the CLI and MCP retrieval surfaces return the same skills.

`scripts/search_knowledge.run_search` and
`mcp/sfskills-mcp/src/sfskills_mcp/skills.search_skill` re-implement the same
pipeline — lexical window, rerank, aggregate, coverage gate — against the same
index. They are not one function called twice, so they can drift, and a drift
here is invisible: both surfaces keep answering, they just stop agreeing about
which skill covers a query.

Three documents (`docs/architecture.md`, `docs/troubleshooting.md`,
`docs/worked-example-trigger-consolidation.md`) and the MCP module's own
docstring have named THIS path as the regression test that catches that. Until
2026-08-13 the file did not exist, so parity was asserted and never checked.

What counts as parity, and what deliberately does not:

  * PARITY — the gated skill list. Same ids, same order, same `has_coverage`
    verdict. This is the contract: ask either surface which skill covers a
    query and get the same answer.
  * NOT PARITY — payload shape. The MCP enriches each hit from the registry
    (`name`, `category`, `status`, …) and returns `skill_id`/`domain` on
    chunks. Those are additive client conveniences, not retrieval behaviour.
  * NOT PARITY — the lexical window when a client asks for `limit > 10`. The
    CLI uses `retrieval.lexical_limit`; the MCP uses `max(limit * 3, 30)`.
    At the default limit they are both 30. Above it the MCP widens, which
    changes recall by design. This runner therefore compares at the default.

Usage:
    python3 evals/measurement/check_cli_mcp_parity.py            # default query set
    python3 evals/measurement/check_cli_mcp_parity.py --heldout  # 154 held-out queries
    python3 evals/measurement/check_cli_mcp_parity.py --json out.json

Exit code is 1 on any divergence, so this is CI-safe.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "mcp" / "sfskills-mcp" / "src"))

from search_knowledge import build_search_context, run_search  # noqa: E402

# The MCP package resolves the repo through its own paths module; point it here
# so a dev checkout compares like-for-like against the CLI.
from sfskills_mcp import skills as mcp_skills  # noqa: E402

# Queries that exercise the parts of the pipeline most likely to drift:
# the coverage gate, the name/description bonus, domain scoping, and the
# skill-scoped window that knowledge/ imports used to crowd out.
DEFAULT_QUERIES: list[tuple[str, str | None]] = [
    ("set up single sign on", None),
    ("share data between two lightning web components", None),
    ("integrate with an external rest api", None),
    ("move changes from sandbox to production safely", None),
    ("search across objects for a phone number", None),
    ("apex trigger handler pattern bulkification", None),
    ("flow fault path error handling", None),
    ("too many SOQL queries 101 error", None),
    ("permission set group muting", None),
    ("bulk api 2.0 job failed rows", None),
    ("omniscript data mapper performance", None),
    ("restriction rule record access", None),
    ("trigger recursion", "apex"),
    ("wire adapter refresh", "lwc"),
    ("zzzznonexistenttoken", None),
]


def _cli(query: str, domain: str | None, ctx) -> dict:
    payload = run_search(query, ctx, domain=domain)
    return {
        "has_coverage": payload["has_coverage"],
        "skills": [s["id"] for s in payload["skills"]],
    }


def _mcp(query: str, domain: str | None) -> dict:
    payload = mcp_skills.search_skill(query=query, domain=domain)
    return {
        "has_coverage": payload.get("has_coverage"),
        "skills": [s["id"] for s in payload.get("skills", [])],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--heldout", action="store_true",
                    help="use evals/measurement/heldout-queries.json instead of the built-in set")
    ap.add_argument("--json", type=Path, help="write the full comparison to this path")
    args = ap.parse_args()

    if args.heldout:
        raw = json.loads((REPO / "evals/measurement/heldout-queries.json").read_text())
        queries = [(q["query"], q.get("domain")) for q in raw["queries"]]
    else:
        queries = DEFAULT_QUERIES

    ctx = build_search_context(REPO)
    rows, diverged = [], []
    for query, domain in queries:
        cli, mcp = _cli(query, domain, ctx), _mcp(query, domain)
        ok = cli == mcp
        row = {"query": query, "domain": domain, "match": ok, "cli": cli, "mcp": mcp}
        rows.append(row)
        if not ok:
            diverged.append(row)

    print(f"CLI/MCP retrieval parity: {len(rows) - len(diverged)}/{len(rows)} queries agree")
    for row in diverged:
        print(f"\n  DIVERGED  {row['query']!r} (domain={row['domain']})")
        print(f"    cli coverage={row['cli']['has_coverage']} skills={row['cli']['skills'][:5]}")
        print(f"    mcp coverage={row['mcp']['has_coverage']} skills={row['mcp']['skills'][:5]}")

    if args.json:
        args.json.write_text(json.dumps(rows, indent=1))
        print(f"\nwrote {args.json}")

    if diverged:
        print(f"\nFAIL: {len(diverged)} quer(ies) diverged. The gate or the window "
              f"changed in one surface and not the other.")
        return 1
    print("OK: both surfaces return the same gated skill list for every query.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
