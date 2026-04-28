#!/usr/bin/env python3
"""Validate a UAT test case file (or set) against the canonical schema.

Checks:
  - Every case has story_id + ac_id + persona (non-empty, persona not "System Administrator")
  - Every case has non-empty data_setup AND permission_setup arrays
  - Every case has steps with length >= 2
  - Every case's pass_fail is in {Pass, Fail, Blocked, Not Run} (case-insensitive)
  - Negative-path coverage: for every distinct story_id, >= 1 case has negative_path: true
  - Cases marked Pass or Fail must have a non-empty evidence_url

Stdlib only. Accepts JSON, CSV (pipe-delimited list cells), and Markdown
(rudimentary block parsing — see Format 1 in templates/uat-case.md).

Usage:
    python3 check_uat_case.py --help
    python3 check_uat_case.py --file cases.json
    python3 check_uat_case.py --file cases.csv --format csv
    python3 check_uat_case.py --file cases.md --format markdown
    python3 check_uat_case.py --rtm-gate --file cases.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PASS_FAIL_ENUM = {"pass", "fail", "blocked", "not run"}
REQUIRED_FIELDS = (
    "case_id",
    "story_id",
    "ac_id",
    "persona",
    "negative_path",
    "precondition",
    "data_setup",
    "permission_setup",
    "steps",
    "expected_result",
)
REJECTED_PERSONAS = {
    "system administrator",
    "admin",
    "internal user",
    "standard user",
}
LIST_FIELDS = ("data_setup", "permission_setup", "steps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate UAT test cases against the canonical schema "
            "(story_id, ac_id, persona, data_setup, permission_setup, steps, "
            "negative-path coverage, pass_fail enum)."
        ),
    )
    parser.add_argument(
        "--file",
        help="Path to a cases file (JSON, CSV, or Markdown). "
        "If omitted, reads JSON from stdin.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv", "markdown", "auto"),
        default="auto",
        help="Input format (default: auto, by extension).",
    )
    parser.add_argument(
        "--rtm-gate",
        action="store_true",
        help=(
            "Stricter pass: also require that for every story, at least one "
            "case is Passed AND at least one negative_path case is Passed."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _coerce_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        # CSV uses pipe-delimited list cells.
        return [chunk.strip() for chunk in value.split("|") if chunk.strip()]
    return []


def parse_json(text: str) -> list[dict]:
    data = json.loads(text)
    if isinstance(data, dict) and "cases" in data:
        return list(data["cases"])
    if isinstance(data, list):
        return data
    raise ValueError("JSON must be either a list of cases or an object with a 'cases' array.")


def parse_csv(text: str) -> list[dict]:
    reader = csv.DictReader(text.splitlines())
    cases: list[dict] = []
    for row in reader:
        case = dict(row)
        for field in LIST_FIELDS:
            case[field] = _coerce_list(case.get(field, ""))
        case["negative_path"] = _coerce_bool(case.get("negative_path", False))
        cases.append(case)
    return cases


_MD_HEADER_RE = re.compile(r"^###\s+Case\s+`?([A-Za-z0-9\-_]+)`?\s*$")
_MD_FIELD_RE = re.compile(r"^-\s+\*\*(\w+):\*\*\s*`?([^`]*)`?\s*$")
_MD_LIST_HEADER_RE = re.compile(r"^\*\*(\w+)\*\*\s*$")
_MD_NUMBERED_RE = re.compile(r"^\d+\.\s+`?(.+?)`?\s*$")
_MD_RUN_FIELD_RE = re.compile(r"^\*\*(\w+):\*\*\s*`?([^`]*)`?\s*$")


def parse_markdown(text: str) -> list[dict]:
    """Parse the markdown skeleton (Format 1) into case dicts.

    Tolerant — only intended to validate well-formed cases produced from the
    template. Not a general-purpose markdown parser.
    """
    cases: list[dict] = []
    current: dict | None = None
    list_field: str | None = None
    expected_buffer: list[str] = []
    in_expected = False

    for raw in text.splitlines():
        line = raw.rstrip()
        header = _MD_HEADER_RE.match(line)
        if header:
            if current is not None:
                if expected_buffer:
                    current.setdefault("expected_result", " ".join(expected_buffer).strip())
                cases.append(current)
            current = {
                "case_id": header.group(1),
                "data_setup": [],
                "permission_setup": [],
                "steps": [],
                "negative_path": False,
            }
            list_field = None
            expected_buffer = []
            in_expected = False
            continue
        if current is None:
            continue
        if line.startswith("> ") and in_expected:
            expected_buffer.append(line[2:].strip())
            continue
        list_header = _MD_LIST_HEADER_RE.match(line)
        if list_header and list_header.group(1) in LIST_FIELDS:
            list_field = list_header.group(1)
            in_expected = False
            continue
        if line.lower().startswith("**expected_result**"):
            list_field = None
            in_expected = True
            continue
        numbered = _MD_NUMBERED_RE.match(line)
        if numbered and list_field:
            current[list_field].append(numbered.group(1).strip())
            continue
        field_match = _MD_FIELD_RE.match(line) or _MD_RUN_FIELD_RE.match(line)
        if field_match:
            key = field_match.group(1).lower()
            value = field_match.group(2).strip()
            if key == "negative_path":
                current[key] = _coerce_bool(value)
            else:
                current[key] = value
            in_expected = False
            list_field = None
            continue

    if current is not None:
        if expected_buffer:
            current.setdefault("expected_result", " ".join(expected_buffer).strip())
        cases.append(current)
    return cases


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_cases(cases: list[dict], *, rtm_gate: bool = False) -> list[str]:
    issues: list[str] = []
    if not cases:
        issues.append("No cases found in input.")
        return issues

    seen_ids: set[str] = set()
    cases_by_story: dict[str, list[dict]] = {}

    for idx, case in enumerate(cases, start=1):
        case_label = case.get("case_id") or f"case[{idx}]"
        for field in REQUIRED_FIELDS:
            if field not in case or case[field] in (None, "", [], {}):
                issues.append(f"{case_label}: missing or empty required field '{field}'")

        case_id = str(case.get("case_id", "")).strip()
        if case_id and case_id in seen_ids:
            issues.append(f"{case_label}: duplicate case_id '{case_id}'")
        seen_ids.add(case_id)

        persona = str(case.get("persona", "")).strip()
        if persona and persona.lower() in REJECTED_PERSONAS:
            issues.append(
                f"{case_label}: persona '{persona}' is not allowed — name a specific profile + PSG"
            )

        for field in LIST_FIELDS:
            value = case.get(field)
            if isinstance(value, list) and not value:
                issues.append(f"{case_label}: list field '{field}' is empty")

        steps = case.get("steps") or []
        if isinstance(steps, list) and len(steps) < 2:
            issues.append(f"{case_label}: 'steps' must have at least 2 entries (got {len(steps)})")

        pass_fail = str(case.get("pass_fail", "Not Run")).strip().lower()
        if pass_fail and pass_fail not in PASS_FAIL_ENUM:
            issues.append(
                f"{case_label}: pass_fail '{case.get('pass_fail')}' not in "
                "{Pass, Fail, Blocked, Not Run}"
            )

        if pass_fail in {"pass", "fail"}:
            evidence = str(case.get("evidence_url", "")).strip()
            if not evidence:
                issues.append(
                    f"{case_label}: pass_fail is '{case.get('pass_fail')}' but evidence_url is empty"
                )

        story_id = str(case.get("story_id", "")).strip()
        if story_id:
            cases_by_story.setdefault(story_id, []).append(case)

    # Negative-path coverage per story.
    for story_id, story_cases in cases_by_story.items():
        if not any(_coerce_bool(c.get("negative_path", False)) for c in story_cases):
            issues.append(
                f"story '{story_id}': no case has negative_path=true — "
                "every story needs >= 1 negative path case"
            )

    if rtm_gate:
        for story_id, story_cases in cases_by_story.items():
            passing = [
                c for c in story_cases
                if str(c.get("pass_fail", "")).strip().lower() == "pass"
            ]
            if not passing:
                issues.append(
                    f"RTM gate — story '{story_id}': no case is Passed yet"
                )
            negative_passing = [
                c for c in passing if _coerce_bool(c.get("negative_path", False))
            ]
            if not negative_passing:
                issues.append(
                    f"RTM gate — story '{story_id}': no negative_path case is Passed yet"
                )

    return issues


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def detect_format(file_path: Path | None) -> str:
    if file_path is None:
        return "json"
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    return "json"


def main() -> int:
    args = parse_args()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: file not found: {file_path}", file=sys.stderr)
            return 2
        text = file_path.read_text(encoding="utf-8")
    else:
        file_path = None
        text = sys.stdin.read()

    fmt = args.format if args.format != "auto" else detect_format(file_path)

    try:
        if fmt == "json":
            cases = parse_json(text)
        elif fmt == "csv":
            cases = parse_csv(text)
        elif fmt == "markdown":
            cases = parse_markdown(text)
        else:
            print(f"ERROR: unsupported format: {fmt}", file=sys.stderr)
            return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: failed to parse input as {fmt}: {exc}", file=sys.stderr)
        return 2

    issues = validate_cases(cases, rtm_gate=args.rtm_gate)

    if not issues:
        print(f"OK — validated {len(cases)} case(s).")
        return 0

    for issue in issues:
        print(f"FAIL: {issue}", file=sys.stderr)
    print(f"\n{len(issues)} issue(s) across {len(cases)} case(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
