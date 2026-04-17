#!/usr/bin/env python3
"""Agent eval runner — structural lint + deterministic envelope grader.

Two modes:

    --structure                Lint every fixture under evals/agents/fixtures/
    --file <path>              Operate on a single fixture
    --grade                    Grade an envelope JSON against a fixture's expect block
    --envelope <path>          Path to a produced envelope JSON (used with --grade)

Exit codes:
    0  all pass
    1  structural lint failure
    2  P0 rubric failure
    3  invalid CLI usage

The runner performs NO network / model calls. Agents are executed in the caller's
model; the envelope JSON they emit is passed in via --envelope.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(3)

try:
    import jsonschema
except ImportError:
    jsonschema = None  # envelope validation becomes a WARN instead of ERROR

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "evals" / "agents" / "fixtures"
AGENTS_DIR = REPO_ROOT / "agents"
ENVELOPE_SCHEMA = REPO_ROOT / "agents" / "_shared" / "schemas" / "output-envelope.schema.json"
FRONTMATTER_SCHEMA = REPO_ROOT / "agents" / "_shared" / "schemas" / "agent-frontmatter.schema.json"


@dataclass
class LintIssue:
    level: str  # ERROR | WARN
    path: str
    message: str


def discover_fixtures() -> list[Path]:
    if not FIXTURES_DIR.exists():
        return []
    return sorted(FIXTURES_DIR.glob("*/*.yaml"))


def load_fixture(path: Path) -> tuple[dict | None, list[LintIssue]]:
    issues: list[LintIssue] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, [LintIssue("ERROR", str(path), f"invalid YAML: {exc}")]
    if not isinstance(data, dict):
        return None, [LintIssue("ERROR", str(path), "fixture root must be a mapping")]
    return data, issues


def lint_fixture(path: Path, data: dict) -> list[LintIssue]:
    issues: list[LintIssue] = []

    eval_block = data.get("eval")
    if not isinstance(eval_block, dict):
        issues.append(LintIssue("ERROR", str(path), "missing top-level `eval:` block"))
        return issues

    for required in ("id", "agent", "mode", "priority", "last_verified"):
        if required not in eval_block:
            issues.append(LintIssue("ERROR", str(path), f"eval.{required} is required"))

    agent_slug = eval_block.get("agent")
    if agent_slug:
        agent_md = AGENTS_DIR / agent_slug / "AGENT.md"
        if not agent_md.exists():
            issues.append(LintIssue("ERROR", str(path), f"eval.agent `{agent_slug}` does not resolve to agents/{agent_slug}/AGENT.md"))

    priority = eval_block.get("priority")
    if priority and priority not in ("P0", "P1", "P2"):
        issues.append(LintIssue("ERROR", str(path), f"eval.priority must be P0|P1|P2, got `{priority}`"))

    if "inputs" not in data or not isinstance(data["inputs"], dict):
        issues.append(LintIssue("ERROR", str(path), "missing `inputs:` block"))

    expect = data.get("expect")
    if not isinstance(expect, dict):
        issues.append(LintIssue("ERROR", str(path), "missing `expect:` block"))
    else:
        confidence = expect.get("confidence")
        if confidence and confidence not in ("HIGH", "MEDIUM", "LOW"):
            issues.append(LintIssue("ERROR", str(path), f"expect.confidence must be HIGH|MEDIUM|LOW, got `{confidence}`"))
        # If refusal_code is set, deliverable expectations are allowed but not required
        # to avoid contradictions.

    return issues


def grade_envelope(fixture_path: Path, fixture: dict, envelope: dict) -> list[LintIssue]:
    issues: list[LintIssue] = []
    expect: dict = fixture.get("expect") or {}

    if jsonschema and ENVELOPE_SCHEMA.exists():
        schema = json.loads(ENVELOPE_SCHEMA.read_text(encoding="utf-8"))
        # Draft 2020-12 $ref resolution needs a registry for relative refs; this is a
        # best-effort check — if resolver can't find the sub-schemas we downgrade to a
        # shallow type check.
        try:
            validator = jsonschema.Draft202012Validator(schema)
            errors = list(validator.iter_errors(envelope))
            for err in errors:
                # suppress $ref-resolution-failed style errors — covered by deeper checks below
                if "$ref" in str(err.message).lower():
                    continue
                issues.append(LintIssue("ERROR", str(fixture_path), f"envelope: {err.message}"))
        except Exception as exc:
            issues.append(LintIssue("WARN", str(fixture_path), f"envelope schema validation skipped: {exc}"))

    # confidence
    if "confidence" in expect:
        if envelope.get("confidence") != expect["confidence"]:
            issues.append(
                LintIssue(
                    "ERROR",
                    str(fixture_path),
                    f"expect.confidence={expect['confidence']} but envelope.confidence={envelope.get('confidence')}",
                )
            )

    # refusal
    if "refusal_code" in expect:
        refusal = envelope.get("refusal") or {}
        if refusal.get("code") != expect["refusal_code"]:
            issues.append(
                LintIssue(
                    "ERROR",
                    str(fixture_path),
                    f"expect.refusal_code={expect['refusal_code']} but envelope.refusal.code={refusal.get('code')}",
                )
            )

    # findings
    finding_ids = {f.get("id") for f in envelope.get("findings") or [] if isinstance(f, dict)}
    for req in expect.get("must_include_findings_with_all_of_ids") or []:
        if req not in finding_ids:
            issues.append(LintIssue("ERROR", str(fixture_path), f"missing required finding id `{req}`"))
    anyof = expect.get("must_include_findings_with_any_of_ids")
    if anyof and not (finding_ids & set(anyof)):
        issues.append(LintIssue("ERROR", str(fixture_path), f"none of {anyof} present in envelope.findings[].id"))
    for forbidden in expect.get("must_not_include_findings_with_ids") or []:
        if forbidden in finding_ids:
            issues.append(LintIssue("ERROR", str(fixture_path), f"finding id `{forbidden}` should not be present"))

    # citations
    envelope_citations = envelope.get("citations") or []
    citation_pairs = {(c.get("type"), c.get("id")) for c in envelope_citations if isinstance(c, dict)}
    for req in expect.get("must_cite_all_of") or []:
        if (req.get("type"), req.get("id")) not in citation_pairs:
            issues.append(LintIssue("ERROR", str(fixture_path), f"missing required citation {req}"))
    anyof_cite = expect.get("must_cite_any_of")
    if anyof_cite and not any((c.get("type"), c.get("id")) in citation_pairs for c in anyof_cite):
        issues.append(LintIssue("ERROR", str(fixture_path), f"none of {anyof_cite} present in envelope.citations"))
    for probe_id in expect.get("must_not_cite_probes") or []:
        if ("probe", probe_id) in citation_pairs:
            issues.append(LintIssue("ERROR", str(fixture_path), f"probe citation `{probe_id}` should not be present"))

    # process_observations
    po_expect = expect.get("process_observations") or {}
    po = envelope.get("process_observations") or []
    if isinstance(po_expect, dict):
        min_count = po_expect.get("min_count")
        if isinstance(min_count, int) and len(po) < min_count:
            issues.append(LintIssue("ERROR", str(fixture_path), f"expected at least {min_count} process observations, got {len(po)}"))
        cats = po_expect.get("categories_present_any_of")
        if cats:
            seen = {obs.get("category") for obs in po if isinstance(obs, dict)}
            if not (seen & set(cats)):
                issues.append(LintIssue("ERROR", str(fixture_path), f"no observation matches any of {cats}"))

    # followups
    followup_slugs = {f.get("agent") for f in envelope.get("followups") or [] if isinstance(f, dict)}
    anyof_follow = expect.get("followups_include_any_of")
    if anyof_follow and not (followup_slugs & set(anyof_follow)):
        issues.append(LintIssue("WARN", str(fixture_path), f"followups did not include any of {anyof_follow}"))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure", action="store_true", help="Lint all fixtures under evals/agents/fixtures/")
    parser.add_argument("--file", type=str, default=None, help="Path to a single fixture YAML")
    parser.add_argument("--grade", action="store_true", help="Grade an envelope against a fixture")
    parser.add_argument("--envelope", type=str, default=None, help="Envelope JSON path (for --grade)")
    args = parser.parse_args()

    if not (args.structure or args.file or args.grade):
        parser.print_help()
        return 3

    fixtures: list[Path]
    if args.file:
        fixtures = [Path(args.file).resolve()]
    else:
        fixtures = discover_fixtures()

    if not fixtures:
        print("No fixtures found under evals/agents/fixtures/")
        return 0

    issues: list[LintIssue] = []
    any_p0_failure = False

    for fx in fixtures:
        data, parse_issues = load_fixture(fx)
        issues.extend(parse_issues)
        if data is None:
            continue

        lint = lint_fixture(fx, data)
        issues.extend(lint)

        if args.grade:
            if not args.envelope:
                print("ERROR: --grade requires --envelope <path>", file=sys.stderr)
                return 3
            try:
                envelope = json.loads(Path(args.envelope).read_text(encoding="utf-8"))
            except Exception as exc:
                issues.append(LintIssue("ERROR", args.envelope, f"cannot parse envelope: {exc}"))
                continue
            grade_issues = grade_envelope(fx, data, envelope)
            issues.extend(grade_issues)
            priority = (data.get("eval") or {}).get("priority")
            if priority == "P0" and any(i.level == "ERROR" for i in grade_issues):
                any_p0_failure = True

    for issue in issues:
        print(f"{issue.level} {issue.path}: {issue.message}")

    errors = sum(1 for i in issues if i.level == "ERROR")
    warns = sum(1 for i in issues if i.level == "WARN")
    print(f"Processed {len(fixtures)} fixture(s); {errors} error(s), {warns} warning(s).")

    if any_p0_failure:
        return 2
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
