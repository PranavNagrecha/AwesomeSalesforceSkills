#!/usr/bin/env python3
"""Enforce AGENT_CONTRACT rule 5 — `dependencies.skills:` and the prose agree.

`agents/_shared/AGENT_CONTRACT.md` rule 5 requires every entry in an agent's
`dependencies.skills:` YAML block to have a matching Mandatory Reads line and
vice versa. Nothing enforced it until 2026-08-13, and the asymmetry is the
point: **the coverage check reads the YAML block only**. So a skill listed in
YAML and never mentioned in the body is counted as cited, is never seen by a
human reviewer, and is never read by the agent either. That is the exact shape
padding takes — and it also clears the 40-read ceiling, which counts prose
lines.

Two ERROR classes:

* `yaml-only-citation` — in `dependencies.skills:`, absent from the body.
  Invisible to review. This is the hiding place.
* `prose-only-citation` — cited in the body, absent from YAML. The inverse:
  a skill the agent really does read, which the coverage check cannot see, so
  the skill looks orphaned corpus-wide.

Matching the body is deliberately PERMISSIVE — any `skills/<domain>/<slug>`
mention anywhere in the AGENT.md counts. The stricter reading-list regex in
`scripts/validate_repo.py` only recognises the numbered form
"3. `skills/x/y` — why", and 29 agents legitimately use forms it misses
(markdown links, bullets, `1)` numbering, `./` prefixes). Being strict here
would report those 29 as divergent when they are not. This gate answers one
question — is the citation visible to a human reading the file — and any
mention answers it.

Deliberately NOT flagged: `skills/admin/agent-output-formats` appearing in
`dependencies.skills:`. Rule 5 calls the Scope Guardrails format-referral a
pointer rather than a read and says not to back-fill it into YAML, but 32
agents list it and most also read it. Whether a given agent loads that skill
or merely hands it to the caller is an intent question no gate can decide,
and guessing would either mass-flag correct files or license real padding.

Usage:
    python3 scripts/check_agent_citation_parity.py
    python3 scripts/check_agent_citation_parity.py --json
Exit code 1 if any ERROR is found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("pyyaml is required: python3 -m pip install -r requirements.txt", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
# Any skills/<domain>/<slug> mention: backticked, linked, bare, or ./-prefixed.
BODY_REF = re.compile(r"(?:^|[\s`(\[])\.?/?skills/([a-z0-9-]+/[a-z0-9-]+)")


def check_agent(path: Path, base: Path) -> list[dict]:
    rel = path.resolve().relative_to(base.resolve())
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER.match(text)
    if not m:
        return []
    try:
        front = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return []  # the frontmatter schema gate owns malformed YAML

    declared = (front.get("dependencies") or {}).get("skills") or []
    declared_set = {str(s).strip() for s in declared if str(s).strip()}
    body = text[m.end():]
    mentioned = set(BODY_REF.findall(body))

    issues: list[dict] = []
    for skill in sorted(declared_set - mentioned):
        issues.append({
            "level": "ERROR",
            "file": str(rel),
            "kind": "yaml-only-citation",
            "message": (
                f"`{skill}` is in dependencies.skills: but is never mentioned in "
                f"the body. The coverage check reads the YAML only, so this "
                f"counts as a citation no reviewer can see and no agent reads. "
                f"Either add a Mandatory Reads line saying why it is needed, or "
                f"drop it from the YAML."
            ),
        })
    for skill in sorted(mentioned - declared_set):
        issues.append({
            "level": "ERROR",
            "file": str(rel),
            "kind": "prose-only-citation",
            "message": (
                f"`{skill}` is cited in the body but missing from "
                f"dependencies.skills:. The coverage check cannot see it, so "
                f"the skill reads as orphaned corpus-wide."
            ),
        })
    return issues


def collect_issues(root: Path | None = None) -> list[dict]:
    base = (root or ROOT).resolve()
    agents_root = base / "agents"
    if not agents_root.is_dir():
        return []
    issues: list[dict] = []
    for path in sorted(agents_root.glob("*/AGENT.md")):
        issues.extend(check_agent(path, base))
    return issues


def collect_citation_parity_issues(root: Path) -> list[tuple[str, str, str]]:
    """(level, path, message) triples, matching validate_repo's ValidationIssue."""
    return [(i["level"], i["file"], f"[{i['kind']}] {i['message']}")
            for i in collect_issues(root)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    issues = collect_issues()
    agents = sorted((ROOT / "agents").glob("*/AGENT.md"))

    if args.json:
        print(json.dumps(issues, indent=1))
    else:
        for i in issues:
            print(f"{i['level']} {i['file']}: [{i['kind']}] {i['message']}")
        print(f"\nChecked {len(agents)} agent(s); {len(issues)} error(s).")

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
