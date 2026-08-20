#!/usr/bin/env python3
"""Validate the SfSkills Salesforce AI Engineering Framework specification package.

This validator is intentionally deterministic and offline. It checks JSON Schema
conformance, cross-artifact references, requirement traceability, read-only policy,
context limits, sample run artifacts, and internal Markdown links.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover - explicit dependency failure
    raise SystemExit("jsonschema is required: python3 -m pip install jsonschema") from exc

REQ_RE = re.compile(r"\bSFAEF-\d{3}-\d{3}\b")
MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
PROHIBITED_PERMISSION_TOKENS = {
    "salesforce.metadata.write",
    "salesforce.data.write",
    "salesforce.apex.execute",
    "salesforce.permissions.write",
    "salesforce.users.write",
    "salesforce.packages.write",
    "salesforce.orgs.write",
}


@dataclass(frozen=True)
class Problem:
    code: str
    path: str
    message: str

    def render(self) -> str:
        return f"{self.code}: {self.path}: {self.message}"


class PackageValidator:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.problems: list[Problem] = []
        self.schemas: dict[str, dict[str, Any]] = {}

    def error(self, code: str, path: Path | str, message: str) -> None:
        if isinstance(path, Path):
            try:
                path = str(path.relative_to(self.root))
            except ValueError:
                path = str(path)
        self.problems.append(Problem(code, str(path), message))

    @staticmethod
    def load_json(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def require_paths(self) -> None:
        required = [
            "README.md",
            "SPEC_INDEX.md",
            "VERSION",
            "spec/000-status-and-conformance.md",
            "spec/220-roadmap-and-exit-criteria.md",
            "implementation/requirements.csv",
            "implementation/requirements.json",
            "implementation/CURSOR_BUILD_SFSAEF_V2.md",
            "implementation/REVIEW_RETURN_CONTRACT.md",
            "reference-kernel/saef_kernel",
            "reference-kernel/tests",
        ]
        for rel in required:
            if not (self.root / rel).exists():
                self.error("MISSING_REQUIRED_PATH", rel, "required package path does not exist")

    def load_and_validate_schemas(self) -> None:
        schema_dir = self.root / "schemas"
        if not schema_dir.is_dir():
            self.error("MISSING_SCHEMA_DIR", schema_dir, "schemas directory is missing")
            return
        for path in sorted(schema_dir.glob("*.schema.json")):
            try:
                schema = self.load_json(path)
                Draft202012Validator.check_schema(schema)
                self.schemas[path.name] = schema
            except Exception as exc:  # noqa: BLE001 - validation aggregator
                self.error("INVALID_SCHEMA", path, str(exc))

    def validate_directory(self, rel_dir: str, schema_name: str) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        directory = self.root / rel_dir
        if not directory.is_dir():
            self.error("MISSING_DEFINITION_DIR", directory, "definition directory is missing")
            return result
        schema = self.schemas.get(schema_name)
        if schema is None:
            self.error("MISSING_SCHEMA", schema_name, f"schema required for {rel_dir} was not loaded")
            return result
        validator = Draft202012Validator(schema)
        for path in sorted(directory.glob("*.json")):
            try:
                data = self.load_json(path)
            except Exception as exc:  # noqa: BLE001
                self.error("INVALID_JSON", path, str(exc))
                continue
            for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
                location = ".".join(str(x) for x in err.path) or "<root>"
                self.error("SCHEMA_VALIDATION", path, f"{location}: {err.message}")
            artifact_id = data.get("id")
            if not isinstance(artifact_id, str) or not artifact_id:
                continue
            if artifact_id in result:
                self.error("DUPLICATE_ID", path, f"duplicate id {artifact_id!r}")
            result[artifact_id] = data
        return result

    def validate_all_json(self) -> None:
        for path in sorted(self.root.rglob("*.json")):
            try:
                self.load_json(path)
            except Exception as exc:  # noqa: BLE001
                self.error("INVALID_JSON", path, str(exc))

    def validate_requirements(self) -> None:
        spec_ids: dict[str, tuple[str, int]] = {}
        for path in sorted((self.root / "spec").glob("*.md")):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for req_id in REQ_RE.findall(line):
                    if req_id in spec_ids:
                        prior = spec_ids[req_id]
                        self.error(
                            "DUPLICATE_REQUIREMENT",
                            path,
                            f"{req_id} also appears at {prior[0]}:{prior[1]}",
                        )
                    spec_ids[req_id] = (str(path.relative_to(self.root)), lineno)

        csv_path = self.root / "implementation/requirements.csv"
        json_path = self.root / "implementation/requirements.json"
        try:
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        except Exception as exc:  # noqa: BLE001
            self.error("INVALID_REQUIREMENTS_CSV", csv_path, str(exc))
            rows = []
        try:
            json_payload = self.load_json(json_path)
            if isinstance(json_payload, dict):
                json_rows = json_payload.get("requirements", [])
            else:
                json_rows = json_payload
            if not isinstance(json_rows, list):
                raise TypeError("requirements JSON must be an array or an object with a requirements array")
        except Exception as exc:  # noqa: BLE001
            self.error("INVALID_REQUIREMENTS_JSON", json_path, str(exc))
            json_rows = []

        csv_ids = [r.get("requirement_id", "") for r in rows]
        json_ids = [r.get("requirement_id", "") for r in json_rows if isinstance(r, dict)]
        for label, values, path in (
            ("CSV", csv_ids, csv_path),
            ("JSON", json_ids, json_path),
        ):
            duplicates = sorted({value for value in values if value and values.count(value) > 1})
            if duplicates:
                self.error("DUPLICATE_TRACEABILITY_ID", path, f"{label}: {duplicates}")
        if set(csv_ids) != set(spec_ids):
            self.error(
                "REQUIREMENT_CSV_DRIFT",
                csv_path,
                f"missing={sorted(set(spec_ids)-set(csv_ids))}; extra={sorted(set(csv_ids)-set(spec_ids))}",
            )
        if set(json_ids) != set(spec_ids):
            self.error(
                "REQUIREMENT_JSON_DRIFT",
                json_path,
                f"missing={sorted(set(spec_ids)-set(json_ids))}; extra={sorted(set(json_ids)-set(spec_ids))}",
            )
        normalized_json_rows = [
            {key: "" if value is None else str(value) for key, value in row.items()}
            for row in json_rows
            if isinstance(row, dict)
        ]
        if rows != normalized_json_rows:
            self.error("REQUIREMENT_FORMAT_DRIFT", json_path, "JSON and CSV traceability rows are not identical after string normalization")

        valid_levels = {"MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY", "NORMATIVE"}
        for row in rows:
            req_id = row.get("requirement_id", "")
            expected = spec_ids.get(req_id)
            if not expected:
                continue
            if row.get("spec_file") != expected[0] or str(row.get("line")) != str(expected[1]):
                self.error(
                    "REQUIREMENT_LOCATION_DRIFT",
                    csv_path,
                    f"{req_id}: expected {expected[0]}:{expected[1]}, got {row.get('spec_file')}:{row.get('line')}",
                )
            level = row.get("level", "")
            if level not in valid_levels:
                self.error("REQUIREMENT_LANGUAGE", csv_path, f"{req_id} has invalid level {level!r}")
            if not row.get("statement", "").strip():
                self.error("EMPTY_REQUIREMENT", csv_path, f"{req_id} has an empty statement")

    def validate_definitions(self) -> None:
        products = self.validate_directory("products/definitions", "product.schema.json")
        agents = self.validate_directory("agents/definitions", "agent.schema.json")
        commands = self.validate_directory("commands/specs", "command.schema.json")
        tools = self.validate_directory("mcp/tool-specs", "tool-spec.schema.json")
        context_packs = self.validate_directory("context/context-packs", "context-pack.schema.json")
        scenarios = self.validate_directory("qa/scenarios", "qa-scenario.schema.json")
        self.validate_directory("research/sources", "source-record.schema.json")

        # Policies have a separate filename convention.
        policy_schema = self.schemas.get("policy.schema.json")
        policies: dict[str, dict[str, Any]] = {}
        if policy_schema:
            validator = Draft202012Validator(policy_schema)
            for path in sorted((self.root / "security").glob("*.json")):
                data = self.load_json(path)
                for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
                    location = ".".join(str(x) for x in err.path) or "<root>"
                    self.error("SCHEMA_VALIDATION", path, f"{location}: {err.message}")
                artifact_id = data.get("id")
                if artifact_id in policies:
                    self.error("DUPLICATE_ID", path, f"duplicate policy id {artifact_id!r}")
                if artifact_id:
                    policies[artifact_id] = data

        # Cross references.
        for product_id, product in products.items():
            for agent_id in product.get("agent_ids", []):
                if agent_id not in agents:
                    self.error("UNKNOWN_AGENT_REF", f"products/definitions/{product_id}", agent_id)
            for command_id in product.get("command_ids", []):
                if command_id not in commands:
                    self.error("UNKNOWN_COMMAND_REF", f"products/definitions/{product_id}", command_id)
            for tool_id in product.get("tool_ids", []):
                if tool_id not in tools:
                    self.error("UNKNOWN_TOOL_REF", f"products/definitions/{product_id}", tool_id)
            for scenario_id in product.get("known_truth_scenarios", []):
                if scenario_id not in scenarios:
                    self.error("UNKNOWN_SCENARIO_REF", f"products/definitions/{product_id}", scenario_id)
            if not (self.root / "products" / f"{product_id}-{product.get('slug')}.md").exists():
                self.error("MISSING_PRODUCT_SPEC", f"products/definitions/{product_id}", "human product spec is missing")
            for permission in product.get("permissions", []):
                if permission in PROHIBITED_PERMISSION_TOKENS:
                    self.error("PRODUCT_WRITE_PERMISSION", f"products/definitions/{product_id}", permission)
            cp = [x for x in context_packs.values() if x.get("product_id") == product_id]
            if len(cp) != 1:
                self.error("CONTEXT_PACK_CARDINALITY", f"products/definitions/{product_id}", f"expected 1, found {len(cp)}")

        for agent_id, agent in agents.items():
            product_id = agent.get("product_id")
            if product_id and product_id not in products:
                self.error("UNKNOWN_PRODUCT_REF", f"agents/definitions/{agent_id}", product_id)
            for tool_id in agent.get("tool_ids", []):
                if tool_id not in tools:
                    self.error("UNKNOWN_TOOL_REF", f"agents/definitions/{agent_id}", tool_id)
            for permission in agent.get("permissions", []):
                if permission in PROHIBITED_PERMISSION_TOKENS:
                    self.error("AGENT_WRITE_PERMISSION", f"agents/definitions/{agent_id}", permission)
            kind = agent.get("kind")
            human_path = self.root / "agents" / ("core" if kind in {"core", "qa"} else "product") / f"{agent_id}.md"
            if kind in {"core", "qa", "product"} and not human_path.exists():
                self.error("MISSING_AGENT_SPEC", f"agents/definitions/{agent_id}", str(human_path.relative_to(self.root)))

        for command_id, command in commands.items():
            product_id = command.get("product_id")
            if product_id and product_id not in products:
                self.error("UNKNOWN_PRODUCT_REF", f"commands/specs/{command_id}", product_id)
            for agent_id in command.get("agent_ids", []):
                if agent_id not in agents:
                    self.error("UNKNOWN_AGENT_REF", f"commands/specs/{command_id}", agent_id)
            for tool_id in command.get("tool_ids", []):
                if tool_id not in tools:
                    self.error("UNKNOWN_TOOL_REF", f"commands/specs/{command_id}", tool_id)
            output_schema = command.get("output_schema")
            if output_schema and not (self.root / "schemas" / output_schema).exists():
                self.error("UNKNOWN_OUTPUT_SCHEMA", f"commands/specs/{command_id}", output_schema)
            for permission in command.get("permissions", []):
                if permission in PROHIBITED_PERMISSION_TOKENS:
                    self.error("COMMAND_WRITE_PERMISSION", f"commands/specs/{command_id}", permission)

        for tool_id, tool in tools.items():
            if tool.get("read_only") is not True:
                self.error("MUTATING_PRODUCT_TOOL", f"mcp/tool-specs/{tool_id}", "product evidence tools must be read-only")
            if tool.get("unknown_tool_default") not in {"deny", "ask"}:
                self.error("UNSAFE_UNKNOWN_TOOL_DEFAULT", f"mcp/tool-specs/{tool_id}", str(tool.get("unknown_tool_default")))
            if tool.get("max_page_bytes", 0) > 32768:
                self.error("TOOL_PAGE_BUDGET", f"mcp/tool-specs/{tool_id}", "max_page_bytes exceeds 32 KiB default ceiling")

        for pack_id, pack in context_packs.items():
            if pack.get("product_id") not in products:
                self.error("UNKNOWN_PRODUCT_REF", f"context/context-packs/{pack_id}", str(pack.get("product_id")))
            target, hard = pack.get("target_files"), pack.get("hard_files")
            if isinstance(target, int) and isinstance(hard, int) and target > hard:
                self.error("CONTEXT_BUDGET_ORDER", f"context/context-packs/{pack_id}", f"target {target} > hard {hard}")
            if isinstance(hard, int) and hard > 12:
                self.error("CONTEXT_HARD_LIMIT", f"context/context-packs/{pack_id}", f"hard file limit {hard} > 12")
            if pack.get("max_tool_page_bytes", 0) > 32768:
                self.error("CONTEXT_TOOL_PAGE_LIMIT", f"context/context-packs/{pack_id}", "tool page limit exceeds 32 KiB")

        for scenario_id, scenario in scenarios.items():
            if scenario.get("product_id") not in products:
                self.error("UNKNOWN_PRODUCT_REF", f"qa/scenarios/{scenario_id}", str(scenario.get("product_id")))
            finding_ids = [f.get("id") for f in scenario.get("required_findings", [])]
            if len(finding_ids) != len(set(finding_ids)):
                self.error("DUPLICATE_FINDING_ID", f"qa/scenarios/{scenario_id}", str(finding_ids))

        for policy_id, policy in policies.items():
            for tool_id in policy.get("allowed_tools", []):
                if tool_id not in tools:
                    self.error("UNKNOWN_TOOL_REF", f"security/{policy_id}", tool_id)
            if policy_id == "product-read-only" and policy.get("default_decision") != "deny":
                self.error("POLICY_DEFAULT", f"security/{policy_id}", "product policy must default deny")

    def validate_sample_bundle(self) -> None:
        sample_dir = self.root / "examples/sample-run-bundle"
        mapping = {
            "evidence.json": ("evidence.schema.json", True),
            "claims.json": ("claim.schema.json", True),
            "context-manifest.json": ("context-manifest.schema.json", False),
            "handoff.json": ("handoff.schema.json", False),
            "output.json": ("output-envelope.schema.json", False),
        }
        for filename, (schema_name, multiple) in mapping.items():
            path = sample_dir / filename
            if not path.exists():
                self.error("MISSING_SAMPLE_ARTIFACT", path, "sample run bundle is incomplete")
                continue
            data = self.load_json(path)
            schema = self.schemas.get(schema_name)
            if not schema:
                continue
            validator = Draft202012Validator(schema)
            items = data if multiple else [data]
            if multiple and not isinstance(items, list):
                self.error("SAMPLE_SHAPE", path, "expected array")
                continue
            for index, item in enumerate(items):
                for err in sorted(validator.iter_errors(item), key=lambda e: list(e.path)):
                    location = ".".join(str(x) for x in err.path) or "<root>"
                    self.error("SAMPLE_SCHEMA", path, f"item {index}, {location}: {err.message}")

        # Cross-artifact sample evidence integrity.
        try:
            evidence = self.load_json(sample_dir / "evidence.json")
            claims = self.load_json(sample_dir / "claims.json")
            output = self.load_json(sample_dir / "output.json")
        except Exception:
            return
        evidence_ids = {item.get("id") for item in evidence if isinstance(item, dict)}
        claim_ids = {item.get("id") for item in claims if isinstance(item, dict)}
        for claim in claims:
            for evidence_id in claim.get("evidence_ids", []):
                if evidence_id not in evidence_ids:
                    self.error("SAMPLE_MISSING_EVIDENCE", sample_dir / "claims.json", f"{claim.get('id')} -> {evidence_id}")
        for finding in output.get("findings", []):
            for claim_id in finding.get("claim_ids", []):
                if claim_id not in claim_ids:
                    self.error("SAMPLE_MISSING_CLAIM", sample_dir / "output.json", f"{finding.get('id')} -> {claim_id}")

    def validate_markdown_links(self) -> None:
        for path in sorted(self.root.rglob("*.md")):
            # Baseline agent profiles are migration snapshots. Their relative links
            # intentionally point into the source repository rather than this kit.
            if "migration/catalogs/agents" in path.as_posix():
                continue
            text = path.read_text(encoding="utf-8")
            for target in MD_LINK_RE.findall(text):
                target = target.strip()
                if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = target.split("#", 1)[0]
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(self.root)
                except ValueError:
                    self.error("LINK_ESCAPES_PACKAGE", path, target)
                    continue
                if not resolved.exists():
                    self.error("BROKEN_MARKDOWN_LINK", path, target)

    def validate_cleanliness(self) -> None:
        for path in self.root.rglob("*"):
            if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}:
                self.error("GENERATED_CACHE_FILE", path, "Python cache files must not be packaged")
            if path.is_file() and path.name in {".DS_Store", "Thumbs.db"}:
                self.error("OS_JUNK_FILE", path, "OS-generated file must not be packaged")

    def run(self) -> list[Problem]:
        self.require_paths()
        self.load_and_validate_schemas()
        self.validate_all_json()
        self.validate_requirements()
        self.validate_definitions()
        self.validate_sample_bundle()
        self.validate_markdown_links()
        self.validate_cleanliness()
        return sorted(self.problems, key=lambda p: (p.code, p.path, p.message))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(args.root)
    validator = PackageValidator(root)
    problems = validator.run()
    if args.as_json:
        print(json.dumps({
            "root": str(root.resolve()),
            "status": "pass" if not problems else "fail",
            "problem_count": len(problems),
            "problems": [p.__dict__ for p in problems],
        }, indent=2, sort_keys=True))
    else:
        if problems:
            print(f"FAIL: {len(problems)} problem(s)")
            for problem in problems:
                print(problem.render())
        else:
            print("PASS: specification package is internally consistent")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
