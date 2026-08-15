#!/usr/bin/env python3
"""Does a term reach the surface that actually routes?

The recurring failure this guards against: a content wave rewrites skill
bodies, the repo looks updated, and the shipped roster never changes. Only
`.claude/skills/salesforce-<domain>/references/skill-index.md` ships — a
GitHub-sourced install has no FTS5 index and no embeddings (`vector_index/`
is gitignored), so a package body is invisible to routing until its *gloss*
carries the vocabulary.

`build_gloss()` ranks triggers > NOT-for redirect > lead, and glosses run at
the 220-char cap, so a term added to the lead is exactly the thing that gets
clipped. That is silent: nothing errors, the wave "succeeded", and the term
reaches zero users.

    python3 scripts/check_gloss_coverage.py subagent --domain agentforce

Reports packages that mention the term in their body or description but not
in the gloss. Exit 1 if any are found, so it can gate a wave.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_plugin as bp  # noqa: E402  (needs the path insert above)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("term", help="Vocabulary to look for, case-insensitive.")
    p.add_argument("--domain", help="Restrict to one domain, e.g. agentforce.")
    p.add_argument("--json", action="store_true", help="Machine-readable output.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    term = args.term.lower()

    payload = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))
    records = payload["skills"] if isinstance(payload, dict) else payload

    rows = []
    for rec in records:
        sid = str(rec.get("id") or "")
        if "/" not in sid:
            continue
        domain = sid.split("/", 1)[0]
        if args.domain and domain != args.domain:
            continue

        description = rec.get("description", "") or ""
        gloss = bp.build_gloss(description)
        # Split so lead prose is not mistaken for routing intent. "topic (now
        # subagent) design impact on cost" in the lead is a clarification the
        # author wrote for a reader; only the `Triggers:` clause is a claim
        # about what phrasings should land here.
        lead, triggers, _notfor = bp.split_description(description)

        pkg = ROOT / "skills" / sid
        in_body = any(
            term in f.read_text(encoding="utf-8", errors="ignore").lower()
            for f in pkg.rglob("*.md")
            if f.is_file()
        )
        rows.append(
            {
                "id": sid,
                "in_body": in_body,
                "in_triggers": term in (triggers or "").lower(),
                "in_lead": term in (lead or "").lower(),
                "in_gloss": term in gloss.lower(),
                "gloss_chars": len(gloss),
            }
        )

    routed = [r for r in rows if r["in_gloss"]]
    # Only a description that never survives into the gloss is a defect: the
    # author wrote routing vocabulary and the clip silently ate it. A term that
    # merely appears in the body is normal and must NOT be promoted — every
    # package that says "subagent" in prose is not a package a user typing
    # "subagent" should land on, and appending vocabulary to chase that has
    # already cost this repo 5pp of retrieval accuracy once.
    clipped = [r for r in rows if r["in_triggers"] and not r["in_gloss"]]
    lead_only = [r for r in rows if r["in_lead"] and not r["in_triggers"] and not r["in_gloss"]]
    body_only = [
        r for r in rows
        if r["in_body"] and not r["in_lead"] and not r["in_triggers"] and not r["in_gloss"]
    ]

    if args.json:
        print(json.dumps(
            {"term": args.term, "routed": routed, "clipped": clipped,
             "lead_only": lead_only, "body_only": body_only},
            indent=2,
        ))
    else:
        scope = f" in {args.domain}" if args.domain else ""
        print(f"'{args.term}'{scope}: reaches the shipped roster in {len(routed)} package(s).")
        if clipped:
            print(f"\nCLIPPED — declared as a trigger, lost before the roster ({len(clipped)}):")
            for r in sorted(clipped, key=lambda x: x["id"]):
                print(f"  {r['id']:52} gloss={r['gloss_chars']}/{bp.MAX_GLOSS_CHARS}")
            print(
                "\nA term in the lead is clipped first. To route it, move it into the\n"
                "description's `Triggers:` clause — substituting, not appending,\n"
                "because glosses already run at the cap."
            )
        for label, group in (("lead prose", lead_only), ("body", body_only)):
            if not group:
                continue
            print(f"\nMentioned in {label} only, not routed ({len(group)}) — usually correct, "
                  "listed for review:")
            for r in sorted(group, key=lambda x: x["id"])[:10]:
                print(f"  {r['id']}")
            if len(group) > 10:
                print(f"  … and {len(group) - 10} more")
    return 1 if clipped else 0


if __name__ == "__main__":
    sys.exit(main())
