#!/usr/bin/env python3
"""
search_skills.py — Context-aware skill search

Extends search_knowledge.py with:
  1. Synonym expansion   — expands query using knowledge/synonyms.yaml
  2. Role-aware boosting — boosts skills relevant to the user's Salesforce role
  3. Cloud-aware boosting — boosts cloud-specific skills when cloud context is set
  4. salesforce-context.md auto-detection — reads project context if present

Usage:
  python3 scripts/search_skills.py "trigger firing twice"
  python3 scripts/search_skills.py "field not visible" --role admin
  python3 scripts/search_skills.py "bulk load timeout" --role data --cloud "Sales Cloud"
  python3 scripts/search_skills.py "integration pattern" --context ./salesforce-context.md
  python3 scripts/search_skills.py "query optimization" --json
  python3 scripts/search_skills.py "apex security" --domain apex --role dev

Falls back to search_knowledge.py behavior when no context is provided.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNONYMS_FILE = ROOT / "knowledge" / "synonyms.yaml"
CONTEXT_FILE = ROOT / "salesforce-context.md"

# ── Role → domain boost map ───────────────────────────────────────────────────

ROLE_DOMAIN_BOOST = {
    "admin":     ["admin"],
    "ba":        ["admin"],
    "dev":       ["apex", "lwc", "flow", "integration", "devops"],
    "developer": ["apex", "lwc", "flow", "integration", "devops"],
    "data":      ["data"],
    "architect": ["admin"],
}

BOOST_AMOUNT = 0.25  # Score boost applied to matching-domain skills

# ── Cloud → keyword signals ───────────────────────────────────────────────────

CLOUD_SIGNALS = {
    "sales cloud":        ["sales", "opportunity", "lead", "forecast", "territory", "quote", "cpq"],
    "service cloud":      ["service", "case", "entitlement", "knowledge", "omni-channel", "sla"],
    "experience cloud":   ["experience", "community", "portal", "guest", "external user", "lwr"],
    "marketing cloud":    ["marketing", "journey", "email studio", "ampscript", "pardot", "mcae"],
    "revenue cloud":      ["cpq", "billing", "quote", "contract", "revenue", "pricing"],
    "field service":      ["field service", "fsl", "work order", "service territory", "mobile worker"],
    "health cloud":       ["health", "patient", "care plan", "ehr", "fhir", "hipaa"],
    "financial services": ["financial", "household", "wealth", "insurance", "banking", "fsc"],
    "nonprofit":          ["npsp", "nonprofit", "donation", "constituent", "gift", "program"],
    "commerce cloud":     ["commerce", "b2b", "b2c", "store", "product catalog", "checkout"],
    "agentforce":         ["agentforce", "einstein", "agent", "ai", "llm", "prompt", "copilot"],
    "omnistudio":         ["omnistudio", "omniscript", "dataraptor", "flexcard", "integration procedure", "vlocity"],
    "analytics":          ["analytics", "crm analytics", "tableau", "dashboard", "dataset", "saql"],
    "integration":        ["mulesoft", "integration", "api", "rest", "soap", "platform event", "cdc"],
    "devops":             ["sfdx", "scratch org", "pipeline", "ci/cd", "deployment", "copado", "gearset"],
}


# ── Minimal YAML list loader (stdlib only) ────────────────────────────────────

def load_synonyms() -> list[dict]:
    """Load knowledge/synonyms.yaml without pyyaml."""
    if not SYNONYMS_FILE.exists():
        return []

    synonyms = []
    current = None
    in_synonyms = False

    for line in SYNONYMS_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- canonical:"):
            if current:
                synonyms.append(current)
            val = stripped.split(":", 1)[1].strip().strip('"')
            current = {"canonical": val, "synonyms": []}
            in_synonyms = False

        elif stripped == "synonyms:" and current is not None:
            in_synonyms = True

        elif stripped.startswith("- ") and in_synonyms and current is not None:
            val = stripped[2:].strip().strip('"')
            current["synonyms"].append(val)

        elif ":" in stripped and not stripped.startswith("-"):
            in_synonyms = False

    if current:
        synonyms.append(current)

    return synonyms


def expand_query(query: str, synonyms: list[dict]) -> str:
    """
    Expand query by adding canonical terms for any matching synonyms.
    Returns original query + canonical terms appended (space-separated).
    Duplicate terms are removed.
    """
    query_lower = query.lower()
    additions = set()

    for entry in synonyms:
        canonical = entry["canonical"].lower()
        # Check if canonical already in query — no expansion needed
        if canonical in query_lower:
            continue
        # Check if any synonym matches
        for syn in entry["synonyms"]:
            if syn.lower() in query_lower:
                additions.add(entry["canonical"])
                break

    if not additions:
        return query

    expanded = query + " " + " ".join(sorted(additions))
    return expanded


# ── salesforce-context.md reader ─────────────────────────────────────────────

def read_context_file(path: Path) -> dict:
    """
    Read salesforce-context.md and extract role and cloud hints.
    Looks for lines like:
      Role: Admin
      Cloud: Sales Cloud
      Primary Role: Developer
    """
    ctx = {"role": None, "cloud": None}
    if not path.exists():
        return ctx

    for line in path.read_text(encoding="utf-8").splitlines():
        low = line.strip().lower()
        if low.startswith("role:") or low.startswith("primary role:"):
            val = line.split(":", 1)[1].strip().lower()
            ctx["role"] = val
        elif low.startswith("cloud:") or low.startswith("primary cloud:"):
            val = line.split(":", 1)[1].strip().lower()
            ctx["cloud"] = val

    return ctx


# ── Core search call ──────────────────────────────────────────────────────────

def run_base_search(query: str, domain: str | None) -> dict:
    """Call search_knowledge.py and return parsed JSON result."""
    cmd = [sys.executable, str(ROOT / "scripts" / "search_knowledge.py"), query, "--json"]
    if domain:
        cmd += ["--domain", domain]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"skills": [], "chunks": [], "official_sources": [], "has_coverage": False}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"skills": [], "chunks": [], "official_sources": [], "has_coverage": False}


# ── Boosting ──────────────────────────────────────────────────────────────────

def apply_role_boost(skills: list[dict], role: str) -> list[dict]:
    """Boost skills whose domain matches the role."""
    role_key = role.lower().strip()
    boost_domains = ROLE_DOMAIN_BOOST.get(role_key, [])
    if not boost_domains:
        return skills

    boosted = []
    for skill in skills:
        skill_id = skill.get("id", "")
        domain = skill_id.split("/")[0] if "/" in skill_id else ""
        score = skill["score"]
        if domain in boost_domains:
            score = min(score + BOOST_AMOUNT, 2.0)  # cap at 2.0
        boosted.append({**skill, "score": round(score, 6)})

    return sorted(boosted, key=lambda s: s["score"], reverse=True)


def apply_cloud_boost(skills: list[dict], cloud: str) -> list[dict]:
    """Boost skills whose name/id contains cloud-specific signals."""
    cloud_key = cloud.lower().strip()
    signals = CLOUD_SIGNALS.get(cloud_key, [])
    if not signals:
        return skills

    boosted = []
    for skill in skills:
        skill_id = skill.get("id", "").lower()
        score = skill["score"]
        for signal in signals:
            if signal in skill_id:
                score = min(score + 0.15, 2.0)
                break
        boosted.append({**skill, "score": round(score, 6)})

    return sorted(boosted, key=lambda s: s["score"], reverse=True)


# ── Output ────────────────────────────────────────────────────────────────────

def print_human(result: dict, original_query: str, expanded_query: str,
                role: str | None, cloud: str | None) -> None:
    print(f"Query: {original_query}")
    if expanded_query != original_query:
        print(f"Expanded: {expanded_query}")
    if role:
        print(f"Role context: {role}")
    if cloud:
        print(f"Cloud context: {cloud}")
    print("")

    skills = result.get("skills", [])
    has_coverage = result.get("has_coverage", False)

    if not has_coverage:
        print("Coverage: NONE — no skill meets the confidence threshold.")
    else:
        print("Top skills:")
        for skill in skills[:5]:
            boost_note = " [boosted]" if skill.get("boosted") else ""
            print(f"  {skill['id']} ({skill['score']:.3f}){boost_note}")

    chunks = result.get("chunks", [])
    if chunks:
        print("\nTop chunks:")
        for chunk in chunks[:5]:
            print(f"  {chunk['path']} [{chunk['score']:.3f}]")
            print(f"  {chunk['snippet']}")

    sources = result.get("official_sources", [])
    if sources:
        print("\nRelated official sources:")
        for src in sources[:5]:
            print(f"  {src['title']}")
            if src.get("url"):
                print(f"  {src['url']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Context-aware skill search with synonym expansion and role/cloud boosting.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/search_skills.py "trigger firing twice"
  python3 scripts/search_skills.py "can't see field" --role admin
  python3 scripts/search_skills.py "bulk load failing" --role data --cloud "Sales Cloud"
  python3 scripts/search_skills.py "apex security" --domain apex --role dev
        """,
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument("--role", help="User role: admin, ba, dev, data, architect")
    parser.add_argument("--cloud", help="Salesforce cloud: 'Sales Cloud', 'Service Cloud', etc.")
    parser.add_argument("--domain", help="Restrict to a specific domain folder")
    parser.add_argument("--context", help="Path to salesforce-context.md for auto role/cloud detection")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--no-expand", action="store_true", help="Disable synonym expansion")

    args = parser.parse_args()

    # Auto-detect role/cloud from context file
    role = args.role
    cloud = args.cloud

    context_path = Path(args.context) if args.context else CONTEXT_FILE
    if (not role or not cloud) and context_path.exists():
        ctx = read_context_file(context_path)
        role = role or ctx.get("role")
        cloud = cloud or ctx.get("cloud")

    # Synonym expansion
    original_query = args.query
    expanded_query = original_query
    if not args.no_expand:
        synonyms = load_synonyms()
        expanded_query = expand_query(original_query, synonyms)

    # Run base search
    result = run_base_search(expanded_query, args.domain)

    # Apply boosts
    skills = result.get("skills", [])
    if role:
        skills = apply_role_boost(skills, role)
    if cloud:
        skills = apply_cloud_boost(skills, cloud)

    # Recompute has_coverage after boosting
    result["skills"] = skills
    result["has_coverage"] = len(skills) > 0
    result["query"] = original_query
    result["expanded_query"] = expanded_query
    result["role_context"] = role
    result["cloud_context"] = cloud

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print_human(result, original_query, expanded_query, role, cloud)
    return 0


if __name__ == "__main__":
    sys.exit(main())
