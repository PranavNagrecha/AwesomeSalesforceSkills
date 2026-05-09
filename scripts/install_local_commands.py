#!/usr/bin/env python3
"""Install repo `commands/*.md` to `.claude/commands/` so the local Claude
Code CLI can invoke them as slash commands.

The repo's top-level `commands/` directory is the canonical source for the
slash-command specs. Claude Code reads slash commands from
`<project>/.claude/commands/` (project-level) or `~/.claude/commands/`
(user-level). The repo's `commands/` is NOT auto-loaded — this script
copies it into the project-level location.

`.claude/` itself is gitignored, so the install is local-only by design.
Re-run after pulling new commands or removing deprecated ones.

Usage:
    python3 scripts/install_local_commands.py

Idempotent: existing files are overwritten with the latest spec.
Removes `.claude/commands/<name>.md` entries that no longer have a
matching `commands/<name>.md` in the source (so deprecated commands stop
appearing).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "commands"
DST = REPO / ".claude" / "commands"


def main() -> int:
    if not SRC.exists():
        print(f"source not found: {SRC}", file=sys.stderr)
        return 2

    DST.mkdir(parents=True, exist_ok=True)

    src_names = {p.name for p in SRC.glob("*.md")}
    dst_names = {p.name for p in DST.glob("*.md")}

    added = 0
    updated = 0
    removed = 0

    # Add or refresh
    for spec in sorted(SRC.glob("*.md")):
        target = DST / spec.name
        existed = target.exists()
        shutil.copy2(spec, target)
        if existed:
            updated += 1
        else:
            added += 1

    # Remove orphans (commands deleted from source)
    for orphan in sorted(dst_names - src_names):
        (DST / orphan).unlink()
        removed += 1

    print(
        f"installed {len(src_names)} commands to {DST.relative_to(REPO)}/  "
        f"(added={added} updated={updated} removed={removed})"
    )
    print(
        "Note: Claude Code loads slash commands at session start. "
        "Restart your CLI for new commands to register."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
