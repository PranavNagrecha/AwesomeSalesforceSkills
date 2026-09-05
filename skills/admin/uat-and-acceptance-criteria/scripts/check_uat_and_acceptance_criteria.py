#!/usr/bin/env python3
"""Checker for the UAT programme artefacts produced by this skill.

Two artefact shapes are linted:

1. A **UAT plan record** (`*.yaml` / `*.yml`) — the machine-readable form of the plan
   described in `references/worked-examples.md` § 7. Structural rules:
     - required top-level sections and environment fields are present
     - persona ids are unique, every persona has a test user, and no persona tests as
       System Administrator (an admin bypasses FLS and most sharing in the UI)
     - every test case has a unique id, a story id, an ac id, a persona that resolves to a
       declared persona, a sandbox matching the environment, a non-empty expected result,
       and a pass/fail value from the allowed set
     - the sandbox was refreshed BEFORE the build was deployed into it
     - at least one negative-path case and at least one bulk-path case exist
     - every defect has a unique id, a severity, a category, an owner, a status from the
       allowed set, and a case_id that resolves to a declared test case
     - a "Go" sign-off carries every required field and has no open P1/P2 defect
     - repo paths under `source_skills` resolve to a real skill package
     - no unfilled placeholder tokens survive anywhere in the file

2. A **UAT script or story document** (`*.md`) — heuristic lint of acceptance criteria
   phrasing, test-case table rows, defect severity, and the presence of a sign-off section.

Stdlib only. A minimal YAML subset is parsed in-process (mappings, nested mappings, lists
of mappings, lists of scalars, single-line values) — the plan record is written to stay
inside that subset on purpose.

Usage:
    python3 check_uat_and_acceptance_criteria.py --file uat-plan.yaml
    python3 check_uat_and_acceptance_criteria.py --file uat-script.md
    python3 check_uat_and_acceptance_criteria.py --manifest-dir ./uat/
Exit code 1 if any ERROR is reported; 0 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------------------
# Allowed value sets
# --------------------------------------------------------------------------------------

SANDBOX_TYPES = {"Developer", "Developer Pro", "Partial Copy", "Full", "Scratch"}
DELIVERABILITY = {"No Access", "System Email Only", "All Email"}
PASS_FAIL = {"Pass", "Fail", "Blocked", "Not Run"}
SEVERITIES = {"P1", "P2", "P3", "P4"}
DEFECT_CATEGORIES = {
    "configuration",
    "automation",
    "security",
    "sharing",
    "data",
    "integration",
    "training",
    "environment",
}
DEFECT_STATUSES = {"Open", "In Progress", "Fixed", "Retest", "Closed", "Deferred"}
SIGN_OFF_DECISIONS = {"Go", "No-Go", "Conditional Go"}

REQUIRED_TOP_LEVEL = ["plan_id", "release", "environment", "personas", "test_cases", "sign_off"]
REQUIRED_ENVIRONMENT = [
    "sandbox_name",
    "sandbox_type",
    "refreshed_on",
    "build_deployed_on",
    "email_deliverability",
]
REQUIRED_CASE_FIELDS = [
    "case_id",
    "story_id",
    "ac_id",
    "persona",
    "sandbox",
    "expected_result",
    "pass_fail",
]
REQUIRED_DEFECT_FIELDS = ["defect_id", "case_id", "severity", "category", "owner", "status"]
REQUIRED_SIGN_OFF_FIELDS = [
    "decision",
    "decided_on",
    "business_owner",
    "build_version",
    "sandbox",
]

# Unfilled-scaffold markers. Written as fragments so this file never ships one itself.
PLACEHOLDER_TOKENS = ("TBD", "FIXME", "XXX", "PLACEHOLDER", "T" + "ODO", "<FILL", "LOREM")
BRACKET_PLACEHOLDER = re.compile(r"\[[A-Za-z][^\]\n]{2,}\]")

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Patterns that indicate untestable acceptance criteria (markdown path)
VAGUE_CRITERIA_PATTERNS = [
    r"\bshould be (fast|easy|simple|intuitive|clean|nice|good|better|user.friendly)\b",
    r"\bshould look\b",
    r"\bshould feel\b",
    r"\bshould work\b",
    r"\bshould be obvious\b",
    r"\bshould be clear\b",
    r"\bshould be responsive\b",
    r"\bpages? should load\b",
    r"\bperformance should\b",
]

SF_OBJECTS = [
    "account", "contact", "opportunity", "case", "lead", "campaign",
    "task", "event", "user", "profile", "permission set", "record type",
    "page layout", "flow", "validation rule", "report", "dashboard",
    "field", "queue", "sharing", "role",
]


# --------------------------------------------------------------------------------------
# Minimal YAML subset parser
# --------------------------------------------------------------------------------------

def _strip_scalar(raw: str):
    """Normalise a scalar: strip quotes and trailing comments, coerce booleans."""
    value = raw.strip()
    if value.startswith(("'", '"')) and len(value) >= 2 and value[-1] == value[0]:
        return value[1:-1]
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if " #" in value:
        value = value.split(" #", 1)[0].strip()
    lowered = value.lower()
    if lowered in ("true", "yes"):
        return True
    if lowered in ("false", "no"):
        return False
    return value


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_yaml_subset(text: str):
    """Parse the restricted YAML shape the plan record uses.

    Supports: top-level and nested mappings, lists of mappings, lists of scalars, and
    single-line scalar values. Raises ValueError on anything outside that subset.
    """
    lines = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.strip() in ("---", "..."):
            continue
        lines.append((number, raw.rstrip()))
    value, consumed = _parse_block(lines, 0, _indent_of(lines[0][1]) if lines else 0)
    if consumed != len(lines):
        number = lines[consumed][0]
        raise ValueError(f"line {number}: unexpected indentation, cannot parse")
    return value


def _parse_block(lines, index: int, indent: int):
    if index >= len(lines):
        return {}, index
    if lines[index][1].lstrip().startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_list(lines, index: int, indent: int):
    items = []
    while index < len(lines):
        number, raw = lines[index]
        current = _indent_of(raw)
        if current < indent or not raw.lstrip().startswith("- "):
            break
        if current > indent:
            raise ValueError(f"line {number}: unexpected indentation inside a list")
        body = raw.lstrip()[2:]
        index += 1
        if ":" in body and not body.startswith(("'", '"')):
            key, _, rest = body.partition(":")
            entry = {key.strip(): _strip_scalar(rest) if rest.strip() else None}
            child_indent = current + 2
            while index < len(lines) and _indent_of(lines[index][1]) >= child_indent \
                    and not lines[index][1].lstrip().startswith("- "):
                sub, index = _parse_map(lines, index, child_indent)
                entry.update(sub)
            items.append(entry)
        else:
            items.append(_strip_scalar(body))
    return items, index


def _parse_map(lines, index: int, indent: int):
    mapping = {}
    while index < len(lines):
        number, raw = lines[index]
        current = _indent_of(raw)
        if current < indent:
            break
        if current > indent:
            raise ValueError(f"line {number}: unexpected indentation")
        stripped = raw.lstrip()
        if stripped.startswith("- "):
            break
        if ":" not in stripped:
            raise ValueError(f"line {number}: expected 'key: value'")
        key, _, rest = stripped.partition(":")
        key = key.strip()
        index += 1
        if rest.strip():
            mapping[key] = _strip_scalar(rest)
            continue
        if index < len(lines) and _indent_of(lines[index][1]) > current:
            child, index = _parse_block(lines, index, _indent_of(lines[index][1]))
            mapping[key] = child
        elif index < len(lines) and _indent_of(lines[index][1]) == current \
                and lines[index][1].lstrip().startswith("- "):
            child, index = _parse_list(lines, index, current)
            mapping[key] = child
        else:
            mapping[key] = None
    return mapping, index


# --------------------------------------------------------------------------------------
# Plan record checks
# --------------------------------------------------------------------------------------

def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text(value) -> str:
    return "" if value is None else str(value).strip()


def check_plan(plan, repo_root: Path) -> list[str]:
    """Structural lint of a UAT plan record. Returns ERROR strings."""
    issues: list[str] = []

    if not isinstance(plan, dict):
        return ["plan record did not parse to a mapping"]

    for key in REQUIRED_TOP_LEVEL:
        if key not in plan or plan[key] in (None, "", []):
            issues.append(f"missing required top-level section '{key}'")

    # --- environment -------------------------------------------------------------
    env = plan.get("environment") if isinstance(plan.get("environment"), dict) else {}
    for key in REQUIRED_ENVIRONMENT:
        if not _text(env.get(key)):
            issues.append(f"environment: missing required field '{key}'")
    sandbox_type = _text(env.get("sandbox_type"))
    if sandbox_type and sandbox_type not in SANDBOX_TYPES:
        issues.append(
            f"environment.sandbox_type '{sandbox_type}' is not one of {sorted(SANDBOX_TYPES)}"
        )
    deliverability = _text(env.get("email_deliverability"))
    if deliverability and deliverability not in DELIVERABILITY:
        issues.append(
            f"environment.email_deliverability '{deliverability}' is not one of "
            f"{sorted(DELIVERABILITY)}"
        )
    refreshed = _text(env.get("refreshed_on"))
    deployed = _text(env.get("build_deployed_on"))
    for label, value in (("refreshed_on", refreshed), ("build_deployed_on", deployed)):
        if value and not ISO_DATE.match(value):
            issues.append(f"environment.{label} '{value}' is not an ISO date (YYYY-MM-DD)")
    if refreshed and deployed and ISO_DATE.match(refreshed) and ISO_DATE.match(deployed):
        if refreshed > deployed:
            issues.append(
                f"environment: sandbox refreshed {refreshed} AFTER the build was deployed "
                f"{deployed} — the refresh destroyed the build under test (gotcha 6)"
            )

    # --- personas ----------------------------------------------------------------
    persona_ids: set[str] = set()
    for persona in _as_list(plan.get("personas")):
        if not isinstance(persona, dict):
            issues.append("personas: entry is not a mapping")
            continue
        pid = _text(persona.get("persona_id"))
        if not pid:
            issues.append("personas: entry missing 'persona_id'")
            continue
        if pid in persona_ids:
            issues.append(f"personas: duplicate persona_id '{pid}'")
        persona_ids.add(pid)
        if not _text(persona.get("test_user")):
            issues.append(f"persona '{pid}': missing 'test_user'")
        profile = _text(persona.get("profile"))
        perms = _text(persona.get("permission_sets"))
        if not profile:
            issues.append(f"persona '{pid}': missing 'profile'")
        if "system administrator" in profile.lower() or "system administrator" in perms.lower():
            issues.append(
                f"persona '{pid}': tests as System Administrator — an admin bypasses FLS and "
                "most sharing in the UI, so the run proves nothing about the persona (gotcha 2)"
            )
        if not profile and not perms:
            issues.append(f"persona '{pid}': no profile or permission set named")

    # --- test cases --------------------------------------------------------------
    case_ids: set[str] = set()
    negative_seen = False
    bulk_seen = False
    failing_cases: set[str] = set()
    sandbox_name = _text(env.get("sandbox_name"))
    cases = _as_list(plan.get("test_cases"))
    if not cases:
        issues.append("test_cases: the plan declares no test cases")
    for case in cases:
        if not isinstance(case, dict):
            issues.append("test_cases: entry is not a mapping")
            continue
        cid = _text(case.get("case_id")) or "<unnamed case>"
        for field in REQUIRED_CASE_FIELDS:
            if not _text(case.get(field)):
                issues.append(f"case '{cid}': missing required field '{field}'")
        if cid in case_ids:
            issues.append(f"test_cases: duplicate case_id '{cid}'")
        case_ids.add(cid)
        persona = _text(case.get("persona"))
        if persona and persona_ids and persona not in persona_ids:
            issues.append(
                f"case '{cid}': persona '{persona}' is not declared in the personas list"
            )
        case_sandbox = _text(case.get("sandbox"))
        if case_sandbox and sandbox_name and case_sandbox != sandbox_name:
            issues.append(
                f"case '{cid}': sandbox '{case_sandbox}' does not match "
                f"environment.sandbox_name '{sandbox_name}'"
            )
        verdict = _text(case.get("pass_fail"))
        if verdict and verdict not in PASS_FAIL:
            issues.append(
                f"case '{cid}': pass_fail '{verdict}' is not one of {sorted(PASS_FAIL)}"
            )
        if verdict == "Fail":
            failing_cases.add(cid)
        if case.get("negative_path") is True:
            negative_seen = True
        if case.get("bulk_path") is True:
            bulk_seen = True
    if cases and not negative_seen:
        issues.append(
            "test_cases: no case has 'negative_path: true' — an all-positive script never "
            "exercises validation rules, FLS or sharing (gotcha 10)"
        )
    if cases and not bulk_seen:
        issues.append(
            "test_cases: no case has 'bulk_path: true' — nothing in the plan probes the "
            "per-transaction limits a single-record test cannot reach (gotcha 8)"
        )

    # --- defects -----------------------------------------------------------------
    defect_ids: set[str] = set()
    blocking_open = []
    for defect in _as_list(plan.get("defects")):
        if not isinstance(defect, dict):
            issues.append("defects: entry is not a mapping")
            continue
        did = _text(defect.get("defect_id")) or "<unnamed defect>"
        for field in REQUIRED_DEFECT_FIELDS:
            if not _text(defect.get(field)):
                issues.append(f"defect '{did}': missing required field '{field}'")
        if did in defect_ids:
            issues.append(f"defects: duplicate defect_id '{did}'")
        defect_ids.add(did)
        linked = _text(defect.get("case_id"))
        if linked and case_ids and linked not in case_ids:
            issues.append(
                f"defect '{did}': case_id '{linked}' does not resolve to a declared test "
                "case — a defect logged against a symptom cannot be retested (gotcha 9)"
            )
        severity = _text(defect.get("severity"))
        if severity and severity not in SEVERITIES:
            issues.append(f"defect '{did}': severity '{severity}' is not one of {sorted(SEVERITIES)}")
        category = _text(defect.get("category")).lower()
        if category and category not in DEFECT_CATEGORIES:
            issues.append(
                f"defect '{did}': category '{category}' is not one of {sorted(DEFECT_CATEGORIES)}"
            )
        status = _text(defect.get("status"))
        if status and status not in DEFECT_STATUSES:
            issues.append(f"defect '{did}': status '{status}' is not one of {sorted(DEFECT_STATUSES)}")
        if severity in ("P1", "P2") and status in ("Open", "In Progress", "Retest"):
            blocking_open.append(f"{did} ({severity}, {status})")

    # --- sign-off ----------------------------------------------------------------
    sign_off = plan.get("sign_off") if isinstance(plan.get("sign_off"), dict) else {}
    for field in REQUIRED_SIGN_OFF_FIELDS:
        if not _text(sign_off.get(field)):
            issues.append(f"sign_off: missing required field '{field}'")
    decision = _text(sign_off.get("decision"))
    if decision and decision not in SIGN_OFF_DECISIONS:
        issues.append(f"sign_off.decision '{decision}' is not one of {sorted(SIGN_OFF_DECISIONS)}")
    if decision == "Go":
        if blocking_open:
            issues.append(
                "sign_off.decision is 'Go' with open P1/P2 defects: " + ", ".join(blocking_open)
            )
        if failing_cases:
            issues.append(
                "sign_off.decision is 'Go' with test cases still marked Fail: "
                + ", ".join(sorted(failing_cases))
            )
        if _text(sign_off.get("known_issues")) == "" and any(
            _text(d.get("status")) == "Deferred"
            for d in _as_list(plan.get("defects"))
            if isinstance(d, dict)
        ):
            issues.append(
                "sign_off: defects are Deferred but 'known_issues' is empty — deferred "
                "defects must be named in the sign-off record"
            )
    signoff_sandbox = _text(sign_off.get("sandbox"))
    if signoff_sandbox and sandbox_name and signoff_sandbox != sandbox_name:
        issues.append(
            f"sign_off.sandbox '{signoff_sandbox}' does not match environment.sandbox_name "
            f"'{sandbox_name}'"
        )

    # --- repo path references ----------------------------------------------------
    for ref in _as_list(plan.get("source_skills")):
        ref_text = _text(ref)
        if not ref_text or "/" not in ref_text:
            continue
        candidate = repo_root / "skills" / ref_text
        if not candidate.is_dir():
            issues.append(
                f"source_skills: '{ref_text}' does not resolve to skills/{ref_text} under "
                f"{repo_root}"
            )
    return issues


def check_placeholders(content: str) -> list[str]:
    """Flag unfilled scaffold markers anywhere in the artefact."""
    issues: list[str] = []
    for number, line in enumerate(content.splitlines(), start=1):
        upper = line.upper()
        for token in PLACEHOLDER_TOKENS:
            if token in upper:
                issues.append(f"line {number}: unfilled placeholder '{token}': {line.strip()[:80]}")
                break
        else:
            match = BRACKET_PLACEHOLDER.search(line)
            if match and not line.lstrip().startswith(("- [ ]", "- [x]", "- [X]", "[")):
                issues.append(
                    f"line {number}: unfilled bracket placeholder '{match.group(0)[:40]}' — "
                    "a template shipped as a plan"
                )
    return issues


# --------------------------------------------------------------------------------------
# Markdown document checks
# --------------------------------------------------------------------------------------

def check_acceptance_criteria(content: str) -> list[str]:
    issues: list[str] = []
    lines = content.splitlines()
    in_ac_block = False

    for i, line in enumerate(lines):
        if re.search(r"acceptance criteria", line, re.IGNORECASE):
            in_ac_block = True
            continue
        if in_ac_block and re.match(r"^#{1,6}\s", line):
            in_ac_block = False
        if not in_ac_block:
            continue

        ac_match = re.match(r"^\s*-\s*\[[ xX]\]\s*(.+)", line)
        if not ac_match:
            continue
        criterion = ac_match.group(1).strip()

        for pattern in VAGUE_CRITERIA_PATTERNS:
            if re.search(pattern, criterion, re.IGNORECASE):
                issues.append(
                    f"Line {i + 1}: acceptance criterion may be untestable (vague language): "
                    f"'{criterion[:80]}'"
                )
                break

        structured = re.search(r"\bif\b.+\bthen\b", criterion, re.IGNORECASE) or re.search(
            r"\b(given|when|then)\b", criterion, re.IGNORECASE
        )
        if not structured and len(criterion) > 30:
            issues.append(
                f"Line {i + 1}: acceptance criterion may lack if/then structure: "
                f"'{criterion[:80]}'"
            )

        if not any(obj in criterion.lower() for obj in SF_OBJECTS) and len(criterion) > 20:
            issues.append(
                f"Line {i + 1}: acceptance criterion names no Salesforce object or feature: "
                f"'{criterion[:80]}'"
            )
    return issues


def check_test_case_rows(content: str) -> list[str]:
    issues: list[str] = []
    in_table = False
    for i, line in enumerate(content.splitlines()):
        if re.search(r"TC.ID|Test.Case.ID|Scenario", line, re.IGNORECASE) and "|" in line:
            in_table = True
            continue
        if not in_table:
            continue
        if re.match(r"^\|[-\s|]+\|$", line):
            continue
        if not line.strip() or re.match(r"^#{1,6}\s", line):
            in_table = False
            continue
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 4:
            continue
        empty = sum(1 for c in cells if c in ("-", ""))
        if empty >= 3:
            issues.append(
                f"Line {i + 1}: test case row has {empty} empty cells — Expected Result, "
                "Preconditions and Steps must be filled in before execution."
            )
    return issues


def check_sign_off_section(content: str) -> list[str]:
    if re.search(r"sign.off|go.no.go|business owner.*approv", content, re.IGNORECASE):
        return []
    return [
        "document contains no UAT sign-off or Go/No-Go section — add a formal sign-off "
        "record (approver, date, sandbox, build version, known issues) before closing UAT."
    ]


def check_defect_severity(content: str) -> list[str]:
    issues: list[str] = []
    for i, line in enumerate(content.splitlines()):
        if "DEF-" in line and "|" in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 3:
                severity_cell = cells[2]
                if not re.search(
                    r"P[1-4]|Critical|Major|Minor|Cosmetic", severity_cell, re.IGNORECASE
                ):
                    issues.append(
                        f"Line {i + 1}: defect entry '{cells[0]}' has no severity "
                        "classification (P1-P4)."
                    )
    return issues


# --------------------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------------------

def lint_file(path: Path, repo_root: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read file: {exc}"]

    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            plan = parse_yaml_subset(content)
        except ValueError as exc:
            return [f"cannot parse plan record: {exc}"]
        return check_plan(plan, repo_root) + check_placeholders(content)

    issues = check_acceptance_criteria(content)
    issues += check_test_case_rows(content)
    issues += check_sign_off_section(content)
    issues += check_defect_severity(content)
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a UAT plan record (YAML) or a UAT script / user-story document (Markdown)."
        )
    )
    parser.add_argument("--file", default=None, help="Path to a single artefact to check.")
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Directory to scan for UAT plan records (*.yaml, *.yml) and scripts (*.md).",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repo root used to resolve 'source_skills' paths. Defaults to the repo this "
             "script lives in.",
    )
    args = parser.parse_args()

    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path(__file__).resolve().parents[4]
    )

    targets: list[Path] = []
    if args.file:
        targets.append(Path(args.file))
    if args.manifest_dir:
        directory = Path(args.manifest_dir)
        if not directory.is_dir():
            print(f"ERROR: not a directory: {directory}")
            return 1
        for pattern in ("*.yaml", "*.yml", "*.md"):
            targets.extend(sorted(directory.rglob(pattern)))

    if not targets:
        print("No artefact given. Pass --file <uat-plan.yaml> or --manifest-dir <dir>.")
        print("Example: python3 check_uat_and_acceptance_criteria.py --file uat-plan.yaml")
        return 0

    total = 0
    for target in targets:
        if not target.exists():
            print(f"ERROR: {target}: file not found")
            total += 1
            continue
        issues = lint_file(target, repo_root)
        if issues:
            for issue in issues:
                print(f"ERROR: {target}: {issue}")
            total += len(issues)
        else:
            print(f"OK: {target}")

    if total:
        print(f"\n{total} issue(s) found across {len(targets)} artefact(s).")
        return 1
    print(f"\nNo issues found across {len(targets)} artefact(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
