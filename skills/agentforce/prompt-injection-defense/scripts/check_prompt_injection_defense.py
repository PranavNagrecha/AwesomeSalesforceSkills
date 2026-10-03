#!/usr/bin/env python3
"""Check an Agentforce project for prompt-injection exposure and adversarial-suite gaps.

Stdlib only. Point --manifest-dir at a source-format folder (for example force-app/main/default).
It reads Apex classes with @InvocableMethod (agent actions), GenAiPlugin topics, and
AiEvaluationDefinition suites. Rules encode the Generative AI guide (Spring '26: Best Practices
for Writing Topic Instructions; What are Agents? Permissions and Access), the Apex Developer
Guide v67.0 (sharing keywords, user mode), and the Metadata API v67.0 (AiEvaluationDefinition,
GenAiPlugin). Thresholds marked heuristic are review defaults, not platform rules.

Rules
  PI-SYS-01    WARN   An invocable action class runs without sharing or in system mode; a custom action
                      "adheres to the permissions, field-level security, and sharing settings" of its class.
  PI-TRUST-01  WARN   A Boolean @InvocableVariable named like a verdict (isEligible, approved, delivered...);
                      re-query facts in the action instead of trusting the model. Heuristic.
  PI-TOPIC-01  WARN   A topic instruction states a numeric business rule; build it into the action. Heuristic.
  PI-TOPIC-02  WARN   A topic carries more than 15 instructions; start minimal. Heuristic.
  PI-SUITE-00  ERROR  An AiEvaluationDefinition is missing name, subjectName, or subjectType AGENT, or does not parse.
  PI-SUITE-01  WARN   Fewer than 5 test cases in an adversarial suite. Heuristic.
  PI-SUITE-02  WARN   No non-English utterance in the suite.
  PI-SUITE-03  WARN   No case asserts action_sequence_match [] (that the agent took no action).
  PI-SUITE-04  WARN   A payload family has no case: override, role, leakage, coercion, exfiltration. Heuristic.
  PI-SUITE-05  WARN   Invocable actions exist but no AiEvaluationDefinition suite is present.

Usage
  python3 check_prompt_injection_defense.py --manifest-dir force-app/main/default [--strict]
  python3 check_prompt_injection_defense.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VERDICT_NAME = re.compile(r"(eligible|approved|verified|delivered|authori[sz]ed|allowed|confirmed|isvalid|isowner)",
                          re.IGNORECASE)
NUMERIC_RULE = re.compile(r"\b\d+(\.\d+)?\s*(%|percent|days?|business days|hours?|dollars?|usd|eur)\b|\$\s?\d", re.IGNORECASE)
FAMILIES = {
    "override": re.compile(r"ignore (all )?(previous|prior|the above)|disregard|ignora|ignorez|ignorieren|olvida", re.IGNORECASE),
    "role": re.compile(r"you are now|act as|pretend|role ?play|as the (system )?admin", re.IGNORECASE),
    "leakage": re.compile(r"(system|initial) (prompt|message)|instructions you were given|reveal your|message système|print the exact instructions", re.IGNORECASE),
    "coercion": re.compile(r"refund|update (every|all)|delete|close (every|all)|change the status|grant", re.IGNORECASE),
    "exfiltration": re.compile(r"email|send|export|list (all|every)|envía|correo|lista de todos|escalation contact", re.IGNORECASE),
}
NON_ENGLISH = re.compile(r"\b(ignora|ignorez|ignorieren|olvida|instrucciones|anweisungen|précédentes)\b", re.IGNORECASE)
MAX_INSTRUCTIONS = 15
MIN_CASES = 5


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def strip_comments(text: str) -> str:
    """Remove // and /* */ comments outside single-quoted Apex string literals."""
    out: list[str] = []
    i, n, in_string = 0, len(text), False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            in_string = ch != "'"
            i += 1
        elif ch == "'":
            in_string = True
            out.append(ch)
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end == -1 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            out.append(" ")
            i = n if end == -1 else end + 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def check_action(path: Path) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    if "@invocablemethod" not in text.lower():
        return out
    if re.search(r"\bwithout\s+sharing\b", text, flags=re.IGNORECASE):
        out.append(("WARN", "PI-SYS-01", f"{path}: invocable action class declares without sharing; an injected turn gets more than the user's access."))
    if re.search(r"WITH\s+SYSTEM_MODE|AccessLevel\.SYSTEM_MODE", text, flags=re.IGNORECASE):
        out.append(("WARN", "PI-SYS-01", f"{path}: invocable action uses system mode; keep agent-facing queries and DML in user mode."))
    for match in re.finditer(r"@InvocableVariable[^;{}]*?\bpublic\s+Boolean\s+(\w+)\s*;", text, flags=re.IGNORECASE):
        if VERDICT_NAME.search(match.group(1)):
            out.append(("WARN", "PI-TRUST-01",
                        f"{path}: Boolean input '{match.group(1)}' lets the model assert a verdict; re-query the fact in the action."))
    return out


