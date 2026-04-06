"""Validation helpers for skills, manifests, and generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .frontmatter import parse_markdown_with_frontmatter

try:
    import jsonschema
except Exception:  # pragma: no cover - optional dependency fallback
    jsonschema = None


ALLOWED_CATEGORIES = {
    "admin",
    "apex",
    "lwc",
    "flow",
    "omnistudio",
    "agentforce",
    "security",
    "integration",
    "data",
    "devops",
    "architect",
}
REQUIRED_FRONTMATTER_KEYS = [
    "name",
    "description",
    "category",
    "salesforce-version",
    "well-architected-pillars",
    "tags",
    "triggers",
    "inputs",
    "outputs",
    "dependencies",
    "version",
    "author",
    "updated",
]
SKILL_BODY_MIN_WORDS = 300

REQUIRED_SKILL_FILES = [
    "SKILL.md",
    "references/examples.md",
    "references/gotchas.md",
    "references/well-architected.md",
]


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    path: str
    message: str


def load_schema(root: Path, relative_path: str) -> dict:
    return json.loads((root / relative_path).read_text(encoding="utf-8"))


def validate_with_jsonschema(instance: dict, schema: dict) -> list[str]:
    if jsonschema is None:
        return []
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in sorted(validator.iter_errors(instance), key=lambda item: item.path)]


def validate_frontmatter(root: Path, path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    parsed = parse_markdown_with_frontmatter(path)
    metadata = parsed.metadata
    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in metadata:
            issues.append(ValidationIssue("ERROR", str(path), f"missing frontmatter key `{key}`"))

    if metadata.get("category") not in ALLOWED_CATEGORIES:
        issues.append(ValidationIssue("ERROR", str(path), "invalid category"))

    for key in ("tags", "triggers", "inputs", "outputs", "dependencies", "well-architected-pillars"):
        if key in metadata and not isinstance(metadata[key], list):
            issues.append(ValidationIssue("ERROR", str(path), f"`{key}` must be a list"))

    # name must match the folder name so skill IDs are deterministic and unambiguous
    folder_name = path.parent.name
    if metadata.get("name") and metadata["name"] != folder_name:
        issues.append(ValidationIssue("ERROR", str(path), f"`name` frontmatter `{metadata['name']}` does not match folder name `{folder_name}`"))

    # category must match the parent domain folder so the skill is in the right place
    parent_domain = path.parent.parent.name
    if metadata.get("category") and metadata["category"] != parent_domain:
        issues.append(ValidationIssue("ERROR", str(path), f"`category` frontmatter `{metadata['category']}` does not match parent domain folder `{parent_domain}`"))

    # description must include an explicit scope exclusion ("NOT for ...") so the
    # trigger boundary is clear and the skill doesn't activate for wrong queries
    desc = metadata.get("description", "")
    if desc and "NOT" not in desc:
        issues.append(ValidationIssue("ERROR", str(path), "`description` must include a scope exclusion (e.g. 'NOT for ...')"))

    # frontmatter fields must not contain unfilled scaffold markers
    for key in ("description", "tags", "triggers", "inputs", "outputs"):
        value = metadata.get(key, "")
        if isinstance(value, str) and "TODO" in value:
            issues.append(ValidationIssue("ERROR", str(path), f"`{key}` contains an unfilled TODO marker; replace with real content"))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.startswith("TODO"):
                    issues.append(ValidationIssue("ERROR", str(path), f"`{key}` contains an unfilled TODO marker; replace with real content"))
                    break

    # body must have enough content to be useful — catches empty stubs from agents
    word_count = len(parsed.body.split())
    if word_count < SKILL_BODY_MIN_WORDS:
        issues.append(ValidationIssue("ERROR", str(path), f"SKILL.md body has {word_count} words; minimum is {SKILL_BODY_MIN_WORDS}"))

    # body must not contain unfilled scaffold markers — catches Codex submitting TODOs verbatim
    todo_lines = [line.strip() for line in parsed.body.splitlines() if "TODO:" in line and not line.strip().startswith("<!--")]
    if todo_lines:
        issues.append(ValidationIssue("ERROR", str(path), f"SKILL.md body contains {len(todo_lines)} unfilled TODO marker(s); replace all TODOs with real content before syncing"))

    schema = load_schema(root, "config/skill-frontmatter.schema.json")
    for error in validate_with_jsonschema(metadata, schema):
        issues.append(ValidationIssue("ERROR", str(path), error))
    return issues


def _validate_checker_script_content(script: Path) -> list[ValidationIssue]:
    """Detect always-pass stubs in skill checker scripts.

    A real checker must have:
    - At least 10 meaningful lines (non-blank, non-comment, non-shebang)
    - At least one conditional branch (`if` keyword)
    - At least one error-output path (sys.exit(1), raise, or ISSUE/WARN/ERROR print)
    """
    issues: list[ValidationIssue] = []
    try:
        source = script.read_text(encoding="utf-8")
    except OSError:
        return issues

    lines = source.splitlines()
    meaningful = [
        ln for ln in lines
        if ln.strip() and not ln.strip().startswith("#") and not ln.strip().startswith("#!/")
    ]

    if len(meaningful) < 10:
        issues.append(ValidationIssue(
            "WARN",
            str(script),
            f"checker script has only {len(meaningful)} meaningful lines — may be a stub; implement real validation logic",
        ))
        return issues  # skip further checks on very small files

    has_conditional = any("if " in ln or "elif " in ln for ln in meaningful)
    has_error_path = any(
        "sys.exit(1)" in ln
        or "raise " in ln
        or ("print(" in ln and any(kw in ln.upper() for kw in ("ERROR", "ISSUE", "WARN", "FAIL")))
        for ln in meaningful
    )

    if not has_conditional:
        issues.append(ValidationIssue(
            "WARN",
            str(script),
            "checker script has no conditional branches (`if`); it will always produce the same output regardless of input",
        ))
    if not has_error_path:
        issues.append(ValidationIssue(
            "WARN",
            str(script),
            "checker script has no error-output path (sys.exit(1), raise, or ERROR/ISSUE/WARN print); it may never report problems",
        ))
    return issues


def validate_skill_structure(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for relative_path in REQUIRED_SKILL_FILES:
        candidate = path / relative_path
        if not candidate.exists():
            issues.append(ValidationIssue("ERROR", str(path), f"missing required file `{relative_path}`"))

    templates_dir = path / "templates"
    scripts_dir = path / "scripts"
    if not templates_dir.exists() or not any(item.is_file() for item in templates_dir.iterdir()):
        issues.append(ValidationIssue("ERROR", str(path), "templates/ must contain at least one file"))
    if not scripts_dir.exists() or not any(item.is_file() and item.suffix == ".py" for item in scripts_dir.iterdir()):
        issues.append(ValidationIssue("ERROR", str(path), "scripts/ must contain at least one Python file"))
    else:
        for script in scripts_dir.iterdir():
            if script.is_file() and script.suffix == ".py":
                issues.extend(_validate_checker_script_content(script))

    # LLM anti-patterns file — ERROR if missing or still has TODOs
    llm_ap_path = path / "references" / "llm-anti-patterns.md"
    if not llm_ap_path.exists():
        issues.append(ValidationIssue("ERROR", str(path), "missing `references/llm-anti-patterns.md` — add LLM-specific anti-patterns for this skill"))
    else:
        llm_text = llm_ap_path.read_text(encoding="utf-8")
        llm_todo_lines = [ln for ln in llm_text.splitlines() if "TODO:" in ln and not ln.strip().startswith("<!--")]
        if llm_todo_lines:
            issues.append(ValidationIssue("ERROR", str(llm_ap_path), f"llm-anti-patterns.md contains {len(llm_todo_lines)} unfilled TODO marker(s)"))

    # Recommended Workflow section in SKILL.md — WARN if missing
    skill_md_path = path / "SKILL.md"
    if skill_md_path.exists():
        skill_text = skill_md_path.read_text(encoding="utf-8")
        if "## Recommended Workflow" not in skill_text:
            issues.append(ValidationIssue("WARN", str(skill_md_path), "SKILL.md has no `## Recommended Workflow` section — add step-by-step agent instructions"))

    waf_path = path / "references" / "well-architected.md"
    if waf_path.exists():
        text = waf_path.read_text(encoding="utf-8")
        if "## Official Sources Used" not in text:
            issues.append(ValidationIssue("ERROR", str(waf_path), "missing `## Official Sources Used` section"))
        else:
            # Heading presence is not enough — there must be at least one non-empty
            # line of content after it (a real source, not just the heading itself)
            after_heading = text.split("## Official Sources Used", 1)[1].strip()
            if not after_heading:
                issues.append(ValidationIssue("ERROR", str(waf_path), "`## Official Sources Used` section is empty; list at least one source"))
    return issues


def validate_skill_registry_record(root: Path, record: dict) -> list[ValidationIssue]:
    schema = load_schema(root, "config/skill-record.schema.json")
    return [
        ValidationIssue("ERROR", record.get("file_location", "registry"), error)
        for error in validate_with_jsonschema(record, schema)
    ]


def validate_knowledge_source(root: Path, source: dict) -> list[ValidationIssue]:
    schema = load_schema(root, "config/knowledge-source.schema.json")
    return [ValidationIssue("ERROR", source.get("id", "knowledge"), error) for error in validate_with_jsonschema(source, schema)]
