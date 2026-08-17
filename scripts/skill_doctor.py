#!/usr/bin/env python3
"""Tell me what to do next on a skill — instead of making me work it out.

`new_skill.py` scaffolds a package and prints a six-step checklist. From then on
the checklist is in your head: which TODOs are left, whether the anti-patterns
file hit five entries, whether a fixture exists, whether an agent cites it,
whether the registry is stale. `validate_repo.py` will tell you eventually, but
it takes ~12 minutes over 1,027 packages and reports problems rather than the
NEXT ACTION.

This does the bookkeeping. Point it at a skill and it prints one thing: the next
command to run, or the next file to open and why.

    python3 scripts/skill_doctor.py apex/trigger-framework   # one skill
    python3 scripts/skill_doctor.py --all                    # everything unfinished, worst first
    python3 scripts/skill_doctor.py --all --new              # only stub/TODO packages
    python3 scripts/skill_doctor.py apex/foo --json          # machine-readable

Every check maps to a gate that already exists somewhere in the repo. Nothing
here is a new standard — it is the standards, collected into one place and
evaluated against real files rather than remembered.

ONE CHECK IS NOT IN validate_repo.py, deliberately: `routing`. It asks whether
the description carries a `NOT for X - use Y` clause naming a REAL package.
That clause is the highest-value token in the shipped roster gloss
(`.claude/skills/salesforce-<domain>/references/skill-index.md`), because on a
fresh install skill selection is Claude reading those glosses — `vector_index/`
is gitignored and never ships. It is a WARN here rather than an ERROR because
a genuinely unambiguous skill does not need one.

This check has been run to completion. Measured 2026-08-14 it was 181 of 1,027;
a description wave took that to 1,010, and the last 17 (16 whose clause named a
real package but omitted its `domain/` prefix, plus one that said "Does NOT
cover" — which this file's own NOTFOR_RE does not match) were repaired on
2026-08-15. Every authored package now names a resolvable destination.

So a non-zero count here is now a REGRESSION signal rather than a backlog:
something new landed without a redirect, or a rename orphaned an existing one.
Treat it that way. The one shape this check still cannot see is a redirect that
resolves and is nevertheless wrong — `security/sso-saml-troubleshooting` pointed
at `admin/connected-apps-and-auth`, a real package about OAuth for integrations
rather than about configuring SSO. Resolving is a syntax gate, not a routing
guarantee.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FRONTMATTER = [
    "name", "description", "category", "salesforce-version",
    "well-architected-pillars", "tags", "inputs", "outputs",
    "dependencies", "version", "author", "updated",
]
REFERENCE_FILES = ["examples.md", "gotchas.md", "well-architected.md", "llm-anti-patterns.md"]

TODO_RE = re.compile(r"\bTODO\b|<placeholder>|FIXME", re.IGNORECASE)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
NOTFOR_RE = re.compile(r"NOT for", re.IGNORECASE)
USE_TARGET_RE = re.compile(
    r"use\s+(?:the\s+)?`?([a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]*)`?", re.IGNORECASE
)
WORKFLOW_STEP_RE = re.compile(r"^\s*\d+\.\s+\S", re.MULTILINE)


def _count_anti_patterns(text: str) -> int:
    """Entries in an llm-anti-patterns.md, counting BOTH house styles.

    Two shapes ship in this corpus and both are correct:
      * `## Anti-Pattern 3: …` section headings (the long form), and
      * a flat top-level numbered list (the compact form, e.g.
        agentforce/agent-action-error-handling, which holds exactly five).
    Counting only headings reported the compact files as having ZERO entries
    and would have sent someone to "fix" five perfectly good anti-patterns.
    """
    headings = len(re.findall(r"^##+\s+\S", text, re.MULTILINE))
    numbered = len(re.findall(r"^\s{0,3}\d+\.\s+\S", text, re.MULTILINE))
    return max(headings, numbered)


@dataclass
class Check:
    name: str
    ok: bool
    level: str            # "ERROR" | "WARN"
    why: str              # what is wrong
    action: str           # what to do about it
    weight: int = 1


@dataclass
class Report:
    skill: str
    exists: bool
    checks: list[Check] = field(default_factory=list)

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.ok]

    @property
    def blocking(self) -> list[Check]:
        return [c for c in self.failures if c.level == "ERROR"]

    @property
    def score(self) -> int:
        done = sum(c.weight for c in self.checks if c.ok)
        total = sum(c.weight for c in self.checks) or 1
        return round(100 * done / total)

    def next_action(self) -> str | None:
        for c in self.blocking:
            return c.action
        for c in self.failures:
            return c.action
        return None


def _load_registry() -> dict[str, dict]:
    path = ROOT / "registry" / "skills.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    recs = data["skills"] if isinstance(data, dict) and "skills" in data else data
    if isinstance(recs, dict):
        recs = list(recs.values())
    return {r["id"]: r for r in recs if isinstance(r, dict) and r.get("id")}


def _all_skill_ids() -> set[str]:
    skills = ROOT / "skills"
    if not skills.is_dir():
        return set()
    return {
        f"{dom.name}/{d.name}"
        for dom in skills.iterdir() if dom.is_dir()
        for d in dom.iterdir() if (d / "SKILL.md").is_file()
    }


def _agent_citations() -> set[str]:
    cited: set[str] = set()
    pat = re.compile(r"(?:^|[\s`(\[])\.?/?skills/([a-z0-9-]+/[a-z0-9-]+)")
    for agent in (ROOT / "agents").glob("*/AGENT.md"):
        text = agent.read_text(encoding="utf-8", errors="ignore")
        cited.update(pat.findall(text))
        m = FRONTMATTER_RE.match(text)
        if m:
            for line in m.group(1).splitlines():
                s = line.strip()
                if s.startswith("- ") and "/" in s:
                    cited.add(s[2:].strip().strip("`"))
    return cited


def _fixture_skills() -> set[str]:
    path = ROOT / "vector_index" / "query-fixtures.json"
    if not path.is_file():
        return set()
    return {q["expected_skill"] for q in json.loads(path.read_text())["queries"]}


def diagnose(skill_id: str, *, registry: dict, cited: set[str],
             fixtures: set[str], real: set[str]) -> Report:
    pkg = ROOT / "skills" / skill_id
    rep = Report(skill=skill_id, exists=(pkg / "SKILL.md").is_file())
    if not rep.exists:
        rep.checks.append(Check(
            "exists", False, "ERROR",
            f"no skills/{skill_id}/SKILL.md",
            f"python3 scripts/new_skill.py {skill_id.replace('/', ' ', 1)} --strict",
        ))
        return rep

    skill_md = (pkg / "SKILL.md").read_text(encoding="utf-8", errors="ignore")
    m = FRONTMATTER_RE.match(skill_md)
    front_raw = m.group(1) if m else ""
    body = skill_md[m.end():] if m else skill_md

    # --- frontmatter ---------------------------------------------------
    missing = [k for k in REQUIRED_FRONTMATTER if not re.search(rf"^{re.escape(k)}:", front_raw, re.M)]
    rep.checks.append(Check(
        "frontmatter", not missing, "ERROR",
        f"missing key(s): {', '.join(missing)}" if missing else "",
        f"open skills/{skill_id}/SKILL.md and add: {', '.join(missing)}",
        weight=2,
    ))

    desc_m = re.search(r"^description:\s*(.+)$", front_raw, re.M)
    desc = (desc_m.group(1).strip().strip('"') if desc_m else "")

    # --- routing: the shipped-gloss lever ------------------------------
    has_notfor = bool(NOTFOR_RE.search(desc))
    target = ""
    for cand in USE_TARGET_RE.findall(desc):
        if cand in real:
            target = cand
            break
    rep.checks.append(Check(
        "routing", bool(has_notfor and target), "WARN",
        ("description has no `NOT for …` clause" if not has_notfor
         else "the `NOT for …` clause names no package that exists, so a misrouted reader has nowhere to go"),
        (f"edit the description in skills/{skill_id}/SKILL.md so it ends with "
         f"`NOT for <the adjacent topic> — use <domain>/<real-slug>`. This clause is "
         f"the highest-value token in the shipped roster gloss, and it is what "
         f"disambiguates this package from its neighbours."),
        weight=2,
    ))

    # --- triggers -------------------------------------------------------
    trig = re.search(r"^triggers:\s*\n((?:\s*-\s*.+\n)+)", front_raw + "\n", re.M)
    n_trig = len(re.findall(r"^\s*-\s+\S", trig.group(1), re.M)) if trig else 0
    rep.checks.append(Check(
        "triggers", n_trig >= 3, "WARN",
        f"{n_trig} trigger phrase(s); 3+ natural-language symptom phrasings expected",
        f"add trigger phrases to skills/{skill_id}/SKILL.md — write what a user TYPES, "
        f"verb-first ('my flow keeps hitting the SOQL limit'), not the topic name",
    ))

    # --- recommended workflow -------------------------------------------
    wf = re.search(r"##\s+Recommended Workflow(.*?)(?=\n##\s|\Z)", body, re.S)
    n_steps = len(WORKFLOW_STEP_RE.findall(wf.group(1))) if wf else 0
    rep.checks.append(Check(
        "workflow", 3 <= n_steps <= 7, "ERROR",
        (f"`## Recommended Workflow` has {n_steps} numbered step(s); the standard is 3-7"
         if wf else "no `## Recommended Workflow` section"),
        f"add a 3-7 step `## Recommended Workflow` to skills/{skill_id}/SKILL.md",
    ))

    # --- reference files -------------------------------------------------
    refs = pkg / "references"
    missing_refs = [f for f in REFERENCE_FILES if not (refs / f).is_file()]
    rep.checks.append(Check(
        "reference-files", not missing_refs, "ERROR",
        f"missing references/: {', '.join(missing_refs)}" if missing_refs else "",
        f"create skills/{skill_id}/references/{missing_refs[0] if missing_refs else ''}",
    ))

    # --- TODO placeholders ------------------------------------------------
    todo_files = []
    for f in [pkg / "SKILL.md", *(refs / r for r in REFERENCE_FILES)]:
        if f.is_file() and TODO_RE.search(f.read_text(encoding="utf-8", errors="ignore")):
            todo_files.append(f.relative_to(ROOT).as_posix())
    rep.checks.append(Check(
        "no-placeholders", not todo_files, "ERROR",
        f"{len(todo_files)} file(s) still hold TODO/placeholder text" if todo_files else "",
        f"fill the placeholders in {todo_files[0] if todo_files else ''}",
        weight=2,
    ))

    # --- llm-anti-patterns depth -------------------------------------------
    ap = refs / "llm-anti-patterns.md"
    n_ap = _count_anti_patterns(ap.read_text(encoding="utf-8", errors="ignore")) if ap.is_file() else 0
    rep.checks.append(Check(
        "anti-patterns", n_ap >= 5, "ERROR",
        f"llm-anti-patterns.md lists {n_ap} entr(ies); the standard is 5+",
        f"add {max(0, 5 - n_ap)} more entr(ies) to skills/{skill_id}/references/llm-anti-patterns.md "
        f"— each is a mistake an AI actually makes here, with the wrong output and the fix",
    ))

    # --- official sources ---------------------------------------------------
    wa = refs / "well-architected.md"
    has_sources = wa.is_file() and "## Official Sources Used" in wa.read_text(encoding="utf-8", errors="ignore")
    rep.checks.append(Check(
        "official-sources", has_sources, "ERROR",
        "no `## Official Sources Used` block in references/well-architected.md",
        f"add `## Official Sources Used` to skills/{skill_id}/references/well-architected.md "
        f"with the developer.salesforce.com pages that back this skill's claims",
    ))

    # --- retrieval fixture ---------------------------------------------------
    rep.checks.append(Check(
        "query-fixture", skill_id in fixtures, "ERROR",
        "no entry in vector_index/query-fixtures.json",
        f'add {{"query": "<what a user would type>", "domain": "{skill_id.split("/")[0]}", '
        f'"expected_skill": "{skill_id}", "top_k": 3}} to vector_index/query-fixtures.json',
    ))

    # --- agent wiring --------------------------------------------------------
    orphan_ok = "runtime_orphan: true" in front_raw
    rep.checks.append(Check(
        "agent-wiring", (skill_id in cited) or orphan_ok, "WARN",
        "no run-time agent cites this skill, and no `runtime_orphan: true` decision is recorded",
        f"either add `{skill_id}` to an agent's Mandatory Reads WITH a reason, or record the "
        f"decision in frontmatter: `runtime_orphan: true` + `runtime_orphan_reason: <why no agent owns this>`",
    ))

    # --- registry freshness ---------------------------------------------------
    rep.checks.append(Check(
        "synced", skill_id in registry, "ERROR",
        "not present in registry/skills.json — generated artifacts are stale",
        f"python3 scripts/skill_sync.py --skill skills/{skill_id}",
    ))

    return rep


def print_report(rep: Report, verbose: bool) -> None:
    bar = "#" * (rep.score // 10) + "." * (10 - rep.score // 10)
    print(f"\n  {rep.skill}   [{bar}] {rep.score}%")
    if not rep.failures:
        print("  ready — every gate this repo enforces passes.")
        return
    for c in rep.failures:
        tag = "BLOCK" if c.level == "ERROR" else " warn"
        print(f"    {tag}  {c.name:16s} {c.why}")
    if verbose:
        for c in (x for x in rep.checks if x.ok):
            print(f"       ok  {c.name}")
    nxt = rep.next_action()
    if nxt:
        print(f"\n  NEXT: {nxt}")


def _normalise_skill_arg(raw: str, real: set[str]) -> str:
    """Accept `domain/slug`, `skills/domain/slug`, or a path to either.

    Everything downstream joins the argument onto ``ROOT / "skills"``, so a
    path-form argument used to resolve to ``skills/skills/<domain>/<slug>`` and
    every check failed. That reported a real package as missing and told the
    caller to scaffold it — confidently wrong output, which is worse than an
    error. Normalise instead, and fail loudly when the id does not exist.
    """
    s = raw.strip()
    try:  # a path into this repo, absolute or relative — resolve before stripping
        s = str(Path(s).resolve().relative_to(ROOT))
    except (ValueError, OSError):
        pass
    s = s.strip("/")
    if s.startswith("skills/"):
        s = s[len("skills/"):]
    if s not in real:
        near = sorted(x for x in real if x.split("/")[-1] == s.split("/")[-1])
        hint = f"  Did you mean: {', '.join(near[:3])}" if near else \
               "  Use `domain/slug`, e.g. apex/trigger-framework. `--all` reports every skill."
        raise SystemExit(f"skill_doctor: no such skill '{raw}'\n{hint}")
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skill", nargs="?", help="domain/slug (omit with --all)")
    ap.add_argument("--all", action="store_true", help="report every unfinished skill, worst first")
    ap.add_argument("--new", action="store_true", help="with --all: only stub/placeholder packages")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    ap.add_argument("--verbose", "-v", action="store_true", help="also list passing checks")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    if not args.skill and not args.all:
        ap.error("give a skill id, or --all")

    registry, cited, fixtures, real = _load_registry(), _agent_citations(), _fixture_skills(), _all_skill_ids()
    targets = sorted(real) if args.all else [_normalise_skill_arg(args.skill, real)]
    reports = [diagnose(s, registry=registry, cited=cited, fixtures=fixtures, real=real) for s in targets]

    if args.json:
        print(json.dumps([{
            "skill": r.skill, "score": r.score, "next_action": r.next_action(),
            "failures": [{"check": c.name, "level": c.level, "why": c.why, "action": c.action}
                         for c in r.failures],
        } for r in reports], indent=1))
        return 1 if any(r.blocking for r in reports) else 0

    if args.all:
        unfinished = [r for r in reports if r.failures]
        if args.new:
            unfinished = [r for r in unfinished
                          if any(c.name == "no-placeholders" and not c.ok for c in r.checks)]
        unfinished.sort(key=lambda r: (r.score, -len(r.blocking)))
        blocked = sum(1 for r in reports if r.blocking)
        print(f"{len(reports)} skill(s): {len(reports) - len(unfinished)} complete, "
              f"{len(unfinished)} unfinished, {blocked} with blocking gaps.\n")
        for r in unfinished[:args.limit]:
            print_report(r, args.verbose)
        if len(unfinished) > args.limit:
            print(f"\n  … {len(unfinished) - args.limit} more (raise --limit)")
        return 1 if blocked else 0

    print_report(reports[0], args.verbose)
    return 1 if reports[0].blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
