#!/usr/bin/env python3
"""Fixture-based harness for skill-local checker scripts.

Discovers:

    skills/<domain>/<skill>/scripts/tests/<case-name>/
        input.cls            # or input.trigger / input.apex
        expected.json        # {"expected": [{"rule": "...", "severity": "HIGH"}, ...],
                             #  "strict": false}

and runs the sibling checker (scripts/check_*.py) against the input file's
parent directory. Compares JSON output of the checker with `expected`:

- Every expected issue (matched on (rule, severity)) MUST be present in actual.
- If expected.strict is true, actual must not contain ANY issues beyond expected.
- expected.line is optional; if present, that exact line must match.

Exit codes:
    0 — all fixtures passed
    1 — one or more fixtures failed
    2 — discovery or invocation error

Usage:
    python3 scripts/test_checkers.py                         # all skills
    python3 scripts/test_checkers.py --skill skills/apex/x   # one skill
    python3 scripts/test_checkers.py --changed-only          # git-dirty subset
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class FixtureCase:
    case_dir: Path
    checker: Path
    input_file: Path
    expected: dict


def _find_cases(roots: list[Path]) -> list[FixtureCase]:
    cases: list[FixtureCase] = []
    for root in roots:
        # Each roots entry is a skill dir or the whole skills/ tree.
        for tests_dir in root.rglob("scripts/tests"):
            if not tests_dir.is_dir():
                continue
            for case_dir in sorted(p for p in tests_dir.iterdir() if p.is_dir()):
                expected_path = case_dir / "expected.json"
                if not expected_path.exists():
                    continue
                input_candidates = [
                    case_dir / "input.cls",
                    case_dir / "input.trigger",
                    case_dir / "input.apex",
                ]
                input_file = next((p for p in input_candidates if p.exists()), None)
                if input_file is None:
                    print(
                        f"SKIP  {case_dir.relative_to(ROOT)}: no input.cls/input.trigger/input.apex",
                        file=sys.stderr,
                    )
                    continue
                # Checker is sibling to tests/, in scripts/.
                scripts_dir = tests_dir.parent
                checker_candidates = sorted(scripts_dir.glob("check_*.py"))
                if not checker_candidates:
                    print(
                        f"SKIP  {case_dir.relative_to(ROOT)}: no check_*.py in {scripts_dir}",
                        file=sys.stderr,
                    )
                    continue
                try:
                    expected = json.loads(expected_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as e:
                    print(
                        f"ERROR {case_dir.relative_to(ROOT)}: malformed expected.json: {e}",
                        file=sys.stderr,
                    )
                    continue
                cases.append(
                    FixtureCase(
                        case_dir=case_dir,
                        checker=checker_candidates[0],
                        input_file=input_file,
                        expected=expected,
                    )
                )
    return cases


def _run_checker(case: FixtureCase) -> dict:
    """Run the checker against the input file's parent dir. Return parsed JSON."""
    proc = subprocess.run(
        [sys.executable, str(case.checker), "--path", str(case.input_file.parent), "--format", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    # The convention in this repo: checker exits 1 if issues found, 0 if clean, 2 on error.
    if proc.returncode not in (0, 1):
        raise RuntimeError(
            f"checker returned code {proc.returncode}\nstderr: {proc.stderr}\nstdout: {proc.stdout}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"checker output is not JSON: {e}\nstdout: {proc.stdout[:500]}")


def _match_expected(actual: dict, expected: dict) -> tuple[bool, list[str]]:
    """Return (pass, failure_reasons)."""
    actual_issues = actual.get("issues", [])
    expected_issues = expected.get("expected", [])
    strict = bool(expected.get("strict", False))
    failures: list[str] = []

    # Every expected issue must be found.
    remaining_actual = list(actual_issues)
    for want in expected_issues:
        want_rule = want.get("rule")
        want_sev = want.get("severity")
        want_line = want.get("line")
        match_idx = None
        for i, have in enumerate(remaining_actual):
            if want_rule and have.get("rule") != want_rule:
                continue
            if want_sev and have.get("severity") != want_sev:
                continue
            if want_line is not None and have.get("line") != want_line:
                continue
            match_idx = i
            break
        if match_idx is None:
            failures.append(f"missing expected issue: {want}")
        else:
            remaining_actual.pop(match_idx)

    if strict and remaining_actual:
        for extra in remaining_actual:
            failures.append(
                f"unexpected issue (strict mode): rule={extra.get('rule')} sev={extra.get('severity')} line={extra.get('line')}"
            )

    return (not failures, failures)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run checker-script fixture tests.")
    parser.add_argument("--skill", action="append", default=[], help="Skill dir (repeatable).")
    parser.add_argument("--changed-only", action="store_true", help="Scope to git-changed skills.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print per-case details.")
    return parser.parse_args()


def _resolve_scopes(args: argparse.Namespace) -> list[Path]:
    if args.skill:
        return [Path(s) if Path(s).is_absolute() else (ROOT / s) for s in args.skill]
    if args.changed_only:
        return _git_changed_skill_dirs()
    return [ROOT / "skills"]


def _git_changed_skill_dirs() -> list[Path]:
    """Return skill dirs with uncommitted or recently-committed changes."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return [ROOT / "skills"]
    touched: set[Path] = set()
    for line in out.splitlines():
        # Format: "XY path" (or "R  old -> new").
        m = re.match(r"^..\s+(?P<path>\S+)(?:\s+->\s+(?P<new>\S+))?$", line)
        if not m:
            continue
        path = m.group("new") or m.group("path")
        parts = Path(path).parts
        if len(parts) >= 3 and parts[0] == "skills":
            touched.add(ROOT / "skills" / parts[1] / parts[2])
    if not touched:
        return [ROOT / "skills"]
    return sorted(touched)


def main() -> int:
    args = _parse_args()
    scopes = _resolve_scopes(args)
    cases = _find_cases(scopes)

    if not cases:
        print("No checker fixtures found. (Each case is a dir under "
              "skills/*/*/scripts/tests/<name>/ with input.cls + expected.json.)")
        return 0

    passes = 0
    failures = 0
    for case in cases:
        rel = case.case_dir.relative_to(ROOT)
        try:
            actual = _run_checker(case)
        except RuntimeError as e:
            print(f"FAIL  {rel}: {e}")
            failures += 1
            continue
        ok, reasons = _match_expected(actual, case.expected)
        if ok:
            passes += 1
            if args.verbose:
                print(f"PASS  {rel}")
        else:
            failures += 1
            print(f"FAIL  {rel}")
            for r in reasons:
                print(f"        {r}")

    print(f"\n{passes} passed, {failures} failed, {len(cases)} total")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
