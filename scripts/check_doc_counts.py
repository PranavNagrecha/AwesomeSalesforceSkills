#!/usr/bin/env python3
"""Count-consistency gate for hand-maintained docs.

The skill / agent / tool counts quoted in README.md, the MCP README,
CLAUDE.md, AGENT_RULES.md, and RUNTIME_VS_BUILD.md are easy to let drift
when the corpus or the agent roster changes. This checker derives the
*canonical* counts from machine-readable sources and asserts every quoted
number matches:

  - skills total + per-domain  -> registry/skills.json (skill_count, domain_counts)
  - agents build/active/deprecated/total -> agents/*/AGENT.md frontmatter
    (the `class` and `status` fields, which are the canonical source per
    CLAUDE.md — frontmatter wins)
  - MCP tool count -> `@mcp.tool` registrations in the server source
  - flagship evals -> evals/golden/*.md

It also enforces that the four runtime-tier sub-counts in each roster doc
sum to the active-runtime total — the exact invariant that broke when nine
deprecated agents were left in the runtime tiers while the headline said 56.

stdlib only. Run standalone (`python3 scripts/check_doc_counts.py`) or import
``collect_doc_count_issues`` from validate_repo.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Em dash used in the tier headings across the docs.
DASH = "—"


# ---------------------------------------------------------------------------
# Canonical counts (derived, never hand-typed)
# ---------------------------------------------------------------------------

def _frontmatter_field(text: str, field: str) -> str | None:
    """Return the value of ``field`` from the leading YAML frontmatter block."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else text
    m = re.search(rf"^{re.escape(field)}:\s*(.+?)\s*$", block, re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'")


def canonical_counts(root: Path = ROOT) -> dict:
    registry = json.loads((root / "registry" / "skills.json").read_text(encoding="utf-8"))

    build = active_runtime = deprecated = total = 0
    for agent_md in sorted((root / "agents").glob("*/AGENT.md")):
        text = agent_md.read_text(encoding="utf-8")
        cls = _frontmatter_field(text, "class")
        status = _frontmatter_field(text, "status")
        total += 1
        if status == "deprecated":
            deprecated += 1
        elif cls == "build":
            build += 1
        elif cls == "runtime":
            active_runtime += 1

    server = root / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp" / "server.py"
    mcp_tools = len(re.findall(r"@mcp\.tool", server.read_text(encoding="utf-8"))) if server.exists() else 0

    return {
        "skills_total": int(registry["skill_count"]),
        "domain_counts": registry["domain_counts"],
        "agents_total": total,
        "build": build,
        "active_runtime": active_runtime,
        "deprecated": deprecated,
        "mcp_tools": mcp_tools,
        "evals_flagship": len(list((root / "evals" / "golden").glob("*.md"))),
    }


# ---------------------------------------------------------------------------
# Doc assertions
# ---------------------------------------------------------------------------

# Each entry: (relative path, regex, [canonical keys for each capture group]).
# A missing match is itself an error — it means a labelled count was renamed
# or removed and the lint can no longer guard it.
GLOBAL_CHECKS: list[tuple[str, str, list[str]]] = [
    ("README.md", r"\*\*([\d,]+) skills · (\d+) agents", ["skills_total", "agents_total"]),
    ("README.md", r"— ([\d,]+) structured guides", ["skills_total"]),
    ("README.md", r"(\d+) tools across skill", ["mcp_tools"]),
    ("README.md", r"\*\*Build-time \((\d+)\)\*\*", ["build"]),
    ("README.md", r"\*\*Run-time \((\d+)\)\*\*", ["active_runtime"]),
    ("README.md", r"(\d+) read-only tools — the fifteen", ["mcp_tools"]),
    ("README.md", r"([\d,]+)-skill SfSkills corpus", ["skills_total"]),
    ("README.md", r"\[x\] ([\d,]+) skills across", ["skills_total"]),
    ("README.md", r"Golden evals for (\d+) flagship", ["evals_flagship"]),
    ("mcp/sfskills-mcp/README.md", r"library \(([\d,]+)\+? Salesforce skills", ["skills_total"]),
    ("mcp/sfskills-mcp/README.md", r"\((\d+) active runtime agents", ["active_runtime"]),
    ("mcp/sfskills-mcp/README.md", r"(\d+) build-time agents and\s+(\d+) deprecation stubs", ["build", "deprecated"]),
    ("CLAUDE.md", r"Run-time agents \((\d+)\)", ["active_runtime"]),
    ("AGENT_RULES.md", r"\*\*Build-time \((\d+)\)\*\*", ["build"]),
    ("AGENT_RULES.md", r"\*\*Run-time \((\d+)\)\*\*", ["active_runtime"]),
    ("agents/_shared/RUNTIME_VS_BUILD.md", r"Build-time agents \((\d+)\)", ["build"]),
    ("agents/_shared/RUNTIME_VS_BUILD.md", r"Run-time agents \((\d+)\)", ["active_runtime"]),
    ("agents/_shared/RUNTIME_VS_BUILD.md", r"Deprecated \((\d+)\)", ["deprecated"]),
]

# Files whose four runtime-tier sub-counts must sum to active_runtime.
TIER_SUM_FILES = [
    "README.md",
    "mcp/sfskills-mcp/README.md",
    "CLAUDE.md",
    "AGENT_RULES.md",
    "agents/_shared/RUNTIME_VS_BUILD.md",
]
TIER_PATTERNS = [
    r"Developer \+ architecture(?: tier)? \((\d+)\)",
    rf"Admin accelerators {DASH} Tier 1 \((\d+)\)",
    rf"Strategic {DASH} Tier 2 \((\d+)\)",
    rf"Vertical \+ governance {DASH} Tier 3 \((\d+)\)",
]

# README "Covered Skills" table rows: "| Admin | 252 — ..."
DOMAIN_ROW_RE = re.compile(r"^\| (\w+) \| (\d+) " + DASH, re.MULTILINE)


def collect_doc_count_issues(root: Path = ROOT) -> list[tuple[str, str, str]]:
    """Return (level, path, message) tuples. Empty list == all counts consistent."""
    counts = canonical_counts(root)
    issues: list[tuple[str, str, str]] = []

    def err(path: str, msg: str) -> None:
        issues.append(("ERROR", path, msg))

    for rel, pattern, keys in GLOBAL_CHECKS:
        fpath = root / rel
        if not fpath.exists():
            err(rel, "file not found (doc-count check expected it)")
            continue
        m = re.search(pattern, fpath.read_text(encoding="utf-8"))
        if not m:
            err(rel, f"labelled count not found for /{pattern}/ — doc restructured? update check_doc_counts.py")
            continue
        for group_i, key in enumerate(keys, start=1):
            actual = int(m.group(group_i).replace(",", ""))
            expected = counts[key]
            if actual != expected:
                err(rel, f"{key} is {actual} in doc but canonical is {expected} (pattern /{pattern}/)")

    for rel in TIER_SUM_FILES:
        fpath = root / rel
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8")
        tier_vals = []
        for tp in TIER_PATTERNS:
            tm = re.search(tp, text)
            if not tm:
                err(rel, f"runtime-tier header not found for /{tp}/ — cannot verify tier sum")
                tier_vals = []
                break
            tier_vals.append(int(tm.group(1)))
        if tier_vals:
            tier_sum = sum(tier_vals)
            if tier_sum != counts["active_runtime"]:
                err(rel, f"runtime tiers sum to {tier_sum} ({'+'.join(map(str, tier_vals))}) "
                         f"but active-runtime total is {counts['active_runtime']}")

    # README per-domain "Covered Skills" table.
    readme = root / "README.md"
    if readme.exists():
        seen = {}
        for m in DOMAIN_ROW_RE.finditer(readme.read_text(encoding="utf-8")):
            label, num = m.group(1), int(m.group(2))
            seen[label.lower()] = num
        for domain, expected in counts["domain_counts"].items():
            if domain in seen and seen[domain] != expected:
                err("README.md", f"Covered-Skills table: {domain} shows {seen[domain]} but canonical is {expected}")

    return issues


def main() -> int:
    issues = collect_doc_count_issues(ROOT)
    counts = canonical_counts(ROOT)
    if not issues:
        print(
            f"Doc counts consistent: {counts['skills_total']} skills, "
            f"{counts['active_runtime']} active runtime + {counts['build']} build + "
            f"{counts['deprecated']} deprecated = {counts['agents_total']} agents, "
            f"{counts['mcp_tools']} MCP tools."
        )
        return 0
    for level, path, msg in issues:
        print(f"{level} {path}: {msg}")
    print(f"{len(issues)} doc-count error(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
