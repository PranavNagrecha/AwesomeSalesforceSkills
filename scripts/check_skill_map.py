#!/usr/bin/env python3
"""Consistency gate between `agents/_shared/SKILL_MAP.md` and agent frontmatter.

`SKILL_MAP.md` is the hand-maintained authoring reference: "agent X cites
skill Y". The machine-readable truth is each agent's `dependencies.skills:`
block in `agents/<id>/AGENT.md`. Nothing kept the two in step, so when an
agent's reading list was trimmed the map kept advertising the pre-trim set —
which is worse than no map, because the next author cites from it.

Two directions, both WARN:

* FORWARD — the map says agent X cites skill Y, but Y is absent from X's
  `dependencies.skills:`. The map is claiming coverage that does not exist.
* REVERSE — the map marks a skill "(no runtime agent — uncited)" but some
  agent now declares it. The map is under-reporting coverage, which sends
  the next author off to write a duplicate skill.

Both are WARN and not ERROR on purpose: the map is prose, its bullet grammar
varies, and a parser over prose should not be able to red the tree. The point
is a number that has to go down, not a gate that has to be silenced.

Deprecated agents (frontmatter `status: deprecated`) are skipped — their
reading lists are intentionally empty and charging the map for them would
bury the live drift.

`--json` emits machine-readable findings; `--strict` exits non-zero when any
drift is found. stdlib only. Run standalone or import
``collect_skill_map_issues``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKILL_MAP = Path("agents/_shared/SKILL_MAP.md")

# `domain/slug` inside backticks. The domain is checked against skills/ on
# disk, so `templates/admin/...`, `standards/decision-trees/...` and
# `agents/_shared/...` fall out without a special case.
_TICKED_RE = re.compile(r"`([a-z0-9][a-z0-9\-]*/[a-z0-9][a-z0-9\-]*)`")
# Bare or backticked identifier, matched against the real agent directory
# names — the map writes attributions both ways ("→ `flow-analyzer`" and
# "→ sandbox-strategy-designer").
_IDENT_RE = re.compile(r"`?([a-z][a-z0-9\-]{2,})`?")

_HEADING_AGENT_RE = re.compile(r"^###\s+`([a-z0-9\-]+)`")
# "`a`, `b` and `c` additionally cite:" / "which cites all five ...:"
_INTRO_RE = re.compile(r"\b(additionally cites?|which cites)\b")
_UNCITED_RE = re.compile(r"no runtime agent", re.IGNORECASE)
_ARROW = "→"
# Em/en dash used to start a free-text description on a bullet.
_DESC_SPLIT_RE = re.compile(r"\s[—–]\s")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else text


def _declared_skills(front: str) -> set[str]:
    """Pull `dependencies: skills: - <id>` without a YAML dependency."""
    out: set[str] = set()
    in_deps = False
    in_skills = False
    for line in front.splitlines():
        if re.match(r"^dependencies:\s*$", line):
            in_deps = True
            continue
        if in_deps and re.match(r"^\S", line):
            break  # next top-level key
        if not in_deps:
            continue
        if re.match(r"^\s{2}skills:\s*$", line):
            in_skills = True
            continue
        if in_skills:
            item = re.match(r"^\s{4,}-\s*(\S+)\s*$", line)
            if item:
                out.add(item.group(1).strip().strip('"').strip("'"))
                continue
            if line.strip():
                in_skills = False  # sibling key (templates:, shared:, ...)
    return out


def load_agents(root: Path) -> dict[str, dict]:
    agents: dict[str, dict] = {}
    for agent_md in sorted((root / "agents").glob("*/AGENT.md")):
        front = _frontmatter(agent_md.read_text(encoding="utf-8"))
        status = re.search(r"^status:\s*(.+?)\s*$", front, re.MULTILINE)
        agents[agent_md.parent.name] = {
            "status": (status.group(1).strip() if status else ""),
            "skills": _declared_skills(front),
        }
    return agents


def load_domains(root: Path) -> set[str]:
    skills_root = root / "skills"
    return {d.name for d in skills_root.iterdir() if d.is_dir()} if skills_root.is_dir() else set()


# ---------------------------------------------------------------------------
# SKILL_MAP parsing
# ---------------------------------------------------------------------------

class Claim:
    __slots__ = ("skill", "agents", "uncited", "line_no", "line")

    def __init__(self, skill: str, agents: list[str], uncited: bool, line_no: int, line: str):
        self.skill = skill
        self.agents = agents
        self.uncited = uncited
        self.line_no = line_no
        self.line = line


def parse_skill_map(text: str, domains: set[str], agent_ids: set[str]) -> list[Claim]:
    """Extract (skill, [agent]) claims from the map's bullet grammars.

    Three grammars are in use and all three are handled:

      1. `### \\`agent\\`` heading, then plain bullets -> heading agent.
      2. "\\`a\\`, \\`b\\` additionally cite:" intro, then plain bullets -> a, b.
      3. Per-bullet override: "- \\`domain/slug\\` -> \\`agent\\` - description",
         including "-> (no runtime agent - uncited ...)".

    A per-bullet arrow always wins over the section context.
    """
    claims: list[Claim] = []
    context: list[str] = []

    def skills_in(fragment: str) -> list[str]:
        return [s for s in _TICKED_RE.findall(fragment) if s.split("/", 1)[0] in domains]

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()

        if line.startswith("## "):
            context = []
            continue
        if line.startswith("### "):
            m = _HEADING_AGENT_RE.match(line)
            context = [m.group(1)] if m and m.group(1) in agent_ids else []
            continue

        stripped = line.strip()
        if not stripped.startswith("- "):
            # Candidate intro line: agents named *before* the "cite" verb.
            m = _INTRO_RE.search(stripped)
            if m:
                named = [i for i in _IDENT_RE.findall(stripped[: m.start()]) if i in agent_ids]
                if named:
                    context = named
            continue

        body = stripped[2:]
        if _ARROW in body:
            left, right = body.split(_ARROW, 1)
            if _UNCITED_RE.search(right):
                targets, uncited = [], True
            else:
                # Stop at the free-text description: agent ids appearing in
                # prose after the dash are commentary, not attribution.
                head = _DESC_SPLIT_RE.split(right, 1)[0]
                targets = [i for i in _IDENT_RE.findall(head) if i in agent_ids]
                uncited = False
        else:
            left, targets, uncited = body, list(context), False

        # Only the part before any description carries skill ids.
        for skill in skills_in(_DESC_SPLIT_RE.split(left, 1)[0]):
            claims.append(Claim(skill, targets, uncited, line_no, stripped))

    return claims


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def collect_skill_map_issues(root: Path = ROOT) -> list[dict]:
    """Return a list of finding dicts. Empty list == map agrees with frontmatter."""
    map_path = root / SKILL_MAP
    if not map_path.exists():
        return [{
            "level": "WARN",
            "direction": "missing",
            "path": str(SKILL_MAP),
            "line": 0,
            "message": f"{SKILL_MAP} not found — nothing to check against agent frontmatter.",
        }]

    agents = load_agents(root)
    domains = load_domains(root)
    live = {aid: info for aid, info in agents.items() if info["status"] != "deprecated"}
    claims = parse_skill_map(map_path.read_text(encoding="utf-8"), domains, set(agents))

    declared_by: dict[str, set[str]] = {}
    for aid, info in live.items():
        for skill in info["skills"]:
            declared_by.setdefault(skill, set()).add(aid)

    findings: list[dict] = []
    for claim in claims:
        if claim.uncited:
            holders = sorted(declared_by.get(claim.skill, ()))
            if holders:
                findings.append({
                    "level": "WARN",
                    "direction": "reverse",
                    "path": str(SKILL_MAP),
                    "line": claim.line_no,
                    "skill": claim.skill,
                    "agents": holders,
                    "message": (
                        f"map marks `{claim.skill}` as having no runtime agent, but "
                        f"{', '.join(holders)} declare(s) it in dependencies.skills — "
                        f"the map under-reports coverage and will send the next author "
                        f"to write a duplicate."
                    ),
                })
            continue
        for aid in claim.agents:
            if aid not in live:
                continue  # deprecated agent — reading list intentionally empty
            if claim.skill not in live[aid]["skills"]:
                findings.append({
                    "level": "WARN",
                    "direction": "forward",
                    "path": str(SKILL_MAP),
                    "line": claim.line_no,
                    "skill": claim.skill,
                    "agents": [aid],
                    "message": (
                        f"map says `{aid}` cites `{claim.skill}`, but it is absent from "
                        f"that agent's dependencies.skills — stale coverage claim."
                    ),
                })

    findings.sort(key=lambda f: (f["direction"], f["line"], f.get("skill", "")))
    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Consistency gate between SKILL_MAP.md and agent frontmatter."
    )
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero when any drift is found (default exits 0)")
    args = ap.parse_args(argv)

    findings = collect_skill_map_issues(ROOT)
    forward = [f for f in findings if f["direction"] == "forward"]
    reverse = [f for f in findings if f["direction"] == "reverse"]

    if args.json:
        print(json.dumps({
            "skill_map": str(SKILL_MAP),
            "total": len(findings),
            "forward": len(forward),
            "reverse": len(reverse),
            "findings": findings,
        }, indent=2))
    elif not findings:
        print(f"{SKILL_MAP} agrees with agent frontmatter in both directions.")
    else:
        for f in findings:
            print(f"{f['level']} {f['path']}:{f['line']} [{f['direction']}] {f['message']}")
        print(
            f"\n{len(findings)} SKILL_MAP drift warning(s): "
            f"{len(forward)} forward (map claims a citation the agent does not declare), "
            f"{len(reverse)} reverse (map says uncited, an agent declares it)."
        )

    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
