#!/usr/bin/env python3
"""Validate the cross-skill decision trees under standards/decision-trees/.

Why this gate exists, and why it runs on EVERY pass rather than
``--changed-only``: `standards/decision-trees/README.md` instructs run-time
agents to consult a tree BEFORE activating any skill and to cite the branch
that resolved the choice. A tree therefore sits upstream of every skill it
routes to, and a defect in one overrides correct skill content inside the
agent's context window. It also means a tree can BREAK WITHOUT THE TREE FILE
CHANGING -- renaming or deleting a skill silently turns a live branch into a
dead citation -- so the tree files being unmodified is not evidence they are
still correct.

Two ERROR classes, both found live in this repo before the gate existed:

1. UNRESOLVABLE SKILL REFERENCE. `automation-selection.md` routed to
   `flow/record-triggered-flows` and `agentforce/agent-creation`, neither of
   which exists. An agent told to read a nonexistent skill either invents its
   contents or silently drops the step.

2. UNREACHABLE QUESTION. `flow-pattern-selector.md` had 4 of its 9 questions
   unreachable, including the entire scheduled-path timing decision -- the tree
   looked complete and simply could not deliver those answers. This was the
   DOMINANT tree defect, more common than wrong facts.

Deliberately NOT checked, because over-flagging is the failure mode here:
prose accuracy, whether a recommendation is good, or numbers in tables. Those
need a human or a doc fetch; this gate only enforces what is mechanically
decidable.

Usage:
    python3 scripts/check_decision_trees.py            # human-readable
    python3 scripts/check_decision_trees.py --json     # machine-readable
Exit code 1 if any ERROR is found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREES = ROOT / "standards" / "decision-trees"
SKILLS = ROOT / "skills"

# `domain/slug` in backticks, or a bare skills/domain/slug path.
SKILL_REF = re.compile(r"`(?P<a>[a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]*)`|(?<![\w/])skills/(?P<b>[a-z][a-z0-9-]*/[a-z0-9][a-z0-9-]*)")

# A question label at the start of a line inside the tree block: "Q3." / "Q3:"
QUESTION_DEF = re.compile(r"^\s*(Q\d+)\s*[.:]")
# A routing target anywhere on a line: "-> Q5" / "→ Q5" / "(go to Q5)"
QUESTION_REF = re.compile(r"(?:->|→|goto|go to|see)\s*\(?\s*(Q\d+)", re.IGNORECASE)

# Domains that exist as directories under skills/. Anything matching the
# `x/y` shape whose first segment is NOT one of these is not a skill reference
# at all (it is a path, a ratio, a date, an and/or pair) and is ignored.
DOMAINS = {p.name for p in SKILLS.iterdir() if p.is_dir()} if SKILLS.is_dir() else set()


def code_blocks(text: str) -> list[str]:
    """Return the contents of every fenced code block."""
    return re.findall(r"```[^\n]*\n(.*?)```", text, re.DOTALL)


def check_tree(path: Path, base: Path | None = None) -> list[dict]:
    """Check one tree. ``base`` is the repo root; defaults to this checkout.

    Both are resolved before use — a caller passing a relative root (``Path(".")``)
    would otherwise blow up in ``relative_to``.
    """
    base = (base or ROOT).resolve()
    path = path.resolve()
    skills_dir = base / "skills"
    domains = {p.name for p in skills_dir.iterdir() if p.is_dir()} if skills_dir.is_dir() else set()

    issues: list[dict] = []
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(base)

    # --- 1. skill references resolve -------------------------------------
    seen: set[str] = set()
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in SKILL_REF.finditer(line):
            ref = m.group("a") or m.group("b")
            if not ref or ref in seen:
                continue
            domain = ref.split("/", 1)[0]
            if domain not in domains:
                continue  # not a skill reference
            seen.add(ref)
            if not (skills_dir / ref / "SKILL.md").is_file():
                issues.append({
                    "level": "ERROR",
                    "file": str(rel),
                    "line": line_no,
                    "kind": "unresolvable-skill-reference",
                    "message": (
                        f"tree routes to `{ref}`, which has no "
                        f"skills/{ref}/SKILL.md. An agent told to read it will "
                        f"either invent its contents or drop the step."
                    ),
                })

    # --- 2. question routing ---------------------------------------------
    # Reachability is a property of the WHOLE FILE, not of one fenced block.
    # Every tree here splits its questions across several blocks
    # (performance-tuning.md uses eleven) and routes ACROSS the boundaries, so
    # analysing a block in isolation reports almost every question as
    # unreachable. That was this gate's own first bug.
    defined: dict[str, int] = {}
    targeted: set[str] = set()
    for block in code_blocks(text):
        for line in block.splitlines():
            m = QUESTION_DEF.match(line)
            if m and m.group(1) not in defined:
                defined[m.group(1)] = 0
            # A question's own definition line does not make it reachable.
            body = line[m.end():] if m else line
            targeted.update(t.upper() for t in QUESTION_REF.findall(body))

    # --- 3. every routing target exists -----------------------------------
    # Unambiguous in every tree shape: a branch that names a question the file
    # never defines is a dead end regardless of how the tree is organised.
    for q in sorted(targeted, key=lambda x: int(x[1:])):
        if q not in defined:
            issues.append({
                "level": "ERROR",
                "file": str(rel),
                "line": None,
                "kind": "dangling-branch-target",
                "message": f"a branch routes to {q}, which this file never defines.",
            })

    # --- 4. every defined question is reachable ---------------------------
    # Only meaningful for a tree that actually ROUTES. Two shapes live in this
    # directory and only one has reachability at all:
    #   * routed      -- flow-pattern-selector.md: Q1 -> Q2 -> ... Every
    #                    question is arrived at from a branch, so one that is
    #                    never targeted is dead. This shape previously shipped
    #                    with 4 of 9 questions unreachable.
    #   * checklist   -- integration-pattern-selection.md: "Authentication?",
    #                    "Payload shape?", "Rate limiting?" are independent
    #                    dimensions answered in sequence, with no arrows
    #                    between them. Nothing is unreachable; the concept does
    #                    not apply.
    # A simple majority separates them: a routed tree arrives at most of its
    # own questions by branch, a checklist at none of them. Do NOT tighten this
    # to "nearly all" -- that was tried, and it made the check disable itself
    # on exactly the input it exists to catch, since breaking one arrow also
    # drops the ratio.
    #
    # This one is a WARN, not an ERROR, and the demotion is deliberate. Trees
    # here mix routed branches with SEQUENTIAL questions that are reached by
    # reading on rather than by an arrow, and nothing mechanical separates the
    # two. Both flagged cases in performance-tuning.md are of that kind: Q9 is
    # literally "After picking the skill above, also open:", a follow-on to Q8,
    # and Q10-Q11 sit under one shared "## Q10-Q11" heading. Neither is dead.
    # An ERROR here would fire on correct trees, and a gate that fires on
    # correct input gets disabled rather than obeyed. Treat a WARN as "read
    # this question and confirm a reader can arrive at it".
    if len(defined) >= 2 and len(targeted & set(defined)) >= len(defined) / 2:
        entry = min(defined, key=lambda q: int(q[1:]))
        for q in sorted(defined, key=lambda x: int(x[1:])):
            if q == entry or q in targeted:
                continue
            issues.append({
                "level": "WARN",
                "file": str(rel),
                "line": None,
                "kind": "unreachable-question",
                "message": (
                    f"{q} is defined but no branch routes to it. Confirm a reader "
                    f"arrives there by reading on; if not, it is a dead branch."
                ),
            })

    return issues


def collect_issues(root: Path | None = None) -> list[dict]:
    """Every decision-tree issue, newest-caller-friendly. Used by validate_repo."""
    base = (root or ROOT).resolve()
    trees_dir = base / "standards" / "decision-trees"
    if not trees_dir.is_dir():
        return []
    issues: list[dict] = []
    for path in sorted(p for p in trees_dir.glob("*.md") if p.name != "README.md"):
        issues.extend(check_tree(path, base))
    return issues


def collect_decision_tree_issues(root: Path) -> list[tuple[str, str, str]]:
    """(level, path, message) triples, matching validate_repo's ValidationIssue."""
    return [
        (i["level"],
         f"{i['file']}:{i['line']}" if i["line"] else i["file"],
         f"[{i['kind']}] {i['message']}")
        for i in collect_issues(root)
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    if not TREES.is_dir():
        print(f"no decision-tree directory at {TREES}", file=sys.stderr)
        return 0

    trees = sorted(p for p in TREES.glob("*.md") if p.name != "README.md")
    issues = collect_issues()

    errors = [i for i in issues if i["level"] == "ERROR"]
    warns = [i for i in issues if i["level"] == "WARN"]

    if args.json:
        print(json.dumps(issues, indent=1))
    else:
        for i in issues:
            loc = f"{i['file']}:{i['line']}" if i["line"] else i["file"]
            print(f"{i['level']} {loc}: [{i['kind']}] {i['message']}")
        print(f"\nChecked {len(trees)} decision tree(s); "
              f"{len(errors)} error(s), {len(warns)} warning(s).")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
