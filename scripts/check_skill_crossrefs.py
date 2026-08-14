#!/usr/bin/env python3
"""Find cross-references to skills that do not exist.

A skill package routinely points at its neighbours — "see `apex/trigger-framework`",
"read `skills/flow/fault-handling` first". When the target was renamed or never
existed, the reference does not fail loudly. An agent told to read a nonexistent
skill either invents its contents or silently drops the step, and a human
follows a dead end. It is the same defect class `scripts/check_decision_trees.py`
ERRORs on for decision trees, one layer down.

MEASURED 2026-08-13: 251 distinct dead slugs across 357 occurrences in 182
containers. Almost all are skill-to-skill; `agents/`, `templates/` and `evals/`
carry one apiece, because the agent reading lists already have their own gates
(`_check_agent_citation_quality` and `check_agent_citation_parity.py`).

Most look like renames that were never chased down — `apex/scheduled-apex` for
`apex/apex-scheduled-jobs`, `lwc/lightning-message-service`,
`flow/flow-best-practices`.

NOT WIRED INTO validate_repo.py, deliberately. At 182 containers it would add
182 WARNs to a run that already emits ~786, drowning the signal before anyone
has decided to do the cleanup. Wire it once the backlog is worked down — the
collector function is here and ready.

FALSE POSITIVES THIS DELIBERATELY AVOIDS. `<domain>/<slug>` is also the shape of
a JavaScript module path, and OmniStudio skills legitimately write
`import pubsub from 'omnistudio/pubsub'`. Counting those inflated an earlier
measurement of this same problem from 251 to 292. Lines that look like imports
are skipped.

Usage:
    python3 scripts/check_skill_crossrefs.py              # grouped summary
    python3 scripts/check_skill_crossrefs.py --by-target  # worst dead slugs first
    python3 scripts/check_skill_crossrefs.py --json
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# `domain/slug` in backticks, or a bare skills/domain/slug path.
REF = re.compile(
    r"`([a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]*)`"
    r"|(?<![\w/])skills/([a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]*)"
)

# UNBACKTICKED references. Adding these closed a real blind spot: a cleanup wave
# found dead slugs sitting in `dependencies:` YAML lists and in plain-text
# "Related Skills" bullets, and reported them as "permanently invisible to
# check_skill_crossrefs.py" — which they were, because the pattern above needs
# backticks or a `skills/` prefix. Frontmatter is the canonical metadata source
# per CLAUDE.md, so a dead pointer there is worse than one in prose.
#
# `domain/slug` unbackticked is also the shape of a path, a ratio and a module
# import, so these are deliberately NARROW: the reference must either be a YAML
# list item, a markdown bullet, or follow an explicit "use"/"see" verb. The
# domain allowlist in collect_issues() then discards anything whose first
# segment is not a real skill domain.
# A skill reference must END there. The negative lookahead for `/` and `.` is
# load-bearing: without it the pattern backtracks to a PREFIX of a real path and
# invents dead slugs. A first draft reported `lwc/component` (from the templates
# entry `- lwc/component-skeleton/`), `lwc/jest` (from `- lwc/jest.config.js`)
# and `admin/naming-conventions` 18 times (from `- admin/naming-conventions.md`,
# a docs file) — 25 fabricated findings out of 57, none of them skills.
_END = r"(?![\w./-])"
UNBACKTICKED_REFS = [
    # A YAML list item or markdown bullet that is the WHOLE value:
    #   "    - admin/person-accounts"
    re.compile(rf"^\s*-\s+([a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]*){_END}\s*[-–—:,.]?\s*(?:\S.*)?$"),
    # An explicit verb: "use admin/sandbox-strategy", "see data/person-accounts"
    re.compile(rf"\b(?:use|see|read)\s+([a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]*){_END}", re.IGNORECASE),
]
# A line that is talking about code modules, not skills.
MODULE_LINE = re.compile(
    r"\bimport\b|\bfrom\s*['\"]|require\(|module|npm|package\.json|/pubsub|lwc:|c-[a-z]"
)
SEARCH_ROOTS = ["skills/", "agents/", "standards/", "docs/", "templates/", "evals/"]


def real_skills(root: Path) -> set[str]:
    skills = root / "skills"
    if not skills.is_dir():
        return set()
    return {
        f"{dom.name}/{d.name}"
        for dom in skills.iterdir() if dom.is_dir()
        for d in dom.iterdir() if (d / "SKILL.md").is_file()
    }


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", *SEARCH_ROOTS],
        cwd=root, capture_output=True, text=True,
    ).stdout.split()
    return [f for f in out if f.endswith((".md", ".yaml", ".yml"))]


def collect_issues(root: Path | None = None) -> list[dict]:
    base = (root or ROOT).resolve()
    skills = base / "skills"
    if not skills.is_dir():
        return []
    domains = {p.name for p in skills.iterdir() if p.is_dir()}
    real = real_skills(base)

    issues: list[dict] = []
    for rel in tracked_files(base):
        path = base / rel
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            if MODULE_LINE.search(line):
                continue
            found: list[str] = []
            for m in REF.finditer(line):
                found.append(m.group(1) or m.group(2))
            for pat in UNBACKTICKED_REFS:
                found.extend(pat.findall(line))
            seen_on_line: set[str] = set()
            for ref in found:
                if not ref or ref in seen_on_line:
                    continue
                seen_on_line.add(ref)
                if ref.split("/", 1)[0] not in domains or ref in real:
                    continue
                issues.append({
                    "level": "WARN",
                    "file": rel,
                    "line": line_no,
                    "target": ref,
                    "kind": "dead-skill-reference",
                    "message": (
                        f"references `{ref}`, which has no skills/{ref}/SKILL.md. "
                        f"An agent told to read it will invent its contents or drop "
                        f"the step."
                    ),
                })
    return issues


def collect_crossref_issues(root: Path) -> list[tuple[str, str, str]]:
    """(level, path, message) triples, matching validate_repo's ValidationIssue."""
    return [(i["level"], f"{i['file']}:{i['line']}", f"[{i['kind']}] {i['message']}")
            for i in collect_issues(root)]


def container_of(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] == "skills" and len(parts) >= 3:
        return f"{parts[1]}/{parts[2]}"
    return "/".join(parts[:2])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--by-target", action="store_true",
                    help="group by dead slug instead of by container")
    ap.add_argument("--limit", type=int, default=25, help="rows to print (default 25)")
    args = ap.parse_args()

    issues = collect_issues()
    if args.json:
        print(json.dumps(issues, indent=1))
        return 0

    targets = collections.Counter(i["target"] for i in issues)
    containers = collections.defaultdict(set)
    for i in issues:
        containers[container_of(i["file"])].add(i["target"])

    print(f"{len(targets)} distinct dead skill reference(s), "
          f"{len(issues)} occurrence(s), across {len(containers)} container(s).\n")

    if args.by_target:
        print("Worst dead slugs (a rename chased down once fixes every row):")
        for target, count in targets.most_common(args.limit):
            example = next(i for i in issues if i["target"] == target)
            print(f"  {count:3d}x  {target:52s} e.g. {example['file']}:{example['line']}")
    else:
        print("Worst containers:")
        for name, refs in sorted(containers.items(), key=lambda kv: -len(kv[1]))[:args.limit]:
            print(f"  {len(refs):2d}  {name}")
            for r in sorted(refs)[:4]:
                print(f"        -> {r}")

    print("\nAdvisory only — this script is not wired into validate_repo.py. "
          "See the module docstring for why.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
