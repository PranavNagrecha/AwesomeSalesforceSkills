#!/usr/bin/env python3
"""score_skill_depth.py — rank skills by how far they are from the agentic-coding bar.

Deterministic, no model calls, stdlib only. Scores each skill package on the
signals the 2026-09-04 depth standard cares about (see
standards/skill-authoring-style.md § 3.7 and CLAUDE.md "Skill Package Standard"):

    questions   `## Questions to Ask` block present in SKILL.md
    workflow    Recommended Workflow is skill-specific (not the scaffold boilerplate)
    artifact    a deployable artifact fence exists (xml / apex / js / soql / json / yaml / bash)
    xml         a metadata XML fence exists (admin bar) — informational for other domains
    gotchas     >= 5 gotcha headings in references/gotchas.md
    antipat     >= 5 anti-pattern headings in references/llm-anti-patterns.md
    sources     >= 4 bullets under `## Official Sources Used`
    checker     scripts/check_*.py is not the scaffold stub
    examples    references/examples.md is not the scaffold stub
    todos       zero `TODO` markers across the package
    triggers    >= 5 natural-language triggers in frontmatter
    extras      at least one reference file beyond the four required ones

Each signal is worth one point (max 12). The report lists the lowest scores
first — that is the worklist.

Usage:
    python3 scripts/score_skill_depth.py                       # summary by domain
    python3 scripts/score_skill_depth.py --domain admin        # ranked worklist
    python3 scripts/score_skill_depth.py --domain admin --csv out.csv
    python3 scripts/score_skill_depth.py --out docs/reports/skill-depth.md
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
REQUIRED_REFS = {"examples.md", "gotchas.md", "well-architected.md", "llm-anti-patterns.md"}
ARTIFACT_LANGS = {"xml", "apex", "java", "javascript", "js", "soql", "sql", "json", "yaml", "yml", "bash", "sh", "html", "css", "python"}
BOILERPLATE_WORKFLOW = "Gather context — confirm the org edition"
CHECKER_STUB = "TODO: Implement real checks"
FENCE_RE = re.compile(r"```([A-Za-z0-9_-]*)\n")
SIGNALS = ["questions", "workflow", "artifact", "xml", "gotchas", "antipat", "sources", "checker", "examples", "todos", "triggers", "extras"]


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _fences(text: str) -> Counter:
    return Counter(m.group(1).lower() for m in FENCE_RE.finditer(text))


def _headings(text: str, prefix: str) -> int:
    return sum(1 for ln in text.splitlines() if ln.startswith("## ") and prefix.lower() in ln.lower())


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def score_skill(skill_dir: Path) -> dict:
    skill_md = _read(skill_dir / "SKILL.md")
    fm = _frontmatter(skill_md)
    refs_dir = skill_dir / "references"
    ref_files = {p.name for p in refs_dir.glob("*.md")} if refs_dir.exists() else set()
    ref_texts = {p.name: _read(p) for p in refs_dir.glob("*.md")} if refs_dir.exists() else {}
    all_text = skill_md + "".join(ref_texts.values())
    fences = _fences(all_text)
    scripts = list((skill_dir / "scripts").glob("*.py")) if (skill_dir / "scripts").exists() else []
    script_text = "".join(_read(p) for p in scripts)
    templates = list((skill_dir / "templates").glob("*")) if (skill_dir / "templates").exists() else []
    template_text = "".join(_read(p) for p in templates if p.is_file())

    triggers = re.findall(r'^\s*-\s*"(.*)"\s*$', fm[fm.find("triggers:"):] if "triggers:" in fm else "", re.M)
    # stop at the next top-level key
    if "triggers:" in fm:
        block = fm[fm.find("triggers:"):]
        nxt = re.search(r"\n[a-z][a-z-]*:", block[9:])
        block = block[: nxt.start() + 9] if nxt else block
        triggers = re.findall(r'^\s*-\s*"(.*)"\s*$', block, re.M)

    sources_block = ""
    wa = ref_texts.get("well-architected.md", "")
    if "## Official Sources Used" in wa:
        sources_block = wa[wa.index("## Official Sources Used"):]
    sources = sum(1 for ln in sources_block.splitlines() if ln.lstrip().startswith("- "))

    todo_count = len(re.findall(r"\bTODO\b", all_text + script_text + template_text))
    sig = {
        "questions": "## Questions to Ask" in skill_md,
        "workflow": "## Recommended Workflow" in skill_md and BOILERPLATE_WORKFLOW not in skill_md,
        "artifact": any(lang in ARTIFACT_LANGS for lang in fences),
        "xml": fences.get("xml", 0) > 0,
        "gotchas": _headings(ref_texts.get("gotchas.md", ""), "gotcha") >= 5 or _headings(ref_texts.get("gotchas.md", ""), "") >= 5,
        "antipat": _headings(ref_texts.get("llm-anti-patterns.md", ""), "anti-pattern") >= 5,
        "sources": sources >= 4,
        "checker": bool(scripts) and CHECKER_STUB not in script_text,
        "examples": "examples.md" in ref_texts and "TODO" not in ref_texts["examples.md"],
        "todos": todo_count == 0,
        "triggers": len(triggers) >= 5,
        "extras": len(ref_files - REQUIRED_REFS) >= 1,
    }
    m_ver = re.search(r"^version:\s*([\d.]+)", fm, re.M)
    m_upd = re.search(r"^updated:\s*[\"']?(\d{4}-\d{2}-\d{2})", fm, re.M)
    tags = re.findall(r"^\s*-\s*([a-z0-9-]+)\s*$", fm[fm.find("tags:"):fm.find("inputs:")] if "tags:" in fm and "inputs:" in fm else "", re.M)
    return {
        "skill": f"{skill_dir.parent.name}/{skill_dir.name}",
        "domain": skill_dir.parent.name,
        "score": sum(sig.values()),
        **sig,
        "gotcha_n": _headings(ref_texts.get("gotchas.md", ""), ""),
        "sources_n": sources,
        "trigger_n": len(triggers),
        "todo_n": todo_count,
        "lines": skill_md.count("\n"),
        "version": m_ver.group(1) if m_ver else "",
        "updated": m_upd.group(1) if m_upd else "",
        "tags": " ".join(tags[:6]),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", help="restrict to one domain")
    ap.add_argument("--csv", help="write the full table to this CSV path")
    ap.add_argument("--out", help="write a markdown report to this path")
    ap.add_argument("--top", type=int, default=40, help="rows to print in the ranked worklist")
    args = ap.parse_args()

    rows = []
    for domain_dir in sorted(SKILLS.iterdir()):
        if not domain_dir.is_dir() or (args.domain and domain_dir.name != args.domain):
            continue
        for skill_dir in sorted(domain_dir.iterdir()):
            if (skill_dir / "SKILL.md").exists():
                rows.append(score_skill(skill_dir))
    if not rows:
        print("no skills found", file=sys.stderr)
        return 1

    by_domain: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_domain[r["domain"]].append(r)

    lines = ["# Skill depth scores", "", f"{len(rows)} skills scored on {len(SIGNALS)} signals (see scripts/score_skill_depth.py). Lowest first = worklist.", ""]
    lines.append("| domain | skills | mean | at bar (>=10) | questions | workflow | artifact | xml | gotchas | antipat | sources | checker | examples | todos | triggers | extras |")
    lines.append("|---|---:|---:|---:|" + "---:|" * len(SIGNALS))
    for d, rs in sorted(by_domain.items()):
        mean = sum(r["score"] for r in rs) / len(rs)
        at_bar = sum(1 for r in rs if r["score"] >= 10)
        pct = [f"{100 * sum(1 for r in rs if r[s]) / len(rs):.0f}%" for s in SIGNALS]
        lines.append(f"| {d} | {len(rs)} | {mean:.1f} | {at_bar} | " + " | ".join(pct) + " |")
    lines.append("")

    ranked = sorted(rows, key=lambda r: (r["score"], r["skill"]))
    lines.append(f"## Ranked worklist (lowest {args.top})")
    lines.append("")
    lines.append("| score | skill | missing | gotchas | sources | triggers | todos | tags |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---|")
    for r in ranked[: args.top]:
        missing = ",".join(s for s in SIGNALS if not r[s])
        lines.append(f"| {r['score']} | {r['skill']} | {missing} | {r['gotcha_n']} | {r['sources_n']} | {r['trigger_n']} | {r['todo_n']} | {r['tags']} |")
    report = "\n".join(lines) + "\n"

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(report)
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(ranked)
        print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
