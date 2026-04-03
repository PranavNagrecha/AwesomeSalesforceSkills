#!/usr/bin/env python3
"""
Run retrieval tests against query-variants.json.

Each variant is a phrasing a real user might type. We run search_knowledge
without domain filter (realistic) and with domain (from expected_skill) and
report whether the expected skill appears in the top 3 and has_coverage.

Usage:
  python3 scripts/run_retrieval_variants.py              # no domain
  python3 scripts/run_retrieval_variants.py --domain     # use domain from expected_skill
  python3 scripts/run_retrieval_variants.py --json       # machine-readable summary
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS_PATH = ROOT / "vector_index" / "query-variants.json"
TOP_K = 3


def run_search(query: str, domain: str | None) -> dict:
    cmd = [sys.executable, str(ROOT / "scripts" / "search_knowledge.py"), query, "--json"]
    if domain:
        cmd.extend(["--domain", domain])
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": result.stderr or "search_knowledge failed", "has_coverage": False, "skills": []}
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Test retrieval with varied user phrasings.")
    parser.add_argument("--domain", action="store_true", help="Pass domain from expected_skill to search.")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON summary.")
    args = parser.parse_args()

    if not VARIANTS_PATH.exists():
        print("Missing vector_index/query-variants.json", file=sys.stderr)
        return 1

    data = json.loads(VARIANTS_PATH.read_text(encoding="utf-8"))
    variants = data.get("variants", [])

    total = 0
    passed = 0
    failed: list[dict] = []

    for block in variants:
        expected = block.get("expected_skill", "")
        domain = block.get("domain") or (expected.split("/")[0] if "/" in expected else None)
        for query in block.get("queries", []):
            total += 1
            use_domain = domain if args.domain else None
            out = run_search(query, use_domain)
            if out.get("error"):
                failed.append({
                    "query": query,
                    "expected_skill": expected,
                    "error": out["error"],
                    "top_skills": [],
                    "has_coverage": False,
                })
                continue
            skills = out.get("skills", [])
            top_ids = [s["id"] for s in skills[:TOP_K]]
            has_coverage = out.get("has_coverage", False)
            ok = expected in top_ids
            if ok:
                passed += 1
            else:
                failed.append({
                    "query": query,
                    "expected_skill": expected,
                    "has_coverage": has_coverage,
                    "top_skills": top_ids,
                    "top_scores": [round(s.get("score", 0), 3) for s in skills[:TOP_K]],
                })

    if args.json:
        print(json.dumps({
            "total": total,
            "passed": passed,
            "failed_count": len(failed),
            "failed": failed,
        }, indent=2))
        return 0 if not failed else 1

    print(f"Variants: {total} total, {passed} passed, {len(failed)} failed")
    if failed:
        print("\nFailed (query → expected_skill; has_coverage; top 3 returned):")
        for f in failed:
            top = f.get("top_skills", []) or ["(none)"]
            hc = f.get("has_coverage", False)
            print(f"  \"{f['query']}\"")
            print(f"    expected: {f['expected_skill']}  has_coverage: {hc}  top: {top}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
