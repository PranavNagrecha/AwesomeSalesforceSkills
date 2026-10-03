#!/usr/bin/env python3
"""Extract the GitHub Release body for an mcp-v* tag from CHANGELOG.md.

The release for tag ``mcp-vX.Y.Z`` carries two CHANGELOG sections: the
``## [X.Y.Z]`` sfskills-mcp section and the ``## [Plugin A.B.C]`` section that
carries the same release date (else the nearest one above it).
``publish-mcp.yml`` runs this in the ``publish-data`` job and passes the file
as ``body_path`` so the release page always carries the notes that shipped in
the repository, never a hand-typed summary that drifts.

Usage:
    python3 scripts/release_notes.py 0.5.0                 # print to stdout
    python3 scripts/release_notes.py 0.5.0 --out notes.md  # write the file
    python3 scripts/release_notes.py 0.5.0 --title         # print the release title only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H2 = re.compile(r"^## \[(.+?)\](.*)$", re.M)


def sections(text: str) -> list[tuple[str, str, str]]:
    """Return (label, rest-of-heading, body) for every ``## [...]`` section."""
    heads = list(H2.finditer(text))
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out.append((m.group(1), m.group(2).strip(), text[m.end():end].strip("\n")))
    return out


def build(version: str, changelog: str) -> tuple[str, str]:
    secs = sections(changelog)
    labels = [s[0] for s in secs]
    if version not in labels:
        raise SystemExit(f"CHANGELOG.md has no '## [{version}]' section; add it before tagging mcp-v{version}.")
    idx = labels.index(version)
    mcp = secs[idx]
    # The plugin section that belongs to this mcp release: same release date in
    # the heading when one exists (CHANGELOG order is not consistent — 1.3.0 sits
    # above 0.5.0, 1.2.0 below 0.4.10), else the nearest Plugin section above.
    date = re.search(r"\d{4}-\d{2}-\d{2}", mcp[1])
    plugin = None
    if date:
        plugin = next((s for s in secs if s[0].startswith("Plugin ") and date.group(0) in s[1]), None)
    if plugin is None:
        plugin = next((s for s in reversed(secs[:idx]) if s[0].startswith("Plugin ")), None)
    title = f"sfskills-mcp {version}"
    parts = [f"## sfskills-mcp {version}{(' ' + mcp[1]) if mcp[1] else ''}", "", mcp[2].strip(), ""]
    if plugin:
        title += f" + {plugin[0]}"
        parts += [f"## {plugin[0]}{(' ' + plugin[1]) if plugin[1] else ''}", "", plugin[2].strip(), ""]
    parts += [
        "---",
        "Assets: `sfskills-data.tar.gz` (registry, lexical index, skills, agents, templates, "
        "decision trees, commands, pipelines, config — what `sfskills-mcp-init` downloads), the "
        "wheel and sdist, and `SHA256SUMS.txt`. Full history: `CHANGELOG.md`.",
    ]
    return title, "\n".join(parts).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build GitHub Release notes for an mcp-v tag from CHANGELOG.md.")
    ap.add_argument("version", help="sfskills-mcp version, e.g. 0.5.0 (tag mcp-v0.5.0)")
    ap.add_argument("--changelog", type=Path, default=ROOT / "CHANGELOG.md")
    ap.add_argument("--out", type=Path, help="write the body here instead of stdout")
    ap.add_argument("--title", action="store_true", help="print only the release title")
    args = ap.parse_args()
    version = args.version.removeprefix("mcp-v").removeprefix("v")
    title, body = build(version, args.changelog.read_text(encoding="utf-8"))
    if args.title:
        print(title)
        return 0
    if args.out:
        args.out.write_text(body, encoding="utf-8")
        print(f"wrote {args.out} ({len(body.splitlines())} lines): {title}")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
