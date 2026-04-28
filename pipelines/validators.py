"""Validation helpers for skills, manifests, and generated artifacts."""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .frontmatter import parse_markdown_with_frontmatter

try:
    import jsonschema
except Exception:  # pragma: no cover - optional dependency fallback
    jsonschema = None


# Common drift aliases we see from authors cross-referencing other frameworks
# (notably AWS WAF). The validator still REJECTS these — it just prints a
# pointed hint so the fix is obvious. Adding an alias here is a deliberate
# decision to ship better error UX without weakening the contract.
_KNOWN_ENUM_ALIASES: dict[str, str] = {
    # AWS WAF pillar name → Salesforce-convention name we use in the enum.
    "Performance Efficiency": "Performance",
    # AWS WAF "Cost Optimization" is not a pillar in our enum at all; point
    # authors at the closest local equivalent so they don't guess.
    "Cost Optimization": "Operational Excellence",
    "Cost Efficiency": "Operational Excellence",
}


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
    messages: list[str] = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: item.path):
        messages.append(_humanize_jsonschema_error(error))
    return messages


def _humanize_jsonschema_error(error) -> str:
    """Turn a raw jsonschema error into a pointed, actionable message.

    Specifically: when the failure is an enum mismatch, append a 'did you
    mean X?' suggestion computed from (1) the known-alias table and
    (2) difflib.get_close_matches against the enum values. This converts
    a cryptic 'not one of [...]' into something a human can act on in one
    read.

    Falls back to the raw message when there's no obvious suggestion.
    """
    raw = error.message

    # Only enrich enum errors; leave other failure modes (type, required,
    # minLength, etc.) alone so we don't mask real issues.
    validator_name = getattr(error, "validator", None)
    if validator_name != "enum":
        return raw

    bad_value = error.instance
    if not isinstance(bad_value, str):
        return raw

    allowed = error.validator_value or []

    # First: check our known-alias table (e.g. AWS WAF → Salesforce names).
    hint = _KNOWN_ENUM_ALIASES.get(bad_value)
    if hint and hint in allowed:
        return (
            f"{raw} "
            f"— did you mean '{hint}'? "
            f"('{bad_value}' is the AWS WAF pillar name; "
            f"our enum uses Salesforce-convention names.)"
        )

    # Second: fuzzy match against the allowed list.
    close = difflib.get_close_matches(bad_value, allowed, n=1, cutoff=0.6)
    if close:
        return f"{raw} — did you mean '{close[0]}'?"

    return raw


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


def validate_skill_authoring_style(path: Path) -> list[ValidationIssue]:
    """Style-level checks against `standards/skill-authoring-style.md`.

    All findings are ERROR-level. The corpus was retrofitted to clear
    every flagged warning before promotion, so a hit now means a real
    regression — a new skill (or an edit) reintroduced one of the three
    duplication anti-patterns. The validator should fail the PR.

    Targets the three highest-confidence anti-patterns from § 6 of the
    guide — the ones that are objective duplication checks rather than
    subjective shape calls:

    - § 6.1 — `## When To Use` body section duplicating frontmatter
      `description:` (the description IS the trigger surface)
    - § 6.4 — pillar mapping inline in SKILL.md when
      `references/well-architected.md` exists
    - § 6.6 — verbatim paragraph appearing in both SKILL.md and
      `references/gotchas.md`
    """
    issues: list[ValidationIssue] = []
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return issues
    skill_text = skill_md.read_text(encoding="utf-8")

    # § 6.1 — duplicate "When To Use" section. Frontmatter `description:`
    # is already the canonical trigger surface; a body section repeats it.
    # Match H2 lines that *start with* the canonical phrase so extended
    # forms like `## When to use this skill` are caught while H3s like
    # `### When to Use Flow` (which appear as legitimate decision-tree
    # sub-headings) are not.
    when_to_use_re = re.compile(r"^## [Ww]hen [Tt]o [Uu]se\b.*$", re.MULTILINE)
    when_match = when_to_use_re.search(skill_text)
    if when_match:
        marker = when_match.group(0).strip()
        issues.append(
            ValidationIssue(
                "ERROR",
                str(skill_md),
                f"body has `{marker}` section — frontmatter `description` is the canonical trigger surface; "
                "remove the body section or fold it into the description "
                "(see standards/skill-authoring-style.md § 6.1)",
            )
        )

    # § 6.4 — pillar mapping inline in SKILL.md when a dedicated
    # references/well-architected.md exists with content. Map once, in
    # one place. H2-only to avoid sub-section false positives.
    waf_ref = path / "references" / "well-architected.md"
    has_waf_ref_content = (
        waf_ref.exists() and len(waf_ref.read_text(encoding="utf-8").strip()) > 200
    )
    pillar_heading_re = re.compile(
        r"^## (?:Well-Architected Pillars?(?: Mapping)?|Architecture Pillars?|Pillar Mapping)\b.*$",
        re.MULTILINE,
    )
    if has_waf_ref_content:
        pillar_match = pillar_heading_re.search(skill_text)
        if pillar_match:
            marker = pillar_match.group(0).strip()
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(skill_md),
                    f"body has `{marker}` section while `references/well-architected.md` already covers it — "
                    "keep pillar mapping in references/well-architected.md only "
                    "(see standards/skill-authoring-style.md § 6.4)",
                )
            )

    # § 6.6 — verbatim PROSE paragraph duplication between SKILL.md and
    # references/gotchas.md. Hash paragraphs >= ~120 chars to avoid
    # false-positives on short shared phrasing. Skip code fences and
    # source-list bullets (URLs are legitimately repeated across files).
    def _is_prose_paragraph(p: str) -> bool:
        stripped = p.strip()
        if len(stripped) < 120:
            return False
        if stripped.startswith("```"):
            return False  # code fence
        # citation list: every non-empty line is a `- ...http...` bullet
        lines = [ln for ln in stripped.split("\n") if ln.strip()]
        if lines and all(
            ln.lstrip().startswith(("- ", "* ", "+ ")) and "http" in ln
            for ln in lines
        ):
            return False
        return True

    gotchas_ref = path / "references" / "gotchas.md"
    if gotchas_ref.exists():
        gotchas_text = gotchas_ref.read_text(encoding="utf-8")
        skill_paragraphs = {
            p.strip()
            for p in skill_text.split("\n\n")
            if _is_prose_paragraph(p)
        }
        gotchas_paragraphs = {
            p.strip()
            for p in gotchas_text.split("\n\n")
            if _is_prose_paragraph(p)
        }
        shared = skill_paragraphs & gotchas_paragraphs
        if shared:
            sample = next(iter(shared))[:80].replace("\n", " ")
            issues.append(
                ValidationIssue(
                    "ERROR",
                    str(skill_md),
                    f"{len(shared)} paragraph(s) appear verbatim in both SKILL.md and references/gotchas.md "
                    f"(e.g. \"{sample}…\") — keep the deep version in references/gotchas.md, "
                    "leave a one-line summary + link in SKILL.md "
                    "(see standards/skill-authoring-style.md § 6.6)",
                )
            )

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
