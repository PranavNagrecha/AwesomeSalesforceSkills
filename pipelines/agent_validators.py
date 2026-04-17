"""Validation helpers for AGENT.md files, their frontmatter, and citations.

The checks here are the run-time equivalent of ``validators.py`` for skills:
structural gate, citation gate, MCP tool gate, and slash-command gate.

Design notes
------------
- No new required behavior for skills; all agent checks live here.
- The validator is conservative: it reports issues, it does not mutate files.
- Citation references are extracted with regexes tight enough to avoid false
  positives on prose (we skip lines that are obviously sentences, and we
  restrict to the "Mandatory Reads" + "Plan" + "Output Contract" sections).
- MCP tool names are sourced from ``server.py`` so additions there flow in
  automatically; no separate list to keep in sync.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .frontmatter import parse_markdown_with_frontmatter
from .validators import ValidationIssue, validate_with_jsonschema


# Run-time agents MUST have all 8 sections, in order.
RUNTIME_REQUIRED_SECTIONS_IN_ORDER = [
    "What This Agent Does",
    "Invocation",
    "Mandatory Reads Before Starting",
    "Inputs",
    "Plan",
    "Output Contract",
    "Escalation / Refusal Rules",
    "What This Agent Does NOT Do",
]

# Build-time agents operate under a lighter contract: caller-supplied
# `Inputs` and user-facing `Output Contract` / `Escalation` aren't always
# meaningful (they read queues, commit skills, route work). They MUST still
# declare what they are, how they're triggered, what they read first, and
# what they do — and they must document scope exclusions.
BUILD_REQUIRED_SECTIONS_IN_ORDER = [
    "What This Agent Does",
    "Invocation",
    "Mandatory Reads Before Starting",
    "Plan",
    "What This Agent Does NOT Do",
]

# Section aliases for legacy / alternate vocabulary across the repo.
SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "Invocation": ("Invocation", "Activation Triggers", "Triggers"),
    "Plan": ("Plan", "Orchestration Plan"),
    "Output Contract": ("Output Contract", "Output Format"),
    "What This Agent Does NOT Do": ("What This Agent Does NOT Do", "Anti-Patterns"),
    "Escalation / Refusal Rules": ("Escalation / Refusal Rules", "Escalation Rules"),
}


@dataclass(frozen=True)
class AgentParse:
    path: Path
    slug: str
    frontmatter: dict
    body: str
    sections: dict[str, tuple[int, str]]  # heading -> (line_index, body_between_this_and_next_h2)


def _agent_frontmatter_schema_path(root: Path) -> Path:
    return root / "agents" / "_shared" / "schemas" / "agent-frontmatter.schema.json"


def _discover_agents(root: Path) -> list[Path]:
    agents_root = root / "agents"
    agents: list[Path] = []
    if not agents_root.exists():
        return agents
    for entry in sorted(agents_root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith((".", "_")):
            continue
        md = entry / "AGENT.md"
        if md.exists():
            agents.append(md)
    return agents


def _canonicalize_heading(raw: str) -> str:
    """Strip a trailing parenthetical or em-dash clarifier from a heading.

    `## Inputs (ask for all three upfront)` -> `Inputs`
    `## Plan — step-by-step` -> `Plan`
    """
    text = raw.strip()
    for sep in ("(", " — ", " - "):
        if sep in text:
            text = text.split(sep, 1)[0].strip()
    return text


def _split_sections(body: str) -> dict[str, tuple[int, str]]:
    """Split the markdown body into {h2_heading: (line_index, content_until_next_h2)}.

    Heading keys are canonicalized: any trailing parenthetical or em-dash clarifier
    (e.g. `## Inputs (ask for all three upfront)`) is stripped so section lookups by
    canonical name always succeed.
    """
    lines = body.splitlines()
    heading_indices: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            heading_indices.append((idx, _canonicalize_heading(m.group(1))))

    sections: dict[str, tuple[int, str]] = {}
    for position, (idx, heading) in enumerate(heading_indices):
        start = idx + 1
        end = heading_indices[position + 1][0] if position + 1 < len(heading_indices) else len(lines)
        content = "\n".join(lines[start:end])
        if heading not in sections:
            sections[heading] = (idx, content)
    return sections


def _parse_agent(path: Path) -> tuple[AgentParse | None, list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    try:
        parsed = parse_markdown_with_frontmatter(path)
    except ValueError as exc:
        issues.append(ValidationIssue("ERROR", str(path), f"frontmatter: {exc}"))
        return None, issues
    except Exception as exc:  # pragma: no cover - guard for YAML edge cases
        issues.append(ValidationIssue("ERROR", str(path), f"unable to parse frontmatter: {exc}"))
        return None, issues

    sections = _split_sections(parsed.body)
    slug = path.parent.name
    return (
        AgentParse(path=path, slug=slug, frontmatter=parsed.metadata, body=parsed.body, sections=sections),
        issues,
    )


def _validate_frontmatter(root: Path, parse: AgentParse) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    schema_path = _agent_frontmatter_schema_path(root)
    if not schema_path.exists():
        issues.append(
            ValidationIssue(
                "ERROR",
                str(schema_path),
                "missing agent frontmatter schema — run `git pull` or restore agents/_shared/schemas/",
            )
        )
        return issues

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    for error in validate_with_jsonschema(parse.frontmatter, schema):
        issues.append(ValidationIssue("ERROR", str(parse.path), f"frontmatter: {error}"))

    declared_id = parse.frontmatter.get("id")
    if declared_id and declared_id != parse.slug:
        issues.append(
            ValidationIssue(
                "ERROR",
                str(parse.path),
                f"frontmatter `id: {declared_id}` does not match folder name `{parse.slug}`",
            )
        )
    return issues


def _validate_sections(parse: AgentParse) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    headings_in_order = [heading for heading, _ in sorted(parse.sections.items(), key=lambda item: item[1][0])]

    agent_class = parse.frontmatter.get("class", "runtime")
    required = (
        BUILD_REQUIRED_SECTIONS_IN_ORDER
        if agent_class == "build"
        else RUNTIME_REQUIRED_SECTIONS_IN_ORDER
    )

    found_positions: list[int] = []
    for section in required:
        accepted = SECTION_ALIASES.get(section, (section,))
        matched = next((heading for heading in accepted if heading in parse.sections), None)
        if matched is None:
            aliases_note = f" (or alias {list(accepted[1:])})" if len(accepted) > 1 else ""
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(parse.path),
                    f"missing required section `## {section}`{aliases_note}",
                )
            )
            continue
        found_positions.append(headings_in_order.index(matched))

    if len(found_positions) == len(required) and found_positions != sorted(found_positions):
        issues.append(
            ValidationIssue(
                "ERROR",
                str(parse.path),
                "required sections are present but not in the canonical order defined by AGENT_CONTRACT.md",
            )
        )
    return issues


# Citation regexes — tuned to be conservative.
# Skills: `skills/<domain>/<slug>` or `<domain>/<slug>` bare when quoted in prose; we only
# match the backticked form to avoid prose false positives.
_CITATION_PATTERNS = {
    "skill": re.compile(r"`skills/([a-z0-9-]+)/([a-z0-9-]+)(?:/[A-Za-z0-9_./-]*)?`"),
    "skill_bare": re.compile(r"`([a-z0-9-]+)/([a-z0-9-]+)`"),  # e.g. `admin/permission-set-architecture`
    "template": re.compile(r"`templates/([A-Za-z0-9_./-]+)`"),
    "standard": re.compile(r"`standards/([A-Za-z0-9_./-]+)`"),
    "probe": re.compile(r"`agents/_shared/probes/([a-z0-9-]+)(?:\.md)?`"),
    "followup_agent": re.compile(r"`agents/([a-z0-9-]+)(?:/AGENT\.md)?`"),
    "slash_command": re.compile(r"\[`/([a-z0-9-]+)`\]\(\.\./\.\./commands/([a-z0-9-]+)\.md\)"),
}


_SKILL_DOMAINS = {
    "admin", "apex", "lwc", "flow", "omnistudio", "agentforce",
    "security", "integration", "data", "devops", "architect",
}


def _extract_mcp_tool_names(server_py: Path) -> set[str]:
    if not server_py.exists():
        return set()
    try:
        tree = ast.parse(server_py.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    tools: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_tool = False
        if isinstance(func, ast.Attribute) and func.attr == "tool":
            is_tool = True
        if not is_tool:
            continue
        for kw in node.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                tools.add(kw.value.value)
    return tools


def _validate_citations(root: Path, parse: AgentParse, known_agents: set[str], mcp_tools: set[str]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    body = parse.body

    for match in _CITATION_PATTERNS["skill"].finditer(body):
        domain, slug = match.group(1), match.group(2)
        if domain not in _SKILL_DOMAINS:
            continue  # path doesn't start with a real skill domain — not a skill citation
        candidate = root / "skills" / domain / slug
        if not candidate.exists():
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(parse.path),
                    f"citation `skills/{domain}/{slug}` does not resolve to a skill folder",
                )
            )

    for match in _CITATION_PATTERNS["skill_bare"].finditer(body):
        domain, slug = match.group(1), match.group(2)
        if domain not in _SKILL_DOMAINS:
            continue
        candidate = root / "skills" / domain / slug
        if not candidate.exists():
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(parse.path),
                    f"citation `{domain}/{slug}` does not resolve to skills/{domain}/{slug}/",
                )
            )

    for match in _CITATION_PATTERNS["template"].finditer(body):
        rel = match.group(1)
        candidate = root / "templates" / rel
        if not candidate.exists():
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(parse.path),
                    f"citation `templates/{rel}` does not resolve to a real file/folder",
                )
            )

    for match in _CITATION_PATTERNS["standard"].finditer(body):
        rel = match.group(1)
        candidate = root / "standards" / rel
        if not candidate.exists():
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(parse.path),
                    f"citation `standards/{rel}` does not resolve to a real file",
                )
            )

    for match in _CITATION_PATTERNS["probe"].finditer(body):
        probe_id = match.group(1)
        candidate = root / "agents" / "_shared" / "probes" / f"{probe_id}.md"
        if not candidate.exists():
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(parse.path),
                    f"citation `agents/_shared/probes/{probe_id}` does not resolve to a probe md file",
                )
            )

    for match in _CITATION_PATTERNS["followup_agent"].finditer(body):
        agent_slug = match.group(1)
        if agent_slug.startswith("_"):
            continue
        if agent_slug == parse.slug:
            continue
        if agent_slug not in known_agents:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(parse.path),
                    f"follow-up reference `agents/{agent_slug}` does not resolve to a real agent folder",
                )
            )

    for match in _CITATION_PATTERNS["slash_command"].finditer(body):
        cmd = match.group(2)
        candidate = root / "commands" / f"{cmd}.md"
        if not candidate.exists():
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(parse.path),
                    f"slash command `/{cmd}` does not resolve to commands/{cmd}.md",
                )
            )

    # MCP tool validation — only in Plan / Output Contract sections to avoid false positives in prose.
    plan_body = _section_body(parse, "Plan") + "\n" + _section_body(parse, "Output Contract")
    for candidate_tool in re.findall(r"`([a-z_]+)\s*\(", plan_body):
        # Heuristic: only flag if it looks like an MCP tool call (e.g. tooling_query(...),
        # list_permission_sets(...)) and is not a known Salesforce function name we should
        # ignore. We restrict failure to names that are *close* to real MCP tools but not
        # actually registered.
        if candidate_tool in {"describe_permission_set", "tooling_query", "list_permission_sets",
                              "list_validation_rules", "list_record_types", "list_named_credentials",
                              "list_approval_processes", "describe_org", "list_custom_objects",
                              "list_flows_on_object", "validate_against_org", "search_skill",
                              "get_skill", "list_agents", "get_agent"}:
            if mcp_tools and candidate_tool not in mcp_tools:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        str(parse.path),
                        f"MCP tool `{candidate_tool}` cited but not registered in mcp/sfskills-mcp/src/sfskills_mcp/server.py",
                    )
                )

    return issues


def _section_body(parse: AgentParse, heading: str) -> str:
    accepted = SECTION_ALIASES.get(heading, (heading,))
    for name in accepted:
        if name in parse.sections:
            return parse.sections[name][1]
    return ""


def _validate_inputs_schema(path: Path, agent_dir: Path) -> list[ValidationIssue]:
    schema_file = agent_dir / "inputs.schema.json"
    if not schema_file.exists():
        return []  # optional
    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [ValidationIssue("ERROR", str(schema_file), f"inputs.schema.json: invalid JSON ({exc})")]
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return [ValidationIssue("ERROR", str(schema_file), "inputs.schema.json must be a JSON Schema object")]
    if "properties" not in schema or not isinstance(schema["properties"], dict) or not schema["properties"]:
        return [ValidationIssue("ERROR", str(schema_file), "inputs.schema.json must define `properties` with at least one input")]
    return []


def validate_agents(root: Path) -> list[ValidationIssue]:
    """Run every agent check against the repo.

    Returns a list of issues. Empty list = clean.
    """
    issues: list[ValidationIssue] = []

    agent_md_paths = _discover_agents(root)
    known_agents = {path.parent.name for path in agent_md_paths}
    mcp_tools = _extract_mcp_tool_names(
        root / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp" / "server.py"
    )

    seen_ids: dict[str, Path] = {}
    for md_path in agent_md_paths:
        parse, parse_issues = _parse_agent(md_path)
        issues.extend(parse_issues)
        if parse is None:
            continue

        issues.extend(_validate_frontmatter(root, parse))
        issues.extend(_validate_sections(parse))
        issues.extend(_validate_citations(root, parse, known_agents, mcp_tools))
        issues.extend(_validate_inputs_schema(md_path, md_path.parent))

        declared_id = parse.frontmatter.get("id")
        if declared_id:
            if declared_id in seen_ids:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        str(md_path),
                        f"duplicate agent id `{declared_id}` — also declared at {seen_ids[declared_id]}",
                    )
                )
            else:
                seen_ids[declared_id] = md_path

    # Every run-time agent in the MCP roster must have a matching AGENT.md. We read the
    # roster from the agents module by regex to avoid importing it (and its MCP deps).
    agents_module = root / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp" / "agents.py"
    if agents_module.exists():
        runtime_listed = set(re.findall(r'"([a-z][a-z0-9-]+)"', agents_module.read_text(encoding="utf-8")))
        runtime_listed = {name for name in runtime_listed if name in known_agents}
        missing_md = runtime_listed - known_agents
        for slug in missing_md:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(agents_module),
                    f"agents.py lists runtime agent `{slug}` but agents/{slug}/AGENT.md does not exist",
                )
            )

    return issues


def summarize_agents(root: Path) -> Iterable[str]:
    agent_md_paths = _discover_agents(root)
    yield f"Discovered {len(agent_md_paths)} AGENT.md files under {root / 'agents'}"
