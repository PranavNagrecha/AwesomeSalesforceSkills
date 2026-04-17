#!/usr/bin/env python3
"""One-shot backfill of YAML frontmatter into existing AGENT.md files.

Adds a frontmatter block that conforms to
``agents/_shared/schemas/agent-frontmatter.schema.json`` when one is missing.
Is idempotent: files that already have frontmatter are left alone.

Defaults (tunable via flags):

- ``class``: ``runtime`` if the agent is listed in the MCP runtime roster
  (mcp/sfskills-mcp/src/sfskills_mcp/agents.py), else ``build``.
- ``requires_org``: ``true`` for runtime agents except the skill-factory
  agents and pure-library agents; ``false`` for build-time agents.
- ``modes``: parsed from the AGENT.md body when a ``| mode | yes | design |
  audit |`` row is present, else ``[single]``.
- ``version``: ``1.0.0`` for stable agents.
- ``status``: ``stable`` unless the path is under an explicit beta directory.
- ``owner``: ``sfskills-core`` (the default maintainer).
- ``created`` / ``updated``: today's date.

Run with ``--dry-run`` to see what would change without writing.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "agents"
RUNTIME_ROSTER_PATH = ROOT / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp" / "agents.py"

# Agents that are runtime per the MCP roster but do not require a live org.
_RUNTIME_NO_ORG = {
    "bulk-migration-planner",
    "test-class-generator",
    "apex-refactorer",
    "trigger-consolidator",
    "agentforce-builder",
    "release-train-planner",
    "sandbox-strategy-designer",
    "csv-to-object-mapper",
}


def _parse_runtime_roster(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    # Single-quoted or double-quoted kebab-case agent ids inside the _RUNTIME_AGENTS set.
    return set(re.findall(r'"([a-z][a-z0-9-]{2,})"', text))


def _detect_modes(body: str) -> list[str]:
    # Look for a row like `| mode | yes | design \| audit |` in an Inputs table.
    match = re.search(
        r"\|\s*`?mode`?\s*\|[^|\n]*\|[^|\n]*`?([a-z]+)`?\s*(?:\\?\|\s*`?([a-z]+)`?\s*)?(?:\\?\|\s*`?([a-z]+)`?\s*)?",
        body,
        re.IGNORECASE,
    )
    if match:
        modes = [m for m in match.groups() if m]
        if modes:
            return modes
    if re.search(r"^###\s+Design\s+mode", body, re.MULTILINE) and re.search(
        r"^###\s+Audit\s+mode", body, re.MULTILINE
    ):
        return ["design", "audit"]
    return ["single"]


def _detect_requires_org(slug: str, is_runtime: bool, body: str) -> bool:
    if not is_runtime:
        return False
    if slug in _RUNTIME_NO_ORG:
        return False
    # Most runtime agents that have an Inputs table with a target_org_alias row are org-required.
    if re.search(r"target_org_alias.*yes", body, re.IGNORECASE):
        return True
    # Default to True for runtime agents — the contract says to refuse loudly if the org is missing.
    return True


def _build_frontmatter(slug: str, is_runtime: bool, body: str, today: str) -> str:
    modes = _detect_modes(body)
    requires_org = _detect_requires_org(slug, is_runtime, body)
    lines = [
        "---",
        f"id: {slug}",
        f"class: {'runtime' if is_runtime else 'build'}",
        "version: 1.0.0",
        "status: stable",
        f"requires_org: {'true' if requires_org else 'false'}",
        "modes: [" + ", ".join(modes) + "]",
        "owner: sfskills-core",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
    ]
    return "\n".join(lines)


def _has_frontmatter(text: str) -> bool:
    lines = text.splitlines()
    if not lines:
        return False
    return lines[0].strip() == "---"


def process_agent(path: Path, runtime_roster: set[str], today: str, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    if _has_frontmatter(text):
        return False
    slug = path.parent.name
    is_runtime = slug in runtime_roster
    frontmatter = _build_frontmatter(slug=slug, is_runtime=is_runtime, body=text, today=today)
    new_text = frontmatter + text
    if dry_run:
        print(f"[DRY-RUN] would add frontmatter to {path.relative_to(ROOT)} (class={'runtime' if is_runtime else 'build'})")
        return True
    path.write_text(new_text, encoding="utf-8")
    print(f"backfilled {path.relative_to(ROOT)} (class={'runtime' if is_runtime else 'build'})")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print what would be written without touching files.")
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Restrict to a single agent slug (matches the folder name).",
    )
    args = parser.parse_args()

    today = datetime.date.today().isoformat()
    runtime_roster = _parse_runtime_roster(RUNTIME_ROSTER_PATH)

    changed = 0
    total = 0
    for entry in sorted(AGENTS_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        if args.only and entry.name != args.only:
            continue
        md = entry / "AGENT.md"
        if not md.exists():
            continue
        total += 1
        if process_agent(md, runtime_roster=runtime_roster, today=today, dry_run=args.dry_run):
            changed += 1

    print(f"{'Would backfill' if args.dry_run else 'Backfilled'} {changed}/{total} agent(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
