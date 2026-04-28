#!/usr/bin/env python3
"""Checker script for Configuration Workbook Authoring skill.

Validates a Configuration Workbook markdown file (authored from
`templates/config-workbook.md`) against the canonical row schema:

- every row has `row_id`, `target_value`, `owner`, `source_req_id`,
  `source_story_id`, `recommended_agent`, `recommended_skills`, `status`
- `recommended_agent` resolves to a real runtime agent in the SfSkills
  repo (read from `agents/_shared/SKILL_MAP.md` plus the `agents/` directory
  listing — both are consulted as authoritative)
- no row has a placeholder `status` (`TBD`, `TODO`, `?`, `WIP`, empty)
- no row is missing `source_req_id` (orphan rows)
- no row carries an inline credential in `target_value`

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_workbook.py --workbook docs/workbooks/<release>/cwb.md
    python3 check_workbook.py --workbook <path> --repo-root /path/to/SfSkills
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Canonical schema
# ---------------------------------------------------------------------------

CANONICAL_SECTIONS = [
    "Objects + Fields",
    "Page Layouts + Lightning Pages",
    "Profiles + Permission Sets + PSGs",
    "Sharing Settings",
    "Validation Rules",
    "Automation",
    "List Views + Search",
    "Reports + Dashboards",
    "Integrations",
    "Data + Migration",
]

REQUIRED_ROW_FIELDS = [
    "row_id",
    "target_value",
    "owner",
    "source_req_id",
    "source_story_id",
    "recommended_agent",
    "recommended_skills",
    "status",
]

ALLOWED_STATUSES = {
    "proposed",
    "committed",
    "in-progress",
    "executed",
    "verified",
    "change-requested",
}

PLACEHOLDER_STATUS_TOKENS = {"", "TBD", "TODO", "?", "WIP", "DOING", "NEXT"}

# Heuristic patterns that look like inline secrets in `target_value`.
# Workbook rows must reference Named Credential aliases instead.
SECRET_PATTERNS = [
    re.compile(r"\bsk_(live|test)_[A-Za-z0-9]{8,}\b"),  # Stripe-like
    re.compile(r"\bAKIA[0-9A-Z]{12,}\b"),                # AWS access key
    re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b"),          # Google API key
    re.compile(r"\bxox[abps]-[A-Za-z0-9-]{8,}\b"),       # Slack tokens
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b"),    # Bearer tokens
    re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"),
]


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a Configuration Workbook markdown file.",
    )
    parser.add_argument(
        "--workbook",
        required=True,
        help="Path to the workbook markdown file (e.g. docs/workbooks/<release>/cwb.md).",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Path to the SfSkills repo root (used to resolve the runtime "
             "agent roster from agents/_shared/SKILL_MAP.md and agents/). "
             "Defaults to walking upward from this script.",
    )
    parser.add_argument(
        "--allow-empty-section",
        action="store_true",
        help="Permit sections that contain no data rows (still require the "
             "section heading to exist).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Repo discovery
# ---------------------------------------------------------------------------

def discover_repo_root(explicit: str | None) -> Path:
    """Resolve the SfSkills repo root.

    Priority:
      1. --repo-root CLI flag.
      2. Walk upward from this script until a sibling `agents/` directory is found.
    """
    if explicit:
        root = Path(explicit).resolve()
        if not (root / "agents").exists():
            raise SystemExit(f"--repo-root {root} does not contain an agents/ directory")
        return root

    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "agents").exists() and (candidate / "skills").exists():
            return candidate
    raise SystemExit(
        "Could not locate SfSkills repo root by walking upward from "
        f"{here}. Pass --repo-root explicitly."
    )


def load_runtime_agents(repo_root: Path) -> set[str]:
    """Load the runtime agent roster.

    The authoritative source is `agents/_shared/SKILL_MAP.md` (per
    AGENT_RULES.md) but the on-disk directory listing under `agents/` is
    consulted as well so newly-added agents that haven't been documented in
    the map yet still validate. Build-time agents (which carry
    `class: build` in their AGENT.md frontmatter) are excluded.
    """
    agents_dir = repo_root / "agents"
    if not agents_dir.exists():
        raise SystemExit(f"agents/ directory not found at {agents_dir}")

    skill_map = repo_root / "agents" / "_shared" / "SKILL_MAP.md"
    map_agents: set[str] = set()
    if skill_map.exists():
        # SKILL_MAP.md uses headings like "### `agent-name`" or
        # "### `agent-name` (deprecated...)". Pull the backticked names.
        text = skill_map.read_text(encoding="utf-8")
        for match in re.finditer(r"^###\s+`([a-z0-9][a-z0-9\-]+)`", text, re.MULTILINE):
            map_agents.add(match.group(1))

    dir_agents: set[str] = set()
    for child in agents_dir.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        agent_md = child / "AGENT.md"
        if not agent_md.exists():
            continue
        # Filter out build-time agents.
        head = agent_md.read_text(encoding="utf-8", errors="ignore").split("\n", 60)
        is_build = any(line.strip() == "class: build" for line in head[:30])
        if is_build:
            continue
        dir_agents.add(child.name)

    roster = map_agents | dir_agents
    if not roster:
        raise SystemExit(
            "Runtime agent roster came back empty — neither "
            "agents/_shared/SKILL_MAP.md nor the agents/ directory yielded "
            "any names. Refusing to validate against an empty allowlist."
        )
    return roster


# ---------------------------------------------------------------------------
# Workbook parsing
# ---------------------------------------------------------------------------

SECTION_HEADING_RE = re.compile(r"^##\s+Section\s+\d+\s+[—\-]\s+(.+?)\s*$")


def normalize_section_name(raw: str) -> str:
    """Loose-match a section heading to one of the canonical names."""
    cleaned = raw.strip()
    cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
    # Tolerate Automation variants like "Automation (Flow / Apex / Approvals)".
    if cleaned.lower().startswith("automation"):
        return "Automation"
    return cleaned


def parse_workbook(path: Path) -> dict:
    """Parse the workbook into a dict of section → list of row dicts.

    The parser only cares about Markdown table rows under each
    `## Section N — <name>` heading. The header row of each table is used
    to map columns to row dict keys.
    """
    if not path.exists():
        raise SystemExit(f"Workbook not found: {path}")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    sections: dict[str, list[dict]] = {}
    current_section: str | None = None
    table_header: list[str] | None = None
    in_table_body = False

    for raw_line in lines:
        line = raw_line.rstrip()

        heading_match = SECTION_HEADING_RE.match(line)
        if heading_match:
            current_section = normalize_section_name(heading_match.group(1))
            sections.setdefault(current_section, [])
            table_header = None
            in_table_body = False
            continue

        if current_section is None:
            continue

        # Markdown tables: header row, separator row, body rows.
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if table_header is None:
                table_header = [c.lower() for c in cells]
                in_table_body = False
                continue
            # Detect the separator row "|---|---|...".
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                in_table_body = True
                continue
            if in_table_body:
                row = dict(zip(table_header, cells))
                # Skip the per-row schema legend table (header is "field").
                if "field" in table_header and "required" in table_header:
                    continue
                sections[current_section].append(row)
        else:
            # A blank or non-table line ends the current table.
            if in_table_body:
                table_header = None
                in_table_body = False

    return sections


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

def is_blank(value: str | None) -> bool:
    return value is None or not value.strip()


def looks_like_secret(target_value: str) -> bool:
    return any(p.search(target_value) for p in SECRET_PATTERNS)


def split_skills(cell: str) -> list[str]:
    if not cell:
        return []
    # Accept ;, |, or newline as delimiters.
    parts = re.split(r"[;|\n]", cell)
    return [p.strip() for p in parts if p.strip()]


def check_row(
    row: dict,
    section: str,
    runtime_agents: set[str],
) -> list[str]:
    issues: list[str] = []
    row_id = row.get("row_id") or "(missing row_id)"

    for field in REQUIRED_ROW_FIELDS:
        if is_blank(row.get(field)):
            issues.append(
                f"[{section}] row {row_id}: missing required field `{field}`"
            )

    status = (row.get("status") or "").strip()
    if status.upper() in PLACEHOLDER_STATUS_TOKENS:
        issues.append(
            f"[{section}] row {row_id}: status `{status or '<empty>'}` is a "
            f"placeholder — must be one of {sorted(ALLOWED_STATUSES)}"
        )
    elif status and status.lower() not in ALLOWED_STATUSES:
        issues.append(
            f"[{section}] row {row_id}: status `{status}` is not in the "
            f"allowed enum {sorted(ALLOWED_STATUSES)}"
        )

    agent = (row.get("recommended_agent") or "").strip()
    if agent and agent not in runtime_agents:
        issues.append(
            f"[{section}] row {row_id}: recommended_agent `{agent}` is not "
            f"in the runtime roster (see agents/_shared/SKILL_MAP.md and the "
            f"agents/ directory)"
        )

    skills_cell = row.get("recommended_skills") or ""
    skills = split_skills(skills_cell)
    if not skills and not is_blank(skills_cell):
        # Cell had content but couldn't be split into ≥ 1 skill id.
        issues.append(
            f"[{section}] row {row_id}: recommended_skills cell present but "
            f"could not be parsed into ≥ 1 skill id (use `;` or `|` to "
            f"delimit multiple skills)"
        )

    target_value = row.get("target_value") or ""
    if target_value and looks_like_secret(target_value):
        issues.append(
            f"[{section}] row {row_id}: target_value appears to contain an "
            f"inline credential — replace with a Named Credential alias"
        )

    return issues


# ---------------------------------------------------------------------------
# Top-level check
# ---------------------------------------------------------------------------

def check_workbook(
    workbook_path: Path,
    repo_root: Path,
    allow_empty_section: bool,
) -> list[str]:
    issues: list[str] = []
    runtime_agents = load_runtime_agents(repo_root)
    sections = parse_workbook(workbook_path)

    # Section coverage check.
    expected_section_keys = {normalize_section_name(s) for s in CANONICAL_SECTIONS}
    seen_section_keys = set(sections.keys())
    missing_sections = expected_section_keys - seen_section_keys
    for missing in sorted(missing_sections):
        issues.append(
            f"Missing canonical section: `{missing}`. All 10 sections must "
            f"be present (use `not-in-scope-this-release` for empty sections)."
        )

    # Per-row checks.
    for section, rows in sections.items():
        if not rows:
            if not allow_empty_section:
                issues.append(
                    f"[{section}] has no rows — even out-of-scope sections "
                    f"must carry one row with target_value "
                    f"`not-in-scope-this-release`."
                )
            continue
        # Filter out the schema legend table that may have leaked in.
        data_rows = [
            r for r in rows if not is_blank(r.get("row_id")) or not is_blank(r.get("target_value"))
        ]
        if not data_rows and not allow_empty_section:
            issues.append(
                f"[{section}] has only blank rows — populate or mark "
                f"`not-in-scope-this-release`."
            )
        for row in data_rows:
            issues.extend(check_row(row, section, runtime_agents))

    return issues


def main() -> int:
    args = parse_args()
    workbook = Path(args.workbook).resolve()
    repo_root = discover_repo_root(args.repo_root)

    issues = check_workbook(
        workbook_path=workbook,
        repo_root=repo_root,
        allow_empty_section=args.allow_empty_section,
    )

    if not issues:
        print(f"OK: workbook {workbook} passes all checks.")
        return 0

    for issue in issues:
        print(f"ERROR: {issue}", file=sys.stderr)
    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
