#!/usr/bin/env python3
"""verify_skill_package.py — reviewer's checks on one or more skill packages.

Runs the mechanical part of a depth review so the human/reviewer can spend
attention on truth, not shape:

  * every ```xml fence in SKILL.md and references/*.md is well-formed
  * every ```apex / ```java fence has balanced braces (cheap syntax smoke test)
  * no TODO markers anywhere in the package
  * `## Questions to Ask` present; Recommended Workflow is not scaffold boilerplate
  * every `domain/slug` under `## Related Skills` resolves to a real SKILL.md
  * every `references/<file>.md` mentioned in SKILL.md exists, and every
    references/*.md is mentioned in SKILL.md (Reference Files table)
  * UNVERIFIED markers are listed (they are allowed; the reviewer reads them)
  * `## Official Sources Used` bullet count and `updated:` date
  * depth score from scripts/score_skill_depth.py

Exit 1 on any hard failure (bad XML, TODO, unresolved slug, missing file).

Usage:
    python3 scripts/verify_skill_package.py skills/admin/validation-rules [more...]
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from score_skill_depth import score_skill, SIGNALS, BOILERPLATE_WORKFLOW  # noqa: E402

FENCE_RE = re.compile(r"```([A-Za-z0-9_-]*)\n(.*?)```", re.S)



def _strip_apex(src: str) -> str:
    """Blank string literals and comments in one left-to-right pass so that a '/*'
    inside a string (e.g. urlMapping='/v1/cases/*') never opens a phantom comment
    and an apostrophe inside a comment never opens a phantom string."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            i = j + 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)

def verify(skill_dir: Path) -> tuple[list[str], list[str]]:
    hard: list[str] = []
    info: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir}: no SKILL.md"], info
    files = [skill_md] + sorted((skill_dir / "references").glob("*.md"))
    texts = {p: p.read_text(encoding="utf-8") for p in files}

    # fences
    for p, t in texts.items():
        for m in FENCE_RE.finditer(t):
            lang, body = m.group(1).lower(), m.group(2)
            if lang == "xml":
                try:
                    ET.fromstring(body.encode("utf-8"))
                except ET.ParseError as exc:
                    hard.append(f"{p.relative_to(ROOT)}: malformed XML fence — {exc}")
            elif lang in ("apex", "java"):
                # braces inside string literals (e.g. Mermaid connectors '||--o{') are not code braces
                code = _strip_apex(body)  # single pass: strings, // and /* */ removed in source order
                if code.count("{") != code.count("}"):
                    # a labelled excerpt (the 300 chars before the fence say "excerpt") is allowed
                    lead = t[max(0, m.start() - 300):m.start()].lower()
                    if "excerpt" in lead or "excerpt" in body[:200].lower():
                        info.append(f"{p.relative_to(ROOT)}: {lang} excerpt with unbalanced braces (labelled, allowed)")
                    else:
                        hard.append(f"{p.relative_to(ROOT)}: unbalanced braces in {lang} fence")

    # TODOs across the package
    for p in skill_dir.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".xml", ".cls", ".txt", ".json", ".yaml", ".yml"):
            t = p.read_text(encoding="utf-8", errors="ignore")
            n = len(re.findall(r"\bTODO\b", t))
            if n:
                hard.append(f"{p.relative_to(ROOT)}: {n} TODO marker(s)")

    s = texts[skill_md]
    if "## Questions to Ask" not in s:
        hard.append(f"{skill_md.relative_to(ROOT)}: no `## Questions to Ask` section")
    if BOILERPLATE_WORKFLOW in s:
        hard.append(f"{skill_md.relative_to(ROOT)}: Recommended Workflow is still scaffold boilerplate")
    if "## When To Use" in s:
        hard.append(f"{skill_md.relative_to(ROOT)}: forbidden `## When To Use` heading")

    # related skills resolve
    rel = s[s.find("## Related Skills"):] if "## Related Skills" in s else ""
    # `templates/admin/x.md` is a shared template path, not a skill slug
    for slug in re.findall(r"(?<!templates/)(?<!/)`?\b(admin|apex|lwc|flow|omnistudio|agentforce|security|integration|data|devops|architect)/([a-z0-9-]+)`?", rel):
        if not (ROOT / "skills" / slug[0] / slug[1] / "SKILL.md").exists():
            hard.append(f"{skill_md.relative_to(ROOT)}: Related Skills cites missing skill {slug[0]}/{slug[1]}")

    # reference files mentioned <-> exist
    refs_dir = skill_dir / "references"
    existing = {p.name for p in refs_dir.glob("*.md")} if refs_dir.exists() else set()
    # a `references/x.md` mention counts as local only when the same line does not
    # name another skill (cross-skill pointers like "`admin/queues` … its references/x.md")
    this_slug = f"{skill_dir.parent.name}/{skill_dir.name}"
    mentioned: set[str] = set()
    for ln in s.splitlines():
        others = [m for m in re.findall(r"\b(?:admin|apex|lwc|flow|omnistudio|agentforce|security|integration|data|devops|architect)/[a-z0-9-]+", ln) if m != this_slug]
        if others:
            continue
        mentioned.update(re.findall(r"references/([A-Za-z0-9_.-]+\.md)", ln))
    for m in mentioned - existing:
        hard.append(f"{skill_md.relative_to(ROOT)}: mentions references/{m} which does not exist")
    for e in sorted(existing - mentioned - {"well-architected.md", "llm-anti-patterns.md", "examples.md", "gotchas.md"}):
        info.append(f"{skill_md.relative_to(ROOT)}: references/{e} exists but SKILL.md never points at it")

    # unverified markers
    for p, t in texts.items():
        for ln_no, ln in enumerate(t.splitlines(), 1):
            if "UNVERIFIED" in ln:
                info.append(f"UNVERIFIED {p.relative_to(ROOT)}:{ln_no}: {ln.strip()[:140]}")

    # sources / updated / score
    r = score_skill(skill_dir)
    missing = [k for k in SIGNALS if not r[k]]
    info.append(f"score {r['score']}/12 (missing: {', '.join(missing) or 'none'}); gotchas {r['gotcha_n']}; sources {r['sources_n']}; triggers {r['trigger_n']}; updated {r['updated']}; version {r['version']}")
    return hard, info


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rc = 0
    for arg in sys.argv[1:]:
        d = (ROOT / arg) if not Path(arg).is_absolute() else Path(arg)
        hard, info = verify(d)
        print(f"=== {arg}")
        for h in hard:
            print(f"FAIL {h}")
        for i in info:
            print(f"     {i}")
        if hard:
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
