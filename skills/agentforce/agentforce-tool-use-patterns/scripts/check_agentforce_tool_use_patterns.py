#!/usr/bin/env python3
"""Lint the tool contract of Agentforce actions: Apex invocables, GenAiFunction, schemas, GenAiPlugin.

Stdlib only. Scans --manifest-dir for:

- Apex classes (``*.cls``) that declare ``@InvocableMethod``. Rules follow the
  Apex Developer Guide, "InvocableMethod Annotation" and "Making Callouts to
  External Systems from Invocable Actions", and the Generative AI guide
  (Spring '26) "Considerations for Custom Actions".
- ``GenAiFunction`` components (``*.genAiFunction`` or ``*.genAiFunction-meta.xml``)
  and the ``input/schema.json`` and ``output/schema.json`` files beside them.
  Rules follow the Metadata API reference for GenAiFunction.
- ``GenAiPlugin`` components (``*.genAiPlugin`` or ``*.genAiPlugin-meta.xml``).
  The 15-action guidance comes from the Generative AI guide, "Agents Limits".

Exit codes: 0 when there is no ERROR (and no WARN with --strict); 1 otherwise.
A missing --manifest-dir is an ERROR (exit 1). A directory with nothing to
check prints a WARN and exits 0.

Usage:
    python3 check_agentforce_tool_use_patterns.py --manifest-dir force-app/main/default
    python3 check_agentforce_tool_use_patterns.py --manifest-dir force-app --strict
    python3 check_agentforce_tool_use_patterns.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

# PlannerFunctionInvocableTargetType values in the Metadata API reference.
TARGET_TYPES = {
    "api", "apex", "auraEnabled", "createCatalogItemRequest", "executeIntegrationProcedure",
    "externalService", "flow", "generatePromptResponse", "mcpTool", "namedQuery", "quickAction",
    "retriever", "runExpressionSet", "slack", "standardInvocableAction", "stub",
}
MAX_TEXT_LENGTH = 250            # lightning__textType maximum length
MAX_ACTIONS_PER_TOPIC = 15       # Generative AI guide, Agents Limits
MIN_DESCRIPTION_WORDS = 8
WRITE_WORDS = re.compile(r"\b(create|creates|update|updates|delete|deletes|cancel|cancels|send|sends|submit|submits|refund|refunds|close|closes)\b", re.I)

INVOCABLE_METHOD_RE = re.compile(
    r"@InvocableMethod\s*(?P<args>\((?:[^()]|\([^()]*\))*\))?\s*"
    r"(?:(?:public|global|static|override)\s+)+[\w<>.,\s]+?\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)",
    re.S,
)
INVOCABLE_VAR_RE = re.compile(
    r"@InvocableVariable\s*(?P<args>\((?:[^()]|\([^()]*\))*\))?\s*"
    r"(?:(?:public|global|static|final)\s+)+(?P<type>[\w<>.,\s]+?)\s+(?P<name>\w+)\s*;",
    re.S,
)
HTTP_RE = re.compile(r"\bnew\s+Http\s*\(|\bHttpRequest\b|\.send\s*\(")


class Finding:
    def __init__(self, severity: str, rule: str, path: Path, message: str) -> None:
        self.severity = severity
        self.rule = rule
        self.path = path
        self.message = message

    def render(self) -> str:
        return f"{self.severity} [{self.rule}] {self.path}: {self.message}"


def _strip_comments(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"//[^\n]*", "", source)


def _has_arg(args: str | None, name: str) -> bool:
    return bool(args) and re.search(rf"\b{name}\s*=", args) is not None


def check_apex(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    source = _strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
    methods = list(INVOCABLE_METHOD_RE.finditer(source))
    if not methods:
        return findings
    if len(methods) > 1:
        findings.append(Finding("ERROR", "TU-002", path, "only one method in a class can carry @InvocableMethod"))
    for match in methods:
        args = match.group("args")
        params = match.group("params").strip()
        if params and not re.match(r"List\s*<", params):
            findings.append(Finding("ERROR", "TU-001", path, f"{match.group('name')}: the single input parameter must be a List, found '{params}'"))
        if not _has_arg(args, "description"):
            findings.append(Finding("WARN", "TU-005", path, f"{match.group('name')}: no description; it seeds the agent action instructions"))
    if HTTP_RE.search(source) and not any(re.search(r"callout\s*=\s*true", m.group("args") or "", re.I) for m in methods):
        findings.append(Finding("WARN", "TU-007", path, "the class makes an HTTP callout but its @InvocableMethod does not declare callout=true"))
    for var in INVOCABLE_VAR_RE.finditer(source):
        vtype = " ".join(var.group("type").split())
        if vtype == "Object":
            findings.append(Finding("ERROR", "TU-003", path, f"{var.group('name')}: the generic Object type is not supported for invocable variables"))
        elif re.match(r"(List|Set|Map)\s*<", vtype):
            findings.append(Finding("WARN", "TU-004", path, f"{var.group('name')}: collection type {vtype}; custom agent actions that reference Apex support only primitive data types"))
        if not _has_arg(var.group("args"), "description"):
            findings.append(Finding("WARN", "TU-006", path, f"{var.group('name')}: no description; the agent copies it into the parameter instructions"))
    return findings


def _text(root: ET.Element, tag: str) -> str:
    elem = root.find(NS + tag)
    return elem.text.strip() if elem is not None and elem.text else ""


def _component_dir(path: Path) -> Path:
    return path.parent


def check_schema(path: Path, kind: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [Finding("ERROR", "TU-021", path, f"schema does not parse as JSON: {exc}")]
    if data.get("lightning:type") != "lightning__objectType":
        findings.append(Finding("ERROR", "TU-022", path, "the schema root lightning:type must be lightning__objectType"))
    props = data.get("properties") or {}
    if not isinstance(props, dict) or not props:
        findings.append(Finding("ERROR", "TU-021", path, "schema has no properties"))
        props = {}
    for name, prop in props.items():
        if not isinstance(prop, dict):
            continue
        for required in ("title", "lightning:type"):
            if not prop.get(required):
                findings.append(Finding("ERROR", "TU-021", path, f"property '{name}' is missing required '{required}'"))
        if prop.get("lightning:type") == "lightning__textType":
            max_len = prop.get("maxLength")
            if isinstance(max_len, int) and max_len > MAX_TEXT_LENGTH:
                findings.append(Finding("WARN", "TU-023", path, f"property '{name}' sets maxLength {max_len}; the text type maximum is {MAX_TEXT_LENGTH}"))
        if kind == "input" and not prop.get("description"):
            findings.append(Finding("WARN", "TU-025", path, f"input '{name}' has no description; the LLM relies on it to choose a value"))
    if kind == "input":
        for req in data.get("required", []) or []:
            if req not in props:
                findings.append(Finding("ERROR", "TU-024", path, f"required input '{req}' is not defined in properties"))
    if kind == "output" and props and not any(isinstance(p, dict) and p.get("copilotAction:isUsedByPlanner") is True for p in props.values()):
        findings.append(Finding("ERROR", "TU-020", path, "no output sets copilotAction:isUsedByPlanner to true; the planner then returns random responses"))
    return findings


def check_function(path: Path, root_dir: Path) -> tuple[list[Finding], str, str]:
    findings: list[Finding] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding("ERROR", "TU-010", path, f"XML does not parse: {exc}")], "", ""
    name = path.name.split(".")[0]
    for required in ("masterLabel", "invocationTarget", "invocationTargetType"):
        if not _text(root, required):
            findings.append(Finding("ERROR", "TU-010", path, f"required field {required} is missing"))
    target_type = _text(root, "invocationTargetType")
    target = _text(root, "invocationTarget")
    if target_type and target_type not in TARGET_TYPES:
        findings.append(Finding("ERROR", "TU-011", path, f"invocationTargetType '{target_type}' is not a documented value"))
    description = _text(root, "description")
    if len(description.split()) < MIN_DESCRIPTION_WORDS:
        findings.append(Finding("WARN", "TU-012", path, f"description has {len(description.split())} word(s); say what the action does, when to use it, and what it does not do"))
    label_and_desc = f"{_text(root, 'masterLabel')} {description}"
    if WRITE_WORDS.search(label_and_desc) and not re.search(r"\bnever changes\b|\bread-only\b|\bdoes not change\b", label_and_desc, re.I):
        if _text(root, "isConfirmationRequired").lower() != "true":
            findings.append(Finding("WARN", "TU-014", path, "the label or description describes a write but isConfirmationRequired is not true"))
    if target and target_type == "apex" and any(root_dir.rglob("*.cls")):
        if not any(p.name == f"{target}.cls" for p in root_dir.rglob("*.cls")):
            findings.append(Finding("WARN", "TU-013", path, f"Apex target {target}.cls was not found under the scanned directory"))
    if target and target_type == "flow" and any(root_dir.rglob("*.flow-meta.xml")):
        if not any(p.name == f"{target}.flow-meta.xml" for p in root_dir.rglob("*.flow-meta.xml")):
            findings.append(Finding("WARN", "TU-013", path, f"flow target {target} was not found under the scanned directory"))
    comp = _component_dir(path)
    output_schema = comp / "output" / "schema.json"
    input_schema = comp / "input" / "schema.json"
    if input_schema.exists():
        findings.extend(check_schema(input_schema, "input"))
    if output_schema.exists():
        findings.extend(check_schema(output_schema, "output"))
    else:
        findings.append(Finding("WARN", "TU-020", path, "no output/schema.json beside this action, so the planner-visible outputs cannot be checked"))
    return findings, name, description


def check_plugin(path: Path, known_functions: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding("ERROR", "TU-030", path, f"XML does not parse: {exc}")]
    names = [(_text(f, "functionName")) for f in root.findall(NS + "genAiFunctions")]
    if len(names) > MAX_ACTIONS_PER_TOPIC:
        findings.append(Finding("WARN", "TU-032", path, f"{len(names)} actions in one subagent; the guidance is no more than {MAX_ACTIONS_PER_TOPIC}"))
    if known_functions:
        for fname in names:
            if fname and "__" not in fname and fname not in known_functions:
                findings.append(Finding("WARN", "TU-031", path, f"functionName '{fname}' is not among the scanned GenAiFunction components"))
    return findings


def run(root_dir: Path) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    scanned = 0
    for cls in sorted(root_dir.rglob("*.cls")):
        result = check_apex(cls)
        if "@InvocableMethod" in cls.read_text(encoding="utf-8", errors="ignore"):
            scanned += 1
        findings.extend(result)
    functions = sorted(p for p in root_dir.rglob("*") if p.is_file() and (p.name.endswith(".genAiFunction") or p.name.endswith(".genAiFunction-meta.xml")))
    known: set[str] = set()
    descriptions: dict[str, Path] = {}
    for fn in functions:
        scanned += 1
        result, name, description = check_function(fn, root_dir)
        findings.extend(result)
        known.add(name)
        key = " ".join(description.lower().split())
        if key:
            if key in descriptions:
                findings.append(Finding("WARN", "TU-030", fn, f"description is identical to {descriptions[key].name}; the planner cannot tell the two apart"))
            else:
                descriptions[key] = fn
    plugins = sorted(p for p in root_dir.rglob("*") if p.is_file() and (p.name.endswith(".genAiPlugin") or p.name.endswith(".genAiPlugin-meta.xml")))
    for plugin in plugins:
        scanned += 1
        findings.extend(check_plugin(plugin, known))
    return findings, scanned


def report(root_dir: Path, strict: bool) -> int:
    if not root_dir.exists():
        print(f"ERROR: manifest directory not found: {root_dir}")
        sys.exit(1)
    findings, scanned = run(root_dir)
    if scanned == 0:
        print(f"WARN: no invocable Apex, GenAiFunction or GenAiPlugin components found under {root_dir}")
        return 0
    for finding in findings:
        print(finding.render())
    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = sum(1 for f in findings if f.severity == "WARN")
    print(f"Scanned {scanned} component(s): {errors} error(s), {warns} warning(s).")
    if errors or (strict and warns):
        return 1
    return 0


def _materialize_skill_example(tmp: Path) -> int:
    """Write every fenced block preceded by a '**File path:**' line in metadata-examples.md."""
    examples = Path(__file__).resolve().parents[1] / "references" / "metadata-examples.md"
    if not examples.exists():
        return 0
    text = examples.read_text(encoding="utf-8")
    written = 0
    for match in re.finditer(r"\*\*File path:\*\* `([^`]+)`\s*\n+```[a-z]*\n(.*?)```", text, re.S):
        target = tmp / match.group(1)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(match.group(2), encoding="utf-8")
        written += 1
    return written


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    failures: list[str] = []

    good, _ = run(base / "good")
    if good:
        failures.append("good fixtures produced findings: " + "; ".join(f.render() for f in good))

    bad, _ = run(base / "bad")
    expected = {"TU-001", "TU-002", "TU-003", "TU-004", "TU-005", "TU-006", "TU-007", "TU-010",
                "TU-011", "TU-012", "TU-014", "TU-020", "TU-021", "TU-022", "TU-023", "TU-024",
                "TU-025", "TU-030", "TU-031", "TU-032"}
    missing = expected - {f.rule for f in bad}
    if missing:
        failures.append(f"bad fixtures did not trigger: {sorted(missing)}")

    _, empty_count = run(base / "empty")
    if empty_count != 0:
        failures.append("empty fixture directory was not treated as empty")

    with tempfile.TemporaryDirectory() as tmp:
        written = _materialize_skill_example(Path(tmp))
        if written < 5:
            failures.append(f"expected at least 5 file blocks in references/metadata-examples.md, found {written}")
        else:
            errors = [f for f in run(Path(tmp))[0] if f.severity == "ERROR"]
            if errors:
                failures.append("skill example has errors: " + "; ".join(f.render() for f in errors))

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("self-test passed: good=clean, bad=all rules fired, empty=skipped, skill example=no errors")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint Agentforce action tool contracts: invocable Apex, GenAiFunction schemas, GenAiPlugin.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the metadata to scan (default: current directory).")
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
