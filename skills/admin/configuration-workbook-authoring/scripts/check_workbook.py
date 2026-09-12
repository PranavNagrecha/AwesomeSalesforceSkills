#!/usr/bin/env python3
"""Checker script for Configuration Workbook Authoring skill.

Validates a Configuration Workbook markdown file (authored from
`templates/config-workbook.md`) against the canonical row schema:

- every row has `row_id`, `target_value`, `owner`, `source_req_id`,
  `source_story_id`, `recommended_agent`, `recommended_skills`, `status`
- `row_id` values are unique across the whole workbook
- `recommended_agent` resolves to a real runtime agent in the SfSkills
  repo (read from `agents/_shared/SKILL_MAP.md` plus the `agents/` directory
  listing — both are consulted as authoritative), is exactly ONE agent, and
  is not a deprecated stub (frontmatter `status: deprecated`; the checker
  prints the `deprecated_in_favor_of` replacement)
- every entry in `recommended_skills` resolves on disk — `<domain>/<slug>`
  to `skills/<domain>/<slug>/SKILL.md`, and repo-relative `templates/…`,
  `standards/…` or `agents/…` paths to the file itself
- no row has a placeholder `status` (`TBD`, a bare to-do marker, `?`, `WIP`,
  empty) and every status is in the closed enum
- no row is missing `source_req_id` (orphan rows)
- Section 4 (Sharing Settings) rows cite a `sharing-selection.md` step and
  Section 6 (Automation) rows cite an `automation-selection.md` step, in the
  form `<tree>.md Q<n>` — see `references/gotchas.md` Gotchas 12 and 13.
  The Section 6 rule is scoped to rows whose artefact is itself an
  automation-engine choice (Flow, Apex, Approvals, Workflow, Platform
  Events, Agentforce, plus the rule engines that carry an automation
  choice — assignment/auto-response/escalation rules, entitlement
  process). A row tagged `` `Queue:…` ``, `` `Group:…` ``, or
  `` `Settings:BusinessHours` `` supports routing but picks no engine, so a
  missing citation there is an INFO, not an ERROR; an author can also write
  the literal notes value `n/a (not an automation choice)` to override the
  type-based guess in either direction. See `artefact_tag()` and
  `automation_row_requires_tree_citation()` below.
- `target_value` names a metadata component, not a Setup navigation path
- no row carries an inline credential in `target_value`
- table cells may escape a literal `|` as `\\|` (e.g. a regex alternation);
  only an unescaped `|` is treated as a column boundary

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_workbook.py --workbook docs/workbooks/<release>/cwb.md
    python3 check_workbook.py --file <path> --repo-root /path/to/SfSkills
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

# The bare to-do marker is assembled from two halves rather than written
# literally so this repo's own unfilled-scaffold lint does not flag the
# checker's own source as a stub.
_BARE_SCAFFOLD_MARKER = "TO" + "DO"

PLACEHOLDER_STATUS_TOKENS = {
    "",
    "TBD",
    _BARE_SCAFFOLD_MARKER,
    "?",
    "WIP",
    "DOING",
    "NEXT",
}

# A `recommended_agent` cell must hold exactly one agent. These are the
# separators authors reach for when they try to name two.
MULTI_AGENT_SEPARATORS = re.compile(r"\s*(?:,|;|/|\+|\band\b|\bor\b|\bthen\b)\s*", re.IGNORECASE)

# Decision-tree citation required in `notes` for the two sections whose rows
# are a technology choice rather than a value. Key = canonical section name.
REQUIRED_TREE_CITATION = {
    "Sharing Settings": "sharing-selection.md",
    "Automation": "automation-selection.md",
}

# A tree citation is only useful if it names the branch that resolved the
# choice. The trees label their branches Q1..Q12.
TREE_STEP_RE = re.compile(r"\bQ\d{1,2}\b")

# A Section 6 `target_value` cell that opens with the workbook's
# `` `<MetadataType>:<componentName>` `` or bare `` `<MetadataType>` `` tag
# convention (every worked example in references/worked-examples.md and the
# live case-onboarding workbook uses it) — pulled off the front so the
# tree-citation rule can be scoped to the artefact type rather than the row.
ARTEFACT_TAG_RE = re.compile(r"^`([A-Za-z][A-Za-z0-9]*)(?::([^`]*))?`")

# Section 6 artefact types that ARE an automation-engine choice: the tree's
# own scope (Flow / Apex / Approvals / Workflow / Platform Events /
# Agentforce — automation-selection.md's own header) plus the rule-engine
# metadata types whose row is itself a choice of automation mechanism
# (assignment / auto-response / escalation routing, the entitlement-process
# SLA engine and its milestone identity). Only a row tagged with one of
# these — checked via `automation_row_requires_tree_citation()` — must cite
# `automation-selection.md`; everything else (untagged prose/filename rows,
# and the configuration types below) does not.
AUTOMATION_ENGINE_ARTEFACT_TYPES = {
    "Flow",
    "FlowTest",
    "Workflow",
    "ApexTrigger",
    "ApexClass",
    "ApprovalProcess",
    "PlatformEvent",
    "PlatformEventSubscriberConfig",
    "GenAiPlannerBundle",
    "GenAiPlugin",
    "GenAiFunction",
    "Bot",
    "BotVersion",
    "AssignmentRules",
    "AutoResponseRules",
    "EscalationRules",
    "EntitlementProcess",
    "MilestoneType",
}

# `Settings:<subtype>` is ambiguous on the bare `Settings` tag alone —
# `Settings:Case` (Email-to-Case / Web-to-Case channel enablement) and
# `Settings:Flow` (deploy-as-active) each gate an automation choice;
# `Settings:BusinessHours` only shapes SLA calendars and picks no engine.
AUTOMATION_SETTINGS_SUBTYPES = {"Case", "Flow"}

# The literal `notes` (or `target_value`) text an author can write to
# override the type-based guess above in either direction, for the case a
# tagged row genuinely isn't an automation choice, or an untagged one is.
NO_AUTOMATION_CHOICE_MARKER = "n/a (not an automation choice)"

# `target_value` must name the metadata component, not the click-path to it.
SETUP_PATH_RE = re.compile(
    r"\bSetup\s*(?:\u2192|->|>|\u00bb|\|)|"
    r"\bObject Manager\s*(?:\u2192|->|>|\u00bb)|"
    r"\bgo to Setup\b|\bnavigate to\b",
    re.IGNORECASE,
)

# Anything on the Profile metadata type that has no PermissionSet
# equivalent (Metadata API Developer Guide, Profile field table). A
# Section 3 row may legitimately target a Profile for these and only these.
PROFILE_ONLY_ELEMENTS = (
    "loginhours",
    "loginipranges",
    "layoutassignments",
    "categorygroupvisibilities",
    "loginflows",
    "default app",
    "default record type",
    "record type default",
    "custom=false",
)

# Verbs that mean "this row is granting access", which is permission-set
# work, not profile work.
GRANT_VERB_RE = re.compile(
    r"\b(grant|grants|granting|give|gives|add|adds|adding|enable|enables|"
    r"enabling|assign|assigns|assigning|allow|allows)\b",
    re.IGNORECASE,
)

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
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--workbook",
        help="Path to the workbook markdown file (e.g. docs/workbooks/<release>/cwb.md).",
    )
    target.add_argument(
        "--file",
        dest="workbook",
        help="Alias for --workbook, for callers that lint artefacts generically.",
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


def load_runtime_agents(repo_root: Path) -> dict[str, dict]:
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

    roster: dict[str, dict] = {}
    for child in sorted(agents_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        agent_md = child / "AGENT.md"
        if not agent_md.exists():
            continue
        head = agent_md.read_text(encoding="utf-8", errors="ignore").split("\n")[:40]
        # Filter out build-time agents.
        if any(line.strip() == "class: build" for line in head):
            continue
        status = ""
        replacement = ""
        for line in head:
            stripped = line.strip()
            if stripped.startswith("status:"):
                status = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("deprecated_in_favor_of:"):
                replacement = stripped.split(":", 1)[1].strip()
        roster[child.name] = {
            "status": status,
            "replacement": replacement,
            "agent_md": agent_md,
        }

    # Names that appear in SKILL_MAP.md but have no agents/<id>/AGENT.md on
    # disk are recorded so the error message can say "documented but not on
    # disk" rather than "unknown agent".
    for name in map_agents:
        roster.setdefault(name, {"status": "", "replacement": "", "agent_md": None})

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

SECTION_HEADING_RE = re.compile(r"^#{2,3}\s+Section\s+(\d+)\s*[\u2014\-\u2013]\s*(.+?)\s*$")


def normalize_section_name(raw: str) -> str:
    """Loose-match a section heading to one of the canonical names."""
    cleaned = raw.strip()
    cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
    # Tolerate Automation variants like "Automation (Flow / Apex / Approvals)".
    if cleaned.lower().startswith("automation"):
        return "Automation"
    return cleaned


def parse_workbook(path: Path) -> dict:
    """Parse the workbook into `{"sections": …, "section_numbers": …}`.

    The parser only cares about Markdown table rows under each
    `## Section N — <name>` heading. The header row of each table is used
    to map columns to row dict keys.
    """
    if not path.exists():
        raise SystemExit(f"Workbook not found: {path}")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    sections: dict[str, list[dict]] = {}
    section_numbers: dict[str, int] = {}
    current_section: str | None = None
    table_header: list[str] | None = None
    in_table_body = False

    for raw_line in lines:
        line = raw_line.rstrip()

        heading_match = SECTION_HEADING_RE.match(line)
        if heading_match:
            current_section = normalize_section_name(heading_match.group(2))
            section_numbers[current_section] = int(heading_match.group(1))
            sections.setdefault(current_section, [])
            table_header = None
            in_table_body = False
            continue

        if current_section is None:
            continue

        # Markdown tables: header row, separator row, body rows.
        if line.startswith("|") and line.endswith("|"):
            cells = split_table_row(line)
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

    return {"sections": sections, "section_numbers": section_numbers}


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

def is_blank(value: str | None) -> bool:
    return value is None or not value.strip()


def artefact_tag(target_value: str) -> tuple[str, str]:
    """Pull the `` `Type:Name` `` (or bare `` `Type` ``) tag off a cell.

    Returns `(type, subtype)` — `("Flow", "")` for `` `Flow:MyFlow` ``,
    `("Settings", "BusinessHours")` for `` `Settings:BusinessHours` ``, or
    `("", "")` when the cell doesn't open with the tag convention at all
    (prose, a bare filename — a documentation artefact rather than a
    deployable component).
    """
    match = ARTEFACT_TAG_RE.match(target_value.strip())
    if not match:
        return "", ""
    return match.group(1), (match.group(2) or "").strip()


def automation_row_requires_tree_citation(target_value: str) -> bool:
    """Whether a Section 6 row must cite `automation-selection.md`.

    Only rows whose artefact is itself an automation-engine choice need the
    citation (references/gotchas.md Gotcha 12). An untagged row — one that
    doesn't open with the `` `Type:Name` `` convention — is a documentation
    artefact, not a deployable engine, so it is not required either. Queue,
    Group and `Settings:BusinessHours` rows are configuration in support of
    routing; nothing in the tree resolves "which Queue" or "which calendar
    shape".
    """
    art_type, sub_type = artefact_tag(target_value)
    if art_type == "Settings":
        return sub_type in AUTOMATION_SETTINGS_SUBTYPES
    return art_type in AUTOMATION_ENGINE_ARTEFACT_TYPES


# A `|` immediately preceded by `\` is a literal pipe inside a cell (e.g. a
# regex alternation), not a column boundary.
UNESCAPED_PIPE_RE = re.compile(r"(?<!\\)\|")


def split_table_row(line: str) -> list[str]:
    """Split one markdown table row into cells, honoring `\\|` as literal.

    A well-formed row starts and ends with an (unescaped) `|`; splitting on
    unescaped pipes only and dropping the resulting empty first/last element
    reproduces what `line.strip("|").split("|")` did for rows with no
    escaped pipes, while a cell that needs a literal `|` can now write `\\|`
    instead of breaking the column count.
    """
    parts = UNESCAPED_PIPE_RE.split(line.strip())
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return [cell.strip().replace("\\|", "|") for cell in parts]


def looks_like_secret(target_value: str) -> bool:
    return any(p.search(target_value) for p in SECRET_PATTERNS)


def split_skills(cell: str) -> list[str]:
    if not cell:
        return []
    # Accept ;, |, or newline as delimiters.
    parts = re.split(r"[;|\n]", cell)
    return [p.strip() for p in parts if p.strip()]


def skill_reference_path(repo_root: Path, reference: str) -> Path | None:
    """Map one `recommended_skills` entry to the file it must resolve to.

    Accepted shapes, all of which appear in real workbooks:

      admin/validation-rules                     -> skills/admin/validation-rules/SKILL.md
      admin/validation-rules -> references/x.md  -> that reference file
      admin/validation-rules § Bypass            -> the SKILL.md (section is prose)
      templates/admin/naming-conventions.md      -> the template itself
      standards/decision-trees/sharing-selection.md
      agents/flow-builder/AGENT.md

    Returns None when the entry is not a repo path at all (nothing to
    resolve) so the caller can report it as unresolvable rather than
    silently passing it.
    """
    ref = reference.strip().strip("`")
    if not ref:
        return None

    # "skill -> references/foo.md" and "skill → references/foo.md"
    sub_ref = ""
    for arrow in ("\u2192", "->"):
        if arrow in ref:
            ref, sub_ref = (part.strip() for part in ref.split(arrow, 1))
            break

    # Trim trailing prose: "§ Section", "Example 2", "(escalation XML)".
    ref = re.split(r"\s+(?:\u00a7|\(|Example\b|Step\b)", ref)[0].strip()
    ref = ref.rstrip(".,")

    if not ref:
        return None

    # Repo-relative paths to a concrete file.
    if ref.startswith(("templates/", "standards/", "agents/", "evals/", "knowledge/")):
        return repo_root / ref
    if ref.startswith("skills/"):
        ref = ref[len("skills/"):]

    parts = ref.split("/")
    if len(parts) != 2 or not all(re.fullmatch(r"[a-z0-9][a-z0-9\-.]*", part) for part in parts):
        return None

    skill_dir = repo_root / "skills" / parts[0] / parts[1]
    if sub_ref:
        candidate = skill_dir / sub_ref.strip("`")
        if candidate.exists():
            return candidate
        # A named reference file that does not exist is still a real
        # resolution target — return it so the caller reports the miss.
        if sub_ref.endswith(".md"):
            return candidate
    return skill_dir / "SKILL.md"


def normalize_agent_id(cell: str) -> str:
    """`audit-router --domain=sharing` -> `audit-router`.

    Everything after the first whitespace is invocation arguments, not part
    of the agent id (agents/config-workbook-author/AGENT.md, Step 6.1).
    """
    if not cell.strip():
        return ""
    head = cell.strip().strip("`").split()[0]
    # Trailing separators belong to the multi-agent check, not to the id.
    return head.rstrip(",;/+")


def check_row(
    row: dict,
    section: str,
    runtime_agents: dict[str, dict],
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    infos: list[str] = []
    row_id = row.get("row_id") or "(missing row_id)"

    # A section that is deliberately empty carries one row whose
    # target_value is `not-in-scope-this-release`. That row has no upstream
    # requirement and no downstream agent by construction, so it is held to
    # the identity fields only.
    out_of_scope = _is_out_of_scope(row.get("target_value") or "")
    required_fields = (
        ["row_id", "target_value", "owner", "status"]
        if out_of_scope
        else REQUIRED_ROW_FIELDS
    )
    for field in required_fields:
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

    agent_cell = (row.get("recommended_agent") or "").strip().strip("`")
    if agent_cell and agent_cell not in {"\u2014", "-"} and not out_of_scope:
        # One row, one agent. Split on the separators authors reach for when
        # they try to name two; `--domain=x` style args are stripped first so
        # `audit-router --domain=sharing` is not read as two agents.
        agent_head = normalize_agent_id(agent_cell)
        remainder = agent_cell[len(agent_head):].lstrip()
        candidates = [
            part.strip()
            for part in MULTI_AGENT_SEPARATORS.split(agent_cell)
            if part.strip()
        ]
        looks_multi = len(candidates) > 1 and any(
            candidate in runtime_agents for candidate in candidates[1:]
        )
        if looks_multi:
            issues.append(
                f"[{section}] row {row_id}: recommended_agent names more than "
                f"one agent ({agent_cell!r}) — one row, one agent, one "
                f"section. Split the row."
            )
        elif remainder and not remainder.startswith("-"):
            issues.append(
                f"[{section}] row {row_id}: recommended_agent `{agent_cell}` "
                f"carries text that is neither an agent id nor a `--flag` "
                f"argument — use the bare agent id, optionally followed by "
                f"invocation flags"
            )

        record = runtime_agents.get(agent_head)
        if looks_multi:
            # The split is the actionable finding; don't also complain that
            # "object-designer, flow-builder" isn't a roster entry.
            record = record or {"status": "", "replacement": "", "agent_md": True}
        if record is None:
            issues.append(
                f"[{section}] row {row_id}: recommended_agent `{agent_head}` "
                f"is not in the runtime roster (see agents/_shared/SKILL_MAP.md "
                f"and the agents/ directory)"
            )
        elif record.get("agent_md") is None:
            issues.append(
                f"[{section}] row {row_id}: recommended_agent `{agent_head}` "
                f"is named in agents/_shared/SKILL_MAP.md but has no "
                f"agents/{agent_head}/AGENT.md on disk"
            )
        elif record.get("status") == "deprecated":
            replacement = record.get("replacement") or "audit-router"
            issues.append(
                f"[{section}] row {row_id}: recommended_agent `{agent_head}` "
                f"is deprecated — route to `{replacement}` instead (see "
                f"agents/_shared/AGENT_DISAMBIGUATION.md for the "
                f"`--domain=` argument)"
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
    for skill_ref in skills:
        if skill_ref in {"—", "-", "n/a", "N/A"}:
            continue
        resolved = skill_reference_path(repo_root, skill_ref)
        if resolved is None:
            issues.append(
                f"[{section}] row {row_id}: recommended_skills entry "
                f"`{skill_ref}` is not a repo path — use `<domain>/<slug>` "
                f"(resolving to skills/<domain>/<slug>/SKILL.md) or a "
                f"repo-relative templates/ or standards/ path"
            )
        elif not resolved.exists():
            issues.append(
                f"[{section}] row {row_id}: recommended_skills entry "
                f"`{skill_ref}` does not resolve — "
                f"{resolved.relative_to(repo_root) if repo_root in resolved.parents else resolved}"
                f" does not exist"
            )

    target_value = row.get("target_value") or ""
    if target_value and looks_like_secret(target_value):
        issues.append(
            f"[{section}] row {row_id}: target_value appears to contain an "
            f"inline credential — replace with a Named Credential alias"
        )
    if target_value and SETUP_PATH_RE.search(target_value):
        issues.append(
            f"[{section}] row {row_id}: target_value reads as a Setup "
            f"navigation path, not a metadata component — a row is executed "
            f"and deployed by component fullName, and a click-path has none"
        )

    notes = row.get("notes") or ""
    required_tree = REQUIRED_TREE_CITATION.get(section)
    if required_tree and not is_blank(target_value) and not out_of_scope:
        needs_citation = True
        if section == "Automation":
            na_override = (
                NO_AUTOMATION_CHOICE_MARKER in notes.lower()
                or NO_AUTOMATION_CHOICE_MARKER in target_value.lower()
            )
            needs_citation = (
                automation_row_requires_tree_citation(target_value)
                and not na_override
            )
        cited = f"{required_tree}" in notes or f"{required_tree}" in target_value
        haystack = f"{notes} {target_value}"
        if not cited:
            if needs_citation:
                issues.append(
                    f"[{section}] row {row_id}: no `{required_tree}` citation — "
                    f"every {section} row must name the decision-tree branch "
                    f"that resolved the choice "
                    f"(standards/decision-trees/{required_tree})"
                )
            else:
                infos.append(
                    f"[{section}] row {row_id}: no automation choice to cite "
                    f"— artefact is configuration, not an automation-engine "
                    f"pick (references/gotchas.md Gotcha 12)"
                )
        elif needs_citation and not TREE_STEP_RE.search(haystack):
            issues.append(
                f"[{section}] row {row_id}: cites `{required_tree}` but names "
                f"no branch — add the step that resolved it (e.g. "
                f"`{required_tree} Q3`)"
            )

    if section == "Profiles + Permission Sets + PSGs" and target_value and not out_of_scope:
        lowered = target_value.lower()
        if (
            "profile" in lowered
            and GRANT_VERB_RE.search(target_value)
            and not any(element in lowered for element in PROFILE_ONLY_ELEMENTS)
        ):
            issues.append(
                f"[{section}] row {row_id}: target_value grants access via a "
                f"Profile. Permission sets are the grant model; a Profile row "
                f"is only correct for the profile-only residue "
                f"(loginHours, loginIpRanges, layoutAssignments, "
                f"categoryGroupVisibilities, loginFlows, the default app and "
                f"the default record type). See admin/permission-sets-vs-profiles."
            )

    return issues, infos


def _is_out_of_scope(target_value: str) -> bool:
    """Placeholder rows that mark a section deliberately empty."""
    return "not-in-scope-this-release" in target_value.lower()


# ---------------------------------------------------------------------------
# Top-level check
# ---------------------------------------------------------------------------

def check_workbook(
    workbook_path: Path,
    repo_root: Path,
    allow_empty_section: bool,
) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    infos: list[str] = []
    runtime_agents = load_runtime_agents(repo_root)
    parsed = parse_workbook(workbook_path)
    sections = parsed["sections"]
    section_numbers = parsed["section_numbers"]

    # Section numbering must match the canonical order, or "Section 4" and
    # "Section 6" in the review checklist point at the wrong tables.
    for position, canonical in enumerate(CANONICAL_SECTIONS, start=1):
        key = normalize_section_name(canonical)
        actual = section_numbers.get(key)
        if actual is not None and actual != position:
            issues.append(
                f"Section `{key}` is numbered {actual} but is canonical "
                f"section {position} — renumber; downstream references cite "
                f"sections by number."
            )

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
            row_issues, row_infos = check_row(row, section, runtime_agents, repo_root)
            issues.extend(row_issues)
            infos.extend(row_infos)

    # row_id uniqueness across the whole workbook — a duplicate id makes the
    # RTM linkage block ambiguous and silently drops one row from hand-off.
    seen: dict[str, str] = {}
    for section, rows in sections.items():
        for row in rows:
            row_id = (row.get("row_id") or "").strip().strip("`")
            if not row_id:
                continue
            if row_id in seen:
                issues.append(
                    f"[{section}] row {row_id}: duplicate row_id — already "
                    f"used in section `{seen[row_id]}`. row_id must be unique "
                    f"across the whole workbook."
                )
            else:
                seen[row_id] = section

    return issues, infos


def main() -> int:
    args = parse_args()
    workbook = Path(args.workbook).resolve()
    repo_root = discover_repo_root(args.repo_root)

    issues, infos = check_workbook(
        workbook_path=workbook,
        repo_root=repo_root,
        allow_empty_section=args.allow_empty_section,
    )

    for info in infos:
        print(f"INFO: {info}")

    if not issues:
        print(f"OK: workbook {workbook} passes all checks.")
        return 0

    for issue in issues:
        print(f"ERROR: {issue}", file=sys.stderr)
    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        sys.exit(1)
    sys.exit(0)
