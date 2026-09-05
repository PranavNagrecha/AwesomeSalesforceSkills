#!/usr/bin/env python3
"""Lint a UAT test-case file, or a whole UAT folder, against the canonical schema.

This is an artefact linter, not a Salesforce client. It never contacts an org and it
never deploys. Stdlib only.

What it checks
--------------
Per case
  1. Required fields present and non-empty: case_id, ac_id, req_id, persona, sandbox,
     steps, evidence, pass_rule (story_id / negative_path / data_setup /
     permission_setup / precondition are checked when present).
  2. ``case_id`` unique and well formed (``TC-...`` / ``UAT-...``, letters, digits,
     hyphens); ``ac_id`` and ``req_id`` well formed.
  3. At least one step, and **every** step carries a non-empty expected result. A step
     with no observable cannot pass or fail.
  4. No ambiguous expected result ("looks correct", "as expected", "works", "properly").
  5. ``persona`` is not a generic or administrator seat.
  6. ``automation_candidate`` is in {apex, flow-test, none} when present.
  7. ``pass_fail`` / ``result`` in {Pass, Fail, Blocked, Not Run}; a Pass or Fail needs
     evidence.

Across the set
  8. Every ``ac_id`` resolves to a criterion declared in a criteria file, when one is
     present in the manifest directory. Absent a criteria file this is skipped, not
     failed.
  9. Every requirement (or story, when req_id is absent) has >= 1 negative-path case.
 10. Every run-sheet row references a case_id that exists.

Exit codes: 0 clean, 1 findings, 2 could not read or parse the input.

Usage
-----
    python3 check_uat_case.py --file uat-cases.yaml
    python3 check_uat_case.py --file cases.json
    python3 check_uat_case.py --file cases.csv --format csv
    python3 check_uat_case.py --manifest-dir ./uat/
    python3 check_uat_case.py --manifest-dir ./uat/ --rtm-gate
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PASS_FAIL_ENUM = {"pass", "fail", "blocked", "not run"}
AUTOMATION_ENUM = {"apex", "flow-test", "none"}

REQUIRED_FIELDS = (
    "case_id",
    "ac_id",
    "req_id",
    "persona",
    "sandbox",
    "steps",
    "evidence",
    "pass_rule",
)
# Checked only when the key is present at all, so the older three-field shape in
# templates/uat-case.md still lints.
OPTIONAL_NONEMPTY = ("story_id", "precondition", "data_setup", "permission_setup")

REJECTED_PERSONA_TOKENS = (
    "system administrator",
    "sysadmin",
    "sys admin",
)
GENERIC_PERSONAS = {"admin", "internal user", "standard user", "user", "tester"}

AMBIGUOUS = (
    "looks correct",
    "looks right",
    "looks good",
    "as expected",
    "works correctly",
    "works as intended",
    "works fine",
    "behaves properly",
    "renders correctly",
    "is correct",
    "no issues",
    "verify it works",
    "should be fine",
    "etc.",
    "tbd",
    "todo",
)

CASE_ID_RE = re.compile(r"^(TC|UAT)-[A-Z0-9]+(-[A-Z0-9]+)*$", re.IGNORECASE)
AC_ID_RE = re.compile(r"^AC-[A-Za-z0-9]+(\.[A-Za-z0-9]+)*$")
REQ_ID_RE = re.compile(r"^(REQ|FG)-[A-Za-z0-9.\-]+$")

LIST_FIELDS = ("data_setup", "permission_setup", "steps", "evidence")

CASE_FILE_HINTS = ("case", "script", "test")
CRITERIA_FILE_HINTS = ("criteri", "acceptance", "ac-", "ac_")
RUNSHEET_FILE_HINTS = ("run-sheet", "run_sheet", "runsheet", "run-log", "results")


# ---------------------------------------------------------------------------
# Tiny YAML subset reader (stdlib only)
# ---------------------------------------------------------------------------

def _strip_inline_comment(v: str) -> str:
    """Drop a trailing ``# comment``, respecting a quoted scalar."""
    if v[:1] in "\"'":
        quote = v[0]
        end = v.find(quote, 1)
        if end != -1:
            return v[: end + 1]
        return v
    idx = v.find(" #")
    return v[:idx].rstrip() if idx != -1 else v


