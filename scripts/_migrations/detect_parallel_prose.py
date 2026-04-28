#!/usr/bin/env python3
"""One-shot triage: detect § 6.2 parallel-prose-→-table candidates.

Walks every `skills/<domain>/<slug>/SKILL.md`, finds runs of 3+ consecutive
`- **X**:` (or `* **X**:`) bullets in the body, and writes a per-domain
ranked report to `docs/reports/parallel-prose-candidates.md`.

The bullets that match this shape are usually parallel dimensions of
independently-selectable items — the canonical "should be a table" signal
from `standards/skill-authoring-style.md` § 6.2.

Heuristic:
- Skip frontmatter (between the first two `---` lines).
- Skip fenced code blocks (between paired ```...``` fences).
- For each remaining line, test against PARALLEL_BULLET_RE.
- A "run" is 3+ consecutive matches with no non-matching, non-blank line
  between them. (A blank line ends the run — table candidates are tight
  bullet lists, not interleaved prose.)

Run from repo root:
    python3 scripts/_migrations/detect_parallel_prose.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PARALLEL_BULLET_RE = re.compile(r"^\s*[-*]\s+\*\*([^*]+)\*\*\s*[:\u2014\-]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*```")

# 4 is the threshold where a table starts paying off visually — the header
# row + delimiter row cost (2 lines) amortizes across 4+ data rows. 3-row
# tables rarely beat 3 well-shaped bullets, so they're left alone here and
# left alone by the WARN validator that mirrors this detector.
MIN_RUN = 4

# Bullets longer than this are paragraph-prose, not parallel-list items.
# A table cell holding 3 sentences loses the column-scanning advantage
# that justifies a table at all — the bullets are the right shape.
MAX_MEDIAN_BULLET_CHARS = 220

# Headings whose parallel-bullet structure is intentional repo convention,
# not a § 6.2 violation. The bullets are a navigation index (Related Skills)
# or carry per-bullet narrative that doesn't fit a grid.
EXEMPT_HEADING_RE = re.compile(r"^#{2,6}\s+Related Skills\b", re.IGNORECASE)


class Run:
    __slots__ = ("start", "end", "slugs", "heading", "preview", "lengths")

    def __init__(
        self,
        start: int,
        end: int,
        slugs: list[str],
        heading: str,
        preview: list[str],
        lengths: list[int],
    ):
        self.start = start
        self.end = end
        self.slugs = slugs
        self.heading = heading
        self.preview = preview
        self.lengths = lengths


def _median(values: list[int]) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    mid = len(sorted_v) // 2
    if len(sorted_v) % 2:
        return float(sorted_v[mid])
    return (sorted_v[mid - 1] + sorted_v[mid]) / 2


def find_runs(path: Path) -> list[Run]:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Locate frontmatter end.
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                body_start = i + 1
                break

    runs: list[Run] = []
    in_fence = False
    current_heading = ""
    current_run_start = -1
    current_slugs: list[str] = []
    current_preview: list[str] = []
    current_lengths: list[int] = []

    def flush(end_line: int) -> None:
        if (
            len(current_slugs) >= MIN_RUN
            and not EXEMPT_HEADING_RE.match(current_heading)
            and _median(current_lengths) <= MAX_MEDIAN_BULLET_CHARS
        ):
            runs.append(
                Run(
                    start=current_run_start + 1,
                    end=end_line + 1,
                    slugs=list(current_slugs),
                    heading=current_heading,
                    preview=list(current_preview[:3]),
                    lengths=list(current_lengths),
                )
            )
        current_slugs.clear()
        current_preview.clear()
        current_lengths.clear()

    for idx in range(body_start, len(lines)):
        line = lines[idx]

        if FENCE_RE.match(line):
            if current_slugs:
                flush(idx - 1)
                current_run_start = -1
            in_fence = not in_fence
            continue

        if in_fence:
            if current_slugs:
                flush(idx - 1)
                current_run_start = -1
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            if current_slugs:
                flush(idx - 1)
                current_run_start = -1
            current_heading = line.strip()
            continue

        bullet_match = PARALLEL_BULLET_RE.match(line)
        if bullet_match:
            if not current_slugs:
                current_run_start = idx
            current_slugs.append(bullet_match.group(1).strip())
            current_preview.append(line.rstrip())
            current_lengths.append(len(line.rstrip()))
        else:
            # Blank or non-matching line — end any open run.
            if current_slugs:
                flush(idx - 1)
                current_run_start = -1

    # End-of-file flush.
    if current_slugs:
        flush(len(lines) - 1)

    return runs


def main() -> int:
    skills = sorted(ROOT.glob("skills/*/*/SKILL.md"))
    by_domain: dict[str, list[tuple[Path, list[Run]]]] = defaultdict(list)
    total_runs = 0
    total_files = 0

    for skill_md in skills:
        runs = find_runs(skill_md)
        if not runs:
            continue
        domain = skill_md.parent.parent.name
        by_domain[domain].append((skill_md, runs))
        total_runs += len(runs)
        total_files += 1

    report_path = ROOT / "docs" / "reports" / "parallel-prose-candidates.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    out: list[str] = []
    out.append("# § 6.2 Parallel-Prose-→-Table Candidates")
    out.append("")
    out.append(
        f"Scanned {len(skills)} SKILL.md files; flagged {total_files} files containing "
        f"{total_runs} runs of {MIN_RUN}+ consecutive `- **X**:` bullets."
    )
    out.append("")
    out.append(
        "Each entry shows the skill, the run's line range in the source file, "
        "the parent `## ...` heading, the bold-prefix slugs (which become the "
        "table's first column if converted), and a 3-line preview."
    )
    out.append("")
    out.append("Per-domain ordering: domains ranked by file count desc, files by run count desc.")
    out.append("")

    domain_order = sorted(by_domain.keys(), key=lambda d: -len(by_domain[d]))
    for domain in domain_order:
        entries = sorted(by_domain[domain], key=lambda e: -len(e[1]))
        out.append(f"## {domain} ({len(entries)} files, {sum(len(r) for _, r in entries)} runs)")
        out.append("")
        for skill_md, runs in entries:
            rel = skill_md.relative_to(ROOT)
            out.append(f"### `{rel}` — {len(runs)} run(s)")
            out.append("")
            for run in runs:
                heading = run.heading or "(no parent heading)"
                slugs_display = ", ".join(f"`{s}`" for s in run.slugs)
                out.append(
                    f"- **L{run.start}–L{run.end}** under {heading} "
                    f"— {len(run.slugs)} bullets: {slugs_display}"
                )
                out.append("")
                out.append("  ```")
                for preview in run.preview:
                    out.append(f"  {preview}")
                if len(run.slugs) > 3:
                    out.append(f"  ... +{len(run.slugs) - 3} more")
                out.append("  ```")
                out.append("")
        out.append("")

    report_path.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {report_path.relative_to(ROOT)}")
    print(f"  {total_files} files flagged across {len(by_domain)} domains")
    print(f"  {total_runs} total runs of {MIN_RUN}+ consecutive bold-prefix bullets")
    print()
    print("Per-domain breakdown:")
    for domain in domain_order:
        entries = by_domain[domain]
        runs = sum(len(r) for _, r in entries)
        print(f"  {domain:14s} {len(entries):4d} files  {runs:5d} runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
