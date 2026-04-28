#!/usr/bin/env python3
"""One-shot migration: strip § 6.1 / § 6.4 duplications from SKILL.md bodies.

Reads the validator's flagged-skill list directly so the source of truth is
`pipelines/validators.py:validate_skill_authoring_style`, not a hand-curated
list.

For each flagged skill:
- § 6.1 — remove the body `## When To Use` / `## When to Use` / `## When to use`
  section. The frontmatter `description` is the canonical trigger surface.
- § 6.4 — remove the body `## Well-Architected Pillars` /
  `## Well-Architected Pillar Mapping` / `## Architecture Pillars` /
  `## Pillar Mapping` section. The pillar list is in frontmatter and the
  analysis is in `references/well-architected.md`.

Section boundary: from the offending heading line up to (but not including)
the next `^## ` heading at the same level, or end of file. Frontmatter is
never touched. Trailing blank lines are collapsed.

Side effect: bumps `updated:` to today's ISO date for every modified file.

Run from repo root:
    python3 scripts/_migrations/strip_style_guide_duplications.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.validators import validate_skill_authoring_style

WHEN_TO_USE_RE = re.compile(r"^## [Ww]hen [Tt]o [Uu]se\b")
PILLAR_HEADING_RE = re.compile(
    r"^## (?:Well-Architected Pillars?(?: Mapping)?|Architecture Pillars?|Pillar Mapping)\b"
)

UPDATED_RE = re.compile(r"^updated:\s*\d{4}-\d{2}-\d{2}\s*$")


def find_section(lines: list[str], pattern: re.Pattern[str]) -> tuple[int, int, str] | None:
    """Return (start, end, heading_line) for the first H2 line matching
    `pattern`. End is the line of the next `## ` heading or len(lines).
    Frontmatter (between the first two `---` markers) is skipped."""
    in_frontmatter = False
    fence_count = 0
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped == "---":
            fence_count += 1
            in_frontmatter = fence_count == 1
            continue
        if fence_count < 2:
            in_frontmatter = fence_count == 1
            if in_frontmatter:
                continue
        if pattern.match(stripped):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            return (i, j, stripped)
    return None


def strip_sections(text: str, patterns: list[re.Pattern[str]]) -> tuple[str, list[str]]:
    """Strip the first H2 section matching each pattern in `patterns`.

    Section span: from the heading line up to (but not including) the next
    `^## ` heading at the same level, or end of file. Frontmatter is never
    touched. After stripping, runs of 3+ blank lines are collapsed to 2 and
    any orphan `---` horizontal rules left adjacent to each other are
    de-duplicated.

    Returns (new_text, removed_heading_list).
    """
    lines = text.split("\n")
    removed: list[str] = []
    for pattern in patterns:
        span = find_section(lines, pattern)
        if span is None:
            continue
        start, end, heading_line = span
        del lines[start:end]
        removed.append(heading_line)
    new_text = "\n".join(lines)
    # Collapse 3+ blank lines to 2.
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    # An immediately-adjacent pair of `---` horizontal rules (separated only
    # by blank lines) collapses to one. Repeat until stable in case removal
    # leaves three rules in a row.
    while True:
        replaced = re.sub(r"\n---\s*\n\s*\n---\s*\n", "\n---\n\n", new_text)
        if replaced == new_text:
            break
        new_text = replaced
    new_text = new_text.rstrip() + "\n"
    return new_text, removed


def bump_updated(text: str, today: str) -> tuple[str, bool]:
    """Bump the `updated:` line in the frontmatter to `today`. Returns
    (new_text, changed)."""
    out_lines = []
    in_frontmatter = False
    seen_open = False
    bumped = False
    for line in text.split("\n"):
        if line.strip() == "---":
            if not seen_open:
                seen_open = True
                in_frontmatter = True
            else:
                in_frontmatter = False
            out_lines.append(line)
            continue
        if in_frontmatter and UPDATED_RE.match(line):
            new_line = f"updated: {today}"
            if new_line != line:
                bumped = True
            out_lines.append(new_line)
            continue
        out_lines.append(line)
    return "\n".join(out_lines), bumped


def collect_flagged() -> dict[Path, list[re.Pattern[str]]]:
    """Walk skills/ and group flagged paths by which heading patterns to strip."""
    flagged: dict[Path, list[re.Pattern[str]]] = {}
    for skill_md in ROOT.glob("skills/*/*/SKILL.md"):
        issues = validate_skill_authoring_style(skill_md.parent)
        if not issues:
            continue
        patterns: list[re.Pattern[str]] = []
        for issue in issues:
            if "§ 6.1" in issue.message and WHEN_TO_USE_RE not in patterns:
                patterns.append(WHEN_TO_USE_RE)
            elif "§ 6.4" in issue.message and PILLAR_HEADING_RE not in patterns:
                patterns.append(PILLAR_HEADING_RE)
        if patterns:
            flagged[skill_md] = patterns
    return flagged


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    args = ap.parse_args()

    today = date.today().isoformat()
    flagged = collect_flagged()
    print(f"Found {len(flagged)} flagged skills (§ 6.1 / § 6.4).")

    if not flagged:
        return 0

    written = 0
    for path, patterns in sorted(flagged.items()):
        original = path.read_text(encoding="utf-8")
        stripped, removed = strip_sections(original, patterns)
        if not removed:
            print(f"  SKIP  {path.relative_to(ROOT)} — flagged but no heading match (validator drift?)")
            continue
        bumped, _ = bump_updated(stripped, today)
        if bumped == original:
            continue
        if args.dry_run:
            print(f"  DRY   {path.relative_to(ROOT)}: would strip {removed}")
        else:
            path.write_text(bumped, encoding="utf-8")
            print(f"  WROTE {path.relative_to(ROOT)}: stripped {removed}")
            written += 1

    if args.dry_run:
        print(f"\nDry run complete. {len(flagged)} files would be modified.")
    else:
        print(f"\nWrote {written} files. Run skill_sync next.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