def _scalar(raw: str):
    v = _strip_inline_comment(raw.strip())
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v in ("[]", "{}"):
        return [] if v == "[]" else {}
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(part) for part in inner.split(",")] if inner else []
    low = v.lower()
    if low in {"true", "yes"}:
        return True
    if low in {"false", "no"}:
        return False
    if low in {"null", "~", ""}:
        return ""
    return v


def load_yaml(text: str) -> dict:
    root: dict = {}
    stack: list[tuple[int, object]] = [(-1, root)]

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or raw.strip() in {"---", "..."}:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()

        top = stack[-1][1]

        if line.startswith("- "):
            item = line[2:].strip()
            if not isinstance(top, list):
                if len(stack) > 1:
                    stack.pop()
                    top = stack[-1][1]
                if not isinstance(top, list):
                    continue
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", item)
            if m:
                entry: dict = {}
                top.append(entry)
                stack.append((indent + 2, entry))
                key, rest = m.group(1), m.group(2).strip()
                if rest:
                    entry[key] = _scalar(rest)
                else:
                    child: list = []
                    entry[key] = child
                    stack.append((indent + 4, child))
            else:
                top.append(_scalar(item))
            continue

        m = re.match(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, rest = m.group(1), m.group(2).strip()

        while len(stack) > 1 and not isinstance(stack[-1][1], dict):
            stack.pop()
        while len(stack) > 1 and indent <= stack[-1][0] - 2:
            stack.pop()
        holder = stack[-1][1]
        if not isinstance(holder, dict):
            continue

        if rest:
            holder[key] = _scalar(rest)
        else:
            container: list = []
            holder[key] = container
            stack.append((indent + 2, container))
    return _prune(root)


def _prune(node):
    """An empty list that only ever received key/value children is really a map."""
    if isinstance(node, dict):
        return {k: _prune(v) for k, v in node.items()}
    if isinstance(node, list):
        if len(node) == 1 and isinstance(node[0], dict) and not any(
            isinstance(x, (str, bool)) for x in node
        ):
            return _prune(node[0])
        return [_prune(v) for v in node]
    return node


# ---------------------------------------------------------------------------
# Coercion
# ---------------------------------------------------------------------------

def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _coerce_list(value) -> list:
    if isinstance(value, list):
        return [v for v in value if v not in ("", None)]
    if isinstance(value, str):
        sep = "|" if "|" in value else ";"
        return [c.strip() for c in value.split(sep) if c.strip() and c.strip() not in {"—", "-"}]
    if isinstance(value, dict):
        return [value]
    return []


def _step_pair(step) -> tuple[str, str]:
    """Return (step text, expected text) for either step shape."""
    if isinstance(step, dict):
        text = str(step.get("step") or step.get("action") or step.get("do") or "").strip()
        exp = str(step.get("expected") or step.get("expected_result") or "").strip()
        return text, exp
    return str(step).strip(), ""


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------

def cases_from_obj(obj) -> list[dict]:
    if isinstance(obj, list):
        return [c for c in obj if isinstance(c, dict)]
    if isinstance(obj, dict):
        for key in ("test_cases", "cases", "uat_cases"):
            val = obj.get(key)
            if isinstance(val, list):
                return [c for c in val if isinstance(c, dict)]
            if isinstance(val, dict):
                return [val]
    return []


def runsheet_from_obj(obj) -> list[dict]:
    if isinstance(obj, dict):
        for key in ("run_sheet", "runs", "run_log", "results"):
            val = obj.get(key)
            if isinstance(val, list):
                return [r for r in val if isinstance(r, dict)]
    return []


def parse_markdown_tables(text: str) -> list[dict]:
    """Pull rows out of any pipe table whose header names case_id or run_id."""
    rows: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and line.endswith("|"):
            header = [c.strip().strip("*`").lower() for c in line.strip("|").split("|")]
            if i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
                is_case = "case_id" in header and "defect_id" not in header
                is_run = "run_id" in header
                if is_case or is_run:
                    j = i + 2
                    while j < len(lines) and lines[j].strip().startswith("|"):
                        cells = [c.strip().strip("*`") for c in lines[j].strip().strip("|").split("|")]
                        if len(cells) == len(header):
                            rows.append(dict(zip(header, cells)))
                        j += 1
                    i = j
                    continue
        i += 1
    return rows


def parse_csv_text(text: str) -> list[dict]:
    reader = csv.DictReader(text.splitlines())
    out = []
    for row in reader:
        rec = {(k or "").strip().lower(): (v or "") for k, v in row.items()}
        for field in LIST_FIELDS:
            if field in rec:
                rec[field] = _coerce_list(rec[field])
        out.append(rec)
    return out


def read_file(path: Path, fmt: str = "auto"):
    """Return (cases, runsheet_rows, criteria_ids) found in one file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    fmt = fmt if fmt != "auto" else {
        ".json": "json", ".csv": "csv", ".yaml": "yaml", ".yml": "yaml",
        ".md": "markdown", ".markdown": "markdown",
    }.get(suffix, "yaml")

    cases: list[dict] = []
    runs: list[dict] = []
    criteria: set[str] = set()

    if fmt == "json":
        obj = json.loads(text)
        cases, runs = cases_from_obj(obj), runsheet_from_obj(obj)
        criteria = criteria_ids_from_obj(obj)
    elif fmt == "csv":
        rows = parse_csv_text(text)
        if rows and "run_id" in rows[0]:
            runs = rows
        else:
            cases = rows
    elif fmt == "yaml":
        obj = load_yaml(text)
        cases, runs = cases_from_obj(obj), runsheet_from_obj(obj)
        criteria = criteria_ids_from_obj(obj)
    else:  # markdown: tables, plus any fenced yaml/csv blocks
        for block_lang, block in fenced_blocks(text):
            if block_lang in {"yaml", "yml"}:
                obj = load_yaml(block)
                cases += cases_from_obj(obj)
                runs += runsheet_from_obj(obj)
                criteria |= criteria_ids_from_obj(obj)
            elif block_lang == "json":
                try:
                    obj = json.loads(block)
                except ValueError:
                    continue
                cases += cases_from_obj(obj)
                runs += runsheet_from_obj(obj)
                criteria |= criteria_ids_from_obj(obj)
            elif block_lang == "csv":
                rows = parse_csv_text(block)
                if rows and "run_id" in rows[0]:
                    runs += rows
                elif rows and "case_id" in rows[0]:
                    cases += rows
        # Fenced blocks are the authoritative form. Only fall back to scraping
        # tables when the document carries no fenced case or run-sheet block —
        # otherwise a narrative file's summary table double-counts its own YAML.
        had_fenced_cases = bool(cases)
        had_fenced_runs = bool(runs)
        for row in parse_markdown_tables(text):
            if "run_id" in row:
                if not had_fenced_runs:
                    runs.append(row)
            elif not had_fenced_cases and "case_id" in row and (
                row.get("ac_id") or row.get("req_id")
            ):
                cases.append(row)
        criteria |= set(re.findall(r"\bAC-[0-9]+\.[0-9]+\b", text))

    return cases, runs, criteria


def fenced_blocks(text: str):
    out = []
    lang = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^```([A-Za-z0-9_+-]*)\s*$", line)
        if m:
            if lang is None:
                lang = m.group(1).lower()
                buf = []
            else:
                out.append((lang, "\n".join(buf)))
                lang = None
        elif lang is not None:
            buf.append(line)
    return out


def criteria_ids_from_obj(obj) -> set[str]:
    ids: set[str] = set()
    if isinstance(obj, dict):
        for key in ("acceptance_criteria", "criteria", "acs"):
            val = obj.get(key)
            if isinstance(val, list):
                for entry in val:
                    if isinstance(entry, dict) and entry.get("ac_id"):
                        ids.add(str(entry["ac_id"]).strip())
            elif isinstance(val, dict) and val.get("ac_id"):
                ids.add(str(val["ac_id"]).strip())
    return ids


def classify(path: Path) -> str:
    name = path.name.lower()
    if any(h in name for h in RUNSHEET_FILE_HINTS):
        return "runsheet"
    if any(h in name for h in CRITERIA_FILE_HINTS):
        return "criteria"
    if any(h in name for h in CASE_FILE_HINTS):
        return "cases"
    return "other"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _ambiguous(text: str) -> str | None:
    low = text.lower()
    for phrase in AMBIGUOUS:
        if phrase in low:
            return phrase
    return None


def validate(cases, runs, criteria_ids, *, rtm_gate=False, have_criteria=False):
    errors: list[str] = []
    warnings: list[str] = []

    if not cases:
        errors.append("No test cases found in the input.")
        return errors, warnings

    seen: set[str] = set()
    by_group: dict[str, list[dict]] = {}
    known_case_ids: set[str] = set()

    for idx, case in enumerate(cases, start=1):
        cid = str(case.get("case_id", "")).strip()
        label = cid or f"case[{idx}]"

        for field in REQUIRED_FIELDS:
            val = case.get(field)
            if field in ("steps", "evidence"):
                val = _coerce_list(val)
            if val in (None, "", [], {}, "—", "-"):
                errors.append(f"{label}: missing or empty required field '{field}'")

        for field in OPTIONAL_NONEMPTY:
            if field in case and case[field] in (None, "", [], {}):
                errors.append(f"{label}: field '{field}' is present but empty")

        if cid:
            if cid in seen:
                errors.append(f"{label}: duplicate case_id '{cid}'")
            seen.add(cid)
            known_case_ids.add(cid)
            if not CASE_ID_RE.match(cid):
                errors.append(
                    f"{label}: case_id '{cid}' is malformed — expected TC-XXX / TC-XXX-NNN "
                    "(letters, digits and hyphens)"
                )

        ac = str(case.get("ac_id", "")).strip()
        if ac and not AC_ID_RE.match(ac):
            errors.append(f"{label}: ac_id '{ac}' is malformed — expected AC-nnn.n")
        if ac and have_criteria and ac not in criteria_ids:
            errors.append(
                f"{label}: ac_id '{ac}' resolves to no criterion in the criteria file(s) "
                "in this manifest directory"
            )

        req = str(case.get("req_id", "")).strip()
        if req and not REQ_ID_RE.match(req):
            errors.append(f"{label}: req_id '{req}' is malformed — expected REQ-nnn or FG-nnn")

        persona = str(case.get("persona", "")).strip()
        plow = persona.lower()
        if persona:
            if any(tok in plow for tok in REJECTED_PERSONA_TOKENS):
                errors.append(
                    f"{label}: persona '{persona}' names an administrator — a pass from an "
                    "admin seat proves nothing about the persona"
                )
            elif plow in GENERIC_PERSONAS:
                errors.append(
                    f"{label}: persona '{persona}' is generic — name the profile and the grant"
                )

        steps = _coerce_list(case.get("steps"))
        if isinstance(case.get("steps"), str) and case["steps"].strip().isdigit():
            # markdown-table shorthand: a step count, not the steps
            steps = []
            warnings.append(f"{label}: 'steps' is a count, not the steps — per-step expected "
                            "results cannot be checked from the summary table")
        if steps:
            for n, step in enumerate(steps, start=1):
                text, expected = _step_pair(step)
                if not text:
                    errors.append(f"{label}: step {n} is empty")
                    continue
                if isinstance(step, dict):
                    if not expected:
                        errors.append(f"{label}: step {n} has no expected result")
                    else:
                        hit = _ambiguous(expected)
                        if hit:
                            errors.append(
                                f"{label}: step {n} expected result is ambiguous "
                                f"(contains '{hit}') — name the observable"
                            )
                else:
                    warnings.append(
                        f"{label}: step {n} is a bare string — the schema wants "
                        "{step, expected} so a failure names the step that broke"
                    )

        pass_rule = str(case.get("pass_rule", "")).strip()
        if pass_rule:
            hit = _ambiguous(pass_rule)
            if hit:
                errors.append(f"{label}: pass_rule is ambiguous (contains '{hit}')")

        exp = str(case.get("expected_result", "")).strip()
        if exp:
            hit = _ambiguous(exp)
            if hit:
                errors.append(f"{label}: expected_result is ambiguous (contains '{hit}')")

        auto = str(case.get("automation_candidate", "")).strip().lower()
        if auto and auto not in AUTOMATION_ENUM:
            errors.append(
                f"{label}: automation_candidate '{case.get('automation_candidate')}' is not "
                "one of {apex, flow-test, none}"
            )
        if auto and auto != "none" and not str(case.get("automation_rationale", "")).strip():
            warnings.append(
                f"{label}: automation_candidate is '{auto}' with no automation_rationale — "
                "record the platform fact behind the verdict"
            )

        result = str(case.get("pass_fail") or case.get("result") or "").strip()
        if result and result.lower() not in PASS_FAIL_ENUM:
            errors.append(
                f"{label}: result '{result}' is not in {{Pass, Fail, Blocked, Not Run}}"
            )
        if result.lower() in {"pass", "fail"}:
            ev = case.get("evidence_url") or case.get("evidence_ref") or case.get("evidence")
            if not _coerce_list(ev) and not str(ev or "").strip():
                errors.append(f"{label}: result is '{result}' but no evidence is recorded")

        group = req or str(case.get("story_id", "")).strip()
        if group:
            by_group.setdefault(group, []).append(case)

    negative_keys = ("negative_path", "negative")
    for group, members in by_group.items():
        has_negative = False
        for c in members:
            for k in negative_keys:
                if k in c and _coerce_bool(c[k]) or str(c.get(k, "")).strip().lower() == "yes":
                    has_negative = True
        if not has_negative:
            errors.append(
                f"'{group}': no case is marked negative — every requirement needs at least "
                "one case that proves the feature blocks the wrong action"
            )

    for r_idx, row in enumerate(runs, start=1):
        rid = str(row.get("run_id") or f"run[{r_idx}]").strip()
        cid = str(row.get("case_id", "")).strip()
        if not cid:
            errors.append(f"run sheet {rid}: no case_id")
            continue
        if cid not in known_case_ids:
            errors.append(f"run sheet {rid}: case_id '{cid}' matches no test case")
        result = str(row.get("result") or row.get("pass_fail") or "").strip()
        if result and result.lower() not in PASS_FAIL_ENUM:
            errors.append(
                f"run sheet {rid}: result '{result}' is not in {{Pass, Fail, Blocked, Not Run}}"
            )
        if result.lower() in {"pass", "fail"} and not str(
            row.get("evidence_ref") or row.get("evidence_url") or ""
        ).strip():
            errors.append(f"run sheet {rid}: result is '{result}' with no evidence_ref")
        if result.lower() == "blocked" and str(row.get("defect_id", "")).strip():
            errors.append(
                f"run sheet {rid}: a Blocked row carries defect_id "
                f"'{row.get('defect_id')}' — Blocked is an environment result, not a build defect"
            )

    if rtm_gate:
        results_by_case: dict[str, list[str]] = {}
        for row in runs:
            cid = str(row.get("case_id", "")).strip()
            res = str(row.get("result") or row.get("pass_fail") or "").strip().lower()
            if cid:
                results_by_case.setdefault(cid, []).append(res)
        for group, members in by_group.items():
            passed = []
            for c in members:
                cid = str(c.get("case_id", "")).strip()
                own = str(c.get("pass_fail") or c.get("result") or "").strip().lower()
                seq = results_by_case.get(cid, []) or ([own] if own else [])
                if seq and seq[-1] == "pass":
                    passed.append(c)
            if not passed:
                errors.append(f"RTM gate — '{group}': no case has a latest result of Pass")
            elif not any(
                _coerce_bool(c.get("negative_path", c.get("negative", False)))
                or str(c.get("negative", "")).strip().lower() == "yes"
                for c in passed
            ):
                errors.append(f"RTM gate — '{group}': no negative case has passed")

    return errors, warnings


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint UAT test cases (YAML, JSON, CSV or markdown table) against the "
            "canonical schema: ids, per-step expected results, evidence, pass rule, "
            "automation verdict, negative coverage, run-sheet integrity."
        ),
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--file", help="One cases file. Omit both flags to read YAML/JSON from stdin.")
    src.add_argument(
        "--manifest-dir",
        help=(
            "A UAT folder. Case files, criteria files and the run sheet are read together, "
            "so ac_id references and run-sheet rows are cross-checked."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("auto", "yaml", "json", "csv", "markdown"),
        default="auto",
        help="Input format for --file (default: auto, by extension).",
    )
    parser.add_argument(
        "--rtm-gate",
        action="store_true",
        help="Also require, per requirement, a passing case and a passing negative case.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    cases: list[dict] = []
    runs: list[dict] = []
    criteria: set[str] = set()
    have_criteria = False
    read_files: list[str] = []

    try:
        if args.manifest_dir:
            root = Path(args.manifest_dir)
            if not root.is_dir():
                print(f"ERROR: not a directory: {root}", file=sys.stderr)
                return 2
            paths = sorted(
                p for p in root.rglob("*")
                if p.is_file() and p.suffix.lower() in
                {".yaml", ".yml", ".json", ".csv", ".md", ".markdown"}
            )
            if not paths:
                print(f"ERROR: no lintable files under {root}", file=sys.stderr)
                return 2
            for path in paths:
                kind = classify(path)
                try:
                    c, r, ac = read_file(path)
                except (ValueError, json.JSONDecodeError) as exc:
                    print(f"ERROR: failed to parse {path}: {exc}", file=sys.stderr)
                    return 2
                read_files.append(f"{path.name} [{kind}]")
                if kind == "criteria":
                    if ac:
                        have_criteria = True
                    criteria |= ac
                    continue
                if ac:
                    criteria |= ac
                cases += c
                runs += r
        elif args.file:
            path = Path(args.file)
            if not path.exists():
                print(f"ERROR: file not found: {path}", file=sys.stderr)
                return 2
            cases, runs, criteria = read_file(path, args.format)
            read_files.append(path.name)
        else:
            text = sys.stdin.read()
            try:
                obj = json.loads(text)
            except ValueError:
                obj = load_yaml(text)
            cases, runs = cases_from_obj(obj), runsheet_from_obj(obj)
            criteria = criteria_ids_from_obj(obj)
            read_files.append("<stdin>")
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate(
        cases, runs, criteria, rtm_gate=args.rtm_gate, have_criteria=have_criteria
    )

    if args.strict:
        errors += warnings
        warnings = []

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)

    if not errors:
        detail = f"{len(cases)} case(s), {len(runs)} run-sheet row(s)"
        if have_criteria:
            detail += f", {len(criteria)} criterion id(s) cross-checked"
        else:
            detail += ", no criteria file present so ac_id resolution was skipped"
        print(f"OK — {detail}. Files read: {', '.join(read_files)}")
        return 0

    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)
    print(
        f"\n{len(errors)} error(s), {len(warnings)} warning(s) across {len(cases)} case(s).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
