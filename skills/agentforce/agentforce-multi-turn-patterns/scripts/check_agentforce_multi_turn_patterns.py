#!/usr/bin/env python3
"""Checker for the agentforce-multi-turn-patterns skill.

Lints Agent Script files (``*.agent`` inside ``aiAuthoringBundles/``) for the multi-turn
failure modes in references/gotchas.md. Agent Script is indentation-based YAML-like text, so
the rules are line-oriented and deliberately conservative.

  MT-VAR-ID-01     a variable typed ``id`` — the type is deprecated; use ``string`` (gotcha 10)
  MT-VAR-DESC-01   a mutable variable with no ``description:`` — slot filling and other
                   subagents cannot tell what it holds (gotcha 1, 7)
  MT-RESET-01      ``reset_to_initial_node: True`` — every turn restarts from the start node,
                   so collected slots are re-asked (gotcha 12)
  MT-ESC-01        ``@utils.escalate`` used without a ``connection messaging:`` block that
                   names an outbound route — escalation needs the Omni-Channel connection and
                   context does not travel by itself (gotcha 8)
  MT-SUB-DESC-01   two subagents share a description, or one has none — routing instability
                   (gotcha 9)
  MT-FILTER-01     an action output whose name looks sensitive (dob, ssn, password, token,
                   secret, card) without ``filter_from_agent: True`` — outputs stay in the
                   session context for the whole conversation (gotcha 14)
  MT-TRANS-01      ``transition to @subagent.X`` where X is not declared (gotcha 13)
  MT-SETVAR-01     ``@utils.setVariables`` writes a variable that is not declared

Usage:
    python3 check_agentforce_multi_turn_patterns.py --manifest-dir force-app/main/default
    python3 check_agentforce_multi_turn_patterns.py --self-test

stdlib only. Missing directory exits 1; a directory with no .agent files warns and exits 0.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SENSITIVE = re.compile(r"(?i)(dob|date_of_birth|birth|ssn|social|passw|token|secret|card_number|pan\b|cvv)")
VAR_DECL = re.compile(r"^\s{4}(\w+):\s*(mutable|linked)\s+(\w+)")
SUBAGENT = re.compile(r"^(?:subagent|start_agent)\s+(\w+):")
TRANSITION = re.compile(r"transition to @subagent\.(\w+)")
SETVAR_WITH = re.compile(r"^\s+with\s+(\w+)\s*=")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def check_agent_script(path: Path) -> list[str]:
    issues: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    name = path.name

    # --- variables ---------------------------------------------------------------
    declared: dict[str, str] = {}
    in_vars = False
    for i, line in enumerate(lines):
        if line.startswith("variables:"):
            in_vars = True
            continue
        if in_vars and line and not line.startswith(" "):
            in_vars = False
        if not in_vars:
            continue
        m = VAR_DECL.match(line)
        if not m:
            continue
        var, kind, vtype = m.groups()
        declared[var] = vtype
        if vtype == "id":
            issues.append(f"MT-VAR-ID-01 {name}: variable '{var}' is typed 'id'; the type is deprecated in "
                          "Agent Script — declare record IDs as 'string' (gotcha 10).")
        if kind == "mutable":
            has_desc = False
            for nxt in lines[i + 1:i + 4]:
                if _indent(nxt) <= 4 and nxt.strip():
                    break
                if nxt.strip().startswith("description:"):
                    has_desc = True
                    break
            if not has_desc:
                issues.append(f"MT-VAR-DESC-01 {name}: mutable variable '{var}' has no description; every "
                              "subagent reads the same variables, so say what it holds and which action "
                              "is its source of truth (gotchas 1 and 7).")

    # --- runtime -----------------------------------------------------------------
    for line in lines:
        if re.search(r"reset_to_initial_node:\s*(True|true)", line):
            issues.append(f"MT-RESET-01 {name}: reset_to_initial_node is True — every turn restarts at the "
                          "start node and collected slots are asked again; keep it False for a slot-filling "
                          "agent (gotcha 12).")
            break

    # --- escalation --------------------------------------------------------------
    text = "\n".join(lines)
    if "@utils.escalate" in text:
        has_conn = re.search(r"^connection messaging:", text, re.M) and re.search(r"outbound_route_(type|name):", text)
        if not has_conn:
            issues.append(f"MT-ESC-01 {name}: @utils.escalate is used but no 'connection messaging:' block "
                          "names an outbound route; escalation needs the Omni-Channel connection, and the "
                          "collected context must be packaged for the agent (gotcha 8).")

    # --- subagents ---------------------------------------------------------------
    subagents: dict[str, str] = {}
    for i, line in enumerate(lines):
        m = SUBAGENT.match(line)
        if not m:
            continue
        desc = ""
        for nxt in lines[i + 1:i + 3]:
            s = nxt.strip()
            if s.startswith("description:"):
                desc = s.split(":", 1)[1].strip().strip('"')
                break
        subagents[m.group(1)] = desc
        if not desc:
            issues.append(f"MT-SUB-DESC-01 {name}: subagent '{m.group(1)}' has no description; the router "
                          "picks subagents by description (gotcha 9).")
    seen: dict[str, str] = {}
    for sub, desc in subagents.items():
        if desc and desc.lower() in seen:
            issues.append(f"MT-SUB-DESC-01 {name}: subagents '{seen[desc.lower()]}' and '{sub}' share the "
                          "same description; overlapping descriptions make routing unstable (gotcha 9).")
        elif desc:
            seen[desc.lower()] = sub

    # --- outputs that stay in context -------------------------------------------
    in_outputs = False
    out_indent = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s == "outputs:":
            in_outputs, out_indent = True, _indent(line)
            continue
        if in_outputs:
            if s and _indent(line) <= out_indent:
                in_outputs = False
                continue
            m = re.match(r"^(\w+):\s*\w+\s*$", s)
            if m and _indent(line) == out_indent + 4 and SENSITIVE.search(m.group(1)):
                filtered = any(
                    "filter_from_agent" in nxt and re.search(r"True|true", nxt)
                    for nxt in lines[i + 1:i + 3]
                    if _indent(nxt) > _indent(line)
                )
                if not filtered:
                    issues.append(f"MT-FILTER-01 {name}: action output '{m.group(1)}' looks sensitive and is "
                                  "not filter_from_agent: True; action outputs stay in the session context "
                                  "for the whole conversation (gotcha 14).")

    # --- transitions and setVariables -------------------------------------------
    for target in sorted(set(TRANSITION.findall(text))):
        if target not in subagents:
            issues.append(f"MT-TRANS-01 {name}: 'transition to @subagent.{target}' but no subagent '{target}' "
                          "is declared; transitions are one way and a bad target strands the user (gotcha 13).")
    for i, line in enumerate(lines):
        if "@utils.setVariables" in line:
            for nxt in lines[i + 1:i + 6]:
                if _indent(nxt) <= _indent(line):
                    break
                m = SETVAR_WITH.match(nxt)
                if m and m.group(1) not in declared:
                    issues.append(f"MT-SETVAR-01 {name}: @utils.setVariables writes '{m.group(1)}', which is "
                                  "not declared under variables:.")
    return issues


def run(manifest_dir: Path) -> tuple[list[str], int]:
    files = sorted(manifest_dir.rglob("*.agent"))
    issues: list[str] = []
    for f in files:
        issues.extend(check_agent_script(f))
    return issues, len(files)


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    good, n_good = run(here / "good")
    bad, n_bad = run(here / "bad")
    empty, n_empty = run(here / "empty")
    rules = {i.split()[0] for i in bad}
    expected = {"MT-VAR-ID-01", "MT-VAR-DESC-01", "MT-RESET-01", "MT-ESC-01", "MT-SUB-DESC-01",
                "MT-FILTER-01", "MT-TRANS-01", "MT-SETVAR-01"}
    ok = n_good >= 1 and not good and expected <= rules and n_empty == 0 and not empty
    print(f"good: {n_good} file(s), {len(good)} issue(s) (expected 0)")
    print(f"bad: {n_bad} file(s), rules fired {sorted(rules)}")
    for i in good + bad:
        print("  ", i)
    print(f"empty: {n_empty} file(s)")
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint Agent Script files for multi-turn failure modes.")
    ap.add_argument("--manifest-dir", default=".", help="metadata root; *.agent files are found recursively")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ISSUE: directory not found: {root}")
        return 1
    issues, n = run(root)
    if n == 0:
        print(f"WARN: no .agent files under {root}; nothing to check.")
        return 0
    if not issues:
        print(f"No issues found in {n} Agent Script file(s).")
        return 0
    for i in issues:
        print(f"ISSUE: {i}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
