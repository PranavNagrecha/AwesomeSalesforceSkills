#!/usr/bin/env python3
"""Lint Agentforce eval assets: AiEvaluationDefinition metadata and harness fixtures.

Stdlib only. Two asset kinds are checked under --manifest-dir:

1. AiEvaluationDefinition files (``*.aiEvaluationDefinition`` or
   ``*.aiEvaluationDefinition-meta.xml``). Rules follow the Metadata API
   reference for AiEvaluationDefinition (API 63.0+) and the Agentforce
   Developer Guide pages "Build Tests in Metadata API", "Add Custom Evaluation
   Criteria to a Test Case", "Considerations for the Testing API" and "Use Test
   Results to Improve Your Agent".
2. Harness fixtures: markdown files whose YAML frontmatter declares
   ``dimensions:`` (the fixture format in SKILL.md).

Exit codes: 0 when there is no ERROR (and no WARN with --strict); 1 otherwise.
A missing --manifest-dir is an ERROR (exit 1). A directory with no eval assets
prints a WARN and exits 0.

Usage:
    python3 check_agentforce_eval_harness.py --manifest-dir force-app
    python3 check_agentforce_eval_harness.py --manifest-dir evals --strict
    python3 check_agentforce_eval_harness.py --self-test
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

# Expectation names documented for AiEvaluationDefinition.
VALUE_REQUIRED = {"topic_sequence_match", "action_sequence_match", "bot_response_rating"}
QUALITY_METRICS = {"coherence", "completeness", "conciseness", "output_latency_milliseconds"}
CUSTOM_EVALS = {"string_comparison", "numeric_comparison"}
KNOWN_EXPECTATIONS = VALUE_REQUIRED | QUALITY_METRICS | CUSTOM_EVALS

STRING_OPERATORS = {"equals", "contains", "startswith", "endswith"}
NUMERIC_OPERATORS = {"equals", "greater_than_or_equal", "greater_than", "less_than", "less_than_or_equal"}

MAX_TEST_CASES = 1000          # Considerations for the Testing API
MAX_PARAMETER_CHARS = 100      # Custom evaluation criteria: each parameter field
API_NAME_RE = re.compile(r"^[A-Za-z](?!.*__)[A-Za-z0-9_]*(?<!_)$")
SF_ID_RE = re.compile(r"\b(?:001|003|005|006|00Q|500|801|a0[0-9A-Za-z])[0-9A-Za-z]{12}(?:[0-9A-Za-z]{3})?\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE_RE = re.compile(r"\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")

FIXTURE_REQUIRED_KEYS = ("id", "agent", "dimensions", "severity")
FIXTURE_SECTIONS = ("## input transcript", "## expected agent behavior")
SEVERITIES = {"P0", "P1", "P2", "P3"}


class Finding:
    def __init__(self, severity: str, rule: str, path: Path, message: str) -> None:
        self.severity = severity
        self.rule = rule
        self.path = path
        self.message = message

    def render(self) -> str:
        return f"{self.severity} [{self.rule}] {self.path}: {self.message}"


def _child(elem: ET.Element | None, tag: str) -> ET.Element | None:
    if elem is None:
        return None
    return elem.find(NS + tag)


def _text(elem: ET.Element | None) -> str:
    if elem is None or elem.text is None:
        return ""
    return elem.text.strip()


def _pii_findings(text: str, path: Path, rule: str, where: str) -> list[Finding]:
    found: list[Finding] = []
    if EMAIL_RE.search(text) or SSN_RE.search(text) or PHONE_RE.search(text):
        found.append(Finding("WARN", rule, path, f"{where} looks like it contains personal data; generalize or synthesize it instead of copying production records"))
    return found


def check_definition(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding("ERROR", "AIEVAL-000", path, f"XML does not parse: {exc}")]
    if root.tag != NS + "AiEvaluationDefinition":
        return [Finding("ERROR", "AIEVAL-000", path, "root element is not AiEvaluationDefinition in the metadata namespace")]

    if _text(_child(root, "subjectType")) != "AGENT":
        findings.append(Finding("ERROR", "AIEVAL-001", path, "subjectType must be AGENT, the only supported value"))
    name = _text(_child(root, "name"))
    if not name:
        findings.append(Finding("ERROR", "AIEVAL-002", path, "name is required"))
    elif not API_NAME_RE.match(name):
        findings.append(Finding("ERROR", "AIEVAL-002", path, f"name '{name}' must start with a letter, use only letters, digits and underscores, and not end with or double an underscore"))
    if not _text(_child(root, "subjectName")):
        findings.append(Finding("ERROR", "AIEVAL-003", path, "subjectName (the agent API name) is required"))
    if not _text(_child(root, "subjectVersion")):
        findings.append(Finding("WARN", "AIEVAL-004", path, "subjectVersion is missing, so the latest active agent version is tested and the baseline moves on every activation"))

    cases = root.findall(NS + "testCase")
    if not cases:
        findings.append(Finding("ERROR", "AIEVAL-007", path, "definition has no testCase"))
    if len(cases) > MAX_TEST_CASES:
        findings.append(Finding("ERROR", "AIEVAL-005", path, f"{len(cases)} test cases exceeds the documented maximum of {MAX_TEST_CASES}"))

    seen_numbers: set[str] = set()
    has_negative_case = False
    for index, case in enumerate(cases, start=1):
        label = f"testCase {index}"
        number = _text(_child(case, "number"))
        if number:
            if number in seen_numbers:
                findings.append(Finding("WARN", "AIEVAL-014", path, f"{label}: duplicate number {number}"))
            seen_numbers.add(number)
        inputs = _child(case, "inputs")
        utterance = _text(_child(inputs, "utterance"))
        if not utterance:
            findings.append(Finding("ERROR", "AIEVAL-006", path, f"{label}: inputs/utterance is required"))
        else:
            if SF_ID_RE.search(utterance):
                findings.append(Finding("WARN", "AIEVAL-018", path, f"{label}: utterance contains a hard-coded record ID; it will not exist in a refreshed sandbox"))
            findings.extend(_pii_findings(utterance, path, "AIEVAL-019", f"{label} utterance"))
        if inputs is not None:
            for turn in inputs.findall(NS + "conversationHistory"):
                role = _text(_child(turn, "role"))
                if role == "agent" and not _text(_child(turn, "topic")):
                    findings.append(Finding("WARN", "AIEVAL-016", path, f"{label}: an agent turn in conversationHistory names no subagent (topic)"))
                if not _text(_child(turn, "index")):
                    findings.append(Finding("WARN", "AIEVAL-016", path, f"{label}: a conversationHistory entry has no index"))
                findings.extend(_pii_findings(_text(_child(turn, "message")), path, "AIEVAL-019", f"{label} conversation history"))

        expectations = case.findall(NS + "expectation")
        if not expectations:
            findings.append(Finding("ERROR", "AIEVAL-007", path, f"{label}: no expectation, so the case can never fail"))
        for exp in expectations:
            exp_name = _text(_child(exp, "name"))
            value = _text(_child(exp, "expectedValue"))
            if exp_name not in KNOWN_EXPECTATIONS:
                findings.append(Finding("ERROR", "AIEVAL-008", path, f"{label}: unknown expectation name '{exp_name}'"))
                continue
            if exp_name in VALUE_REQUIRED and not value:
                findings.append(Finding("ERROR", "AIEVAL-009", path, f"{label}: {exp_name} needs an expectedValue"))
            if exp_name == "action_sequence_match" and value:
                if not (value.startswith("[") and value.endswith("]")):
                    findings.append(Finding("ERROR", "AIEVAL-010", path, f"{label}: action_sequence_match expectedValue must be a list literal such as [\"Look_Up_Order\"] or []"))
                elif re.fullmatch(r"\[\s*\]", value):
                    has_negative_case = True
            if exp_name in VALUE_REQUIRED and value and SF_ID_RE.search(value):
                findings.append(Finding("WARN", "AIEVAL-018", path, f"{label}: {exp_name} expectedValue contains a hard-coded record ID"))
            if exp_name in QUALITY_METRICS and value:
                findings.append(Finding("WARN", "AIEVAL-013", path, f"{label}: {exp_name} needs no expectedValue; the value is ignored"))
            if exp_name in CUSTOM_EVALS:
                findings.extend(_check_custom_eval(exp, exp_name, path, label))
    if cases and not has_negative_case:
        findings.append(Finding("WARN", "AIEVAL-017", path, "no test case expects an empty action list ([]); add at least one out-of-scope or refusal case"))
    return findings


def _check_custom_eval(exp: ET.Element, exp_name: str, path: Path, label: str) -> list[Finding]:
    findings: list[Finding] = []
    params: dict[str, tuple[str, str]] = {}
    for param in exp.findall(NS + "parameter"):
        pname = _text(_child(param, "name"))
        pvalue = _text(_child(param, "value"))
        params[pname] = (pvalue, _text(_child(param, "isReference")))
        if len(pvalue) > MAX_PARAMETER_CHARS:
            findings.append(Finding("ERROR", "AIEVAL-012", path, f"{label}: {exp_name} parameter '{pname}' is {len(pvalue)} characters; each parameter field is limited to {MAX_PARAMETER_CHARS}"))
    for required in ("operator", "actual", "expected"):
        if required not in params:
            findings.append(Finding("ERROR", "AIEVAL-011", path, f"{label}: {exp_name} is missing the '{required}' parameter"))
    operator = params.get("operator", ("", ""))[0]
    allowed = STRING_OPERATORS if exp_name == "string_comparison" else NUMERIC_OPERATORS
    if operator and operator not in allowed:
        findings.append(Finding("ERROR", "AIEVAL-011", path, f"{label}: operator '{operator}' is not valid for {exp_name}"))
    actual = params.get("actual")
    if actual is not None and actual[0].startswith("$.") and actual[1].lower() != "true":
        findings.append(Finding("ERROR", "AIEVAL-011", path, f"{label}: the 'actual' JSONPath only resolves when isReference is true"))
    return findings


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()
    return data


def check_fixture(path: Path, meta: dict[str, str], text: str) -> list[Finding]:
    findings: list[Finding] = []
    for key in FIXTURE_REQUIRED_KEYS:
        if not meta.get(key):
            findings.append(Finding("ERROR", "FIX-001", path, f"frontmatter key '{key}' is missing or empty"))
    severity = meta.get("severity", "")
    if severity and severity not in SEVERITIES:
        findings.append(Finding("ERROR", "FIX-002", path, f"severity '{severity}' must be one of P0, P1, P2, P3"))
    lower = text.lower()
    for section in FIXTURE_SECTIONS:
        if section not in lower:
            findings.append(Finding("ERROR", "FIX-003", path, f"missing section '{section[3:]}'"))
    dims = [d.strip() for d in meta.get("dimensions", "").strip("[]").split(",") if d.strip()]
    rubric_start = lower.find("## scoring rubric")
    if dims and rubric_start == -1:
        findings.append(Finding("WARN", "FIX-004", path, "dimensions are declared but there is no Scoring rubric section"))
    elif dims:
        rubric = lower[rubric_start:]
        for dim in dims:
            if dim.lower() not in rubric:
                findings.append(Finding("WARN", "FIX-004", path, f"dimension '{dim}' has no rubric line"))
    body = text[text.find("\n---", 3) + 4:] if text.startswith("---") else text
    if SF_ID_RE.search(body):
        findings.append(Finding("WARN", "FIX-005", path, "fixture body contains a hard-coded record ID; use a placeholder resolved from the test-data manifest"))
    findings.extend(_pii_findings(body, path, "FIX-006", "fixture body"))
    return findings


def discover(root: Path) -> tuple[list[Path], list[tuple[Path, dict[str, str], str]]]:
    definitions: list[Path] = []
    fixtures: list[tuple[Path, dict[str, str], str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".aiEvaluationDefinition") or path.name.endswith(".aiEvaluationDefinition-meta.xml"):
            definitions.append(path)
        elif path.suffix == ".md":
            text = path.read_text(encoding="utf-8", errors="ignore")
            meta = _frontmatter(text)
            if "dimensions" in meta:
                fixtures.append((path, meta, text))
    return definitions, fixtures


def run(root: Path) -> tuple[list[Finding], int]:
    definitions, fixtures = discover(root)
    findings: list[Finding] = []
    for path in definitions:
        findings.extend(check_definition(path))
    p0_by_topic: dict[str, int] = {}
    for path, meta, text in fixtures:
        findings.extend(check_fixture(path, meta, text))
        topic = meta.get("topic", "")
        if topic:
            p0_by_topic.setdefault(topic, 0)
            if meta.get("severity") == "P0":
                p0_by_topic[topic] += 1
    for topic, count in sorted(p0_by_topic.items()):
        if count < 2:
            findings.append(Finding("WARN", "FIX-007", root, f"subagent '{topic}' has {count} P0 fixture(s); the workflow asks for at least 2"))
    return findings, len(definitions) + len(fixtures)


def report(root: Path, strict: bool) -> int:
    if not root.exists():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    findings, scanned = run(root)
    if scanned == 0:
        print(f"WARN: no AiEvaluationDefinition files or harness fixtures found under {root}")
        return 0
    for finding in findings:
        print(finding.render())
    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = sum(1 for f in findings if f.severity == "WARN")
    print(f"Scanned {scanned} eval asset(s): {errors} error(s), {warns} warning(s).")
    if errors or (strict and warns):
        return 1
    return 0


def _extract_skill_example(tmp: Path) -> Path | None:
    """Write the AiEvaluationDefinition block from references/metadata-examples.md to tmp."""
    examples = Path(__file__).resolve().parents[1] / "references" / "metadata-examples.md"
    if not examples.exists():
        return None
    text = examples.read_text(encoding="utf-8")
    for block in re.findall(r"```xml\n(.*?)```", text, re.S):
        if "<AiEvaluationDefinition" in block:
            target = tmp / "Skill_Example.aiEvaluationDefinition-meta.xml"
            target.write_text(block, encoding="utf-8")
            return target
    return None


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    failures: list[str] = []

    good, _ = run(base / "good")
    if good:
        failures.append("good fixtures produced findings: " + "; ".join(f.render() for f in good))

    bad, _ = run(base / "bad")
    expected_rules = {"AIEVAL-001", "AIEVAL-002", "AIEVAL-004", "AIEVAL-006", "AIEVAL-008",
                      "AIEVAL-009", "AIEVAL-010", "AIEVAL-011", "AIEVAL-012", "AIEVAL-013",
                      "AIEVAL-017", "AIEVAL-018", "AIEVAL-019", "FIX-001", "FIX-002", "FIX-003",
                      "FIX-004", "FIX-005", "FIX-007"}
    missing = expected_rules - {f.rule for f in bad}
    if missing:
        failures.append(f"bad fixtures did not trigger: {sorted(missing)}")

    _, empty_count = run(base / "empty")
    if empty_count != 0:
        failures.append("empty fixture directory was not treated as empty")

    with tempfile.TemporaryDirectory() as tmp:
        example = _extract_skill_example(Path(tmp))
        if example is None:
            failures.append("no AiEvaluationDefinition block found in references/metadata-examples.md")
        else:
            errors = [f for f in check_definition(example) if f.severity == "ERROR"]
            if errors:
                failures.append("skill example has errors: " + "; ".join(f.render() for f in errors))

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("self-test passed: good=clean, bad=all rules fired, empty=skipped, skill example=valid")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint AiEvaluationDefinition metadata and Agentforce eval harness fixtures.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on warnings as well as errors.")
    parser.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and the skill's own example, then exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    return report(Path(args.manifest_dir), args.strict)


if __name__ == "__main__":
    sys.exit(main())