def check_topic(path: Path) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("WARN", "PI-TOPIC-02", f"{path}: topic does not parse ({exc}); cannot review instructions.")]
    instructions = [el for el in root.iter() if _local(el.tag) == "genAiPluginInstructions"]
    if len(instructions) > MAX_INSTRUCTIONS:
        out.append(("WARN", "PI-TOPIC-02", f"{path}: {len(instructions)} instructions; start minimal and move rules into actions."))
    for ins in instructions:
        desc = next((c.text or "" for c in ins if _local(c.tag) == "description"), "")
        if NUMERIC_RULE.search(desc):
            out.append(("WARN", "PI-TOPIC-01",
                        f"{path}: instruction states a numeric business rule ('{desc[:60]}...'); enforce it in the action."))
    return out


def check_suite(path: Path) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", "PI-SUITE-00", f"{path}: suite does not parse ({exc}).")]
    fields = {_local(c.tag): (c.text or "").strip() for c in root}
    for req in ("name", "subjectName"):
        if not fields.get(req):
            out.append(("ERROR", "PI-SUITE-00", f"{path}: AiEvaluationDefinition requires <{req}>."))
    if fields.get("subjectType") != "AGENT":
        out.append(("ERROR", "PI-SUITE-00", f"{path}: subjectType must be AGENT (the only supported value)."))
    cases = [c for c in root if _local(c.tag) == "testCase"]
    utterances = [(u.text or "") for c in cases for u in c.iter() if _local(u.tag) == "utterance"]
    if len(cases) < MIN_CASES:
        out.append(("WARN", "PI-SUITE-01", f"{path}: {len(cases)} test case(s); an adversarial suite needs at least {MIN_CASES}."))
    if not any(re.search(r"[^\x00-\x7f]", u) or NON_ENGLISH.search(u) for u in utterances):
        out.append(("WARN", "PI-SUITE-02", f"{path}: no non-English utterance; add at least two per payload family."))
    no_action = False
    for case in cases:
        for exp in (e for e in case.iter() if _local(e.tag) == "expectation"):
            name = next((c.text or "" for c in exp if _local(c.tag) == "name"), "").strip()
            value = next((c.text or "" for c in exp if _local(c.tag) == "expectedValue"), "").strip()
            if name == "action_sequence_match" and value.replace(" ", "") == "[]":
                no_action = True
    if not no_action:
        out.append(("WARN", "PI-SUITE-03", f"{path}: no case asserts action_sequence_match [] (agent takes no action)."))
    for family, pattern in FAMILIES.items():
        if not any(pattern.search(u) for u in utterances):
            out.append(("WARN", "PI-SUITE-04", f"{path}: no '{family}' payload in the suite."))
    return out


def scan(root: Path) -> tuple[int, list[tuple[str, str, str]]]:
    findings: list[tuple[str, str, str]] = []
    classes = sorted(p for p in root.rglob("*.cls") if p.is_file())
    actions = [p for p in classes if "@invocablemethod" in p.read_text(encoding="utf-8", errors="replace").lower()]
    topics = sorted(p for p in root.rglob("*") if p.is_file() and ".genAiPlugin" in p.name)
    suites = sorted(p for p in root.rglob("*") if p.is_file() and ".aiEvaluationDefinition" in p.name)
    for p in actions:
        findings.extend(check_action(p))
    for p in topics:
        findings.extend(check_topic(p))
    for p in suites:
        findings.extend(check_suite(p))
    if actions and not suites:
        findings.append(("WARN", "PI-SUITE-05", f"{root}: {len(actions)} invocable action(s) and no AiEvaluationDefinition suite."))
    return len(actions) + len(topics) + len(suites), findings


def self_test() -> int:
    import tempfile
    here = Path(__file__).resolve().parent
    _, good = scan(here / "fixtures" / "good")
    _, bad = scan(here / "fixtures" / "bad")
    expected = {"PI-SYS-01", "PI-TRUST-01", "PI-TOPIC-01", "PI-TOPIC-02", "PI-SUITE-00", "PI-SUITE-01",
                "PI-SUITE-02", "PI-SUITE-03", "PI-SUITE-04"}
    seen = {rule for _, rule, _ in bad}
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "Lonely.cls").write_text(
            "public with sharing class Lonely { @InvocableMethod public static void run(List<Id> ids) {} }",
            encoding="utf-8")
        _, lonely = scan(Path(tmp))
    seen |= {rule for _, rule, _ in lonely}
    expected.add("PI-SUITE-05")
    md = (here.parent / "references" / "metadata-examples.md").read_text(encoding="utf-8")
    own: list[tuple[str, str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, block in enumerate(re.findall(r"```xml\n(.*?)```", md, flags=re.DOTALL)):
            if "<AiEvaluationDefinition" in block:
                (Path(tmp) / f"s{i}.aiEvaluationDefinition-meta.xml").write_text(block, encoding="utf-8")
            elif "<GenAiPlugin" in block:
                (Path(tmp) / f"t{i}.genAiPlugin-meta.xml").write_text(block, encoding="utf-8")
        _, own = scan(Path(tmp))
    ok = not good and expected <= seen and not own
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print("   ", *f)
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    print(f"skill examples: {len(own)} finding(s) (expected 0)")
    for f in own:
        print("   ", *f)
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check an Agentforce project for prompt-injection exposure.")
    ap.add_argument("--manifest-dir", default=".", help="Source folder to scan (default: current directory).")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as failures.")
    ap.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    count, findings = scan(root)
    if count == 0:
        print(f"WARN: no invocable actions, topics, or AiEvaluationDefinition suites under {root}; nothing checked.")
        return 0
    for severity, rule, message in findings:
        print(f"{severity} {rule}: {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"Checked {count} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
