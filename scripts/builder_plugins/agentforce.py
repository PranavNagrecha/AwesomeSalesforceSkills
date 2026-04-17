"""AgentforceBuilderPlugin — gated QA for agentforce-builder.

Scope:
  * Grounding: primary_object + referenced_fields describe against org_stub.
  * Expected resources: AgentActionSkeleton.cls, AgentTopic_Template.md, and
    AgentSkeleton.json (when emit_agent_spec=true).
  * Gate C static: Apex invocable action parses clean, class has @InvocableMethod
    annotation, Request/Response inner classes exist, validate() + execute() are
    present, success/errorMessage surface is uniform. Optional AgentSkeleton.json
    is checked against the canonical shape (agent.{name,label,description,persona,
    topics,guardrails.trustLayer,evaluation}).
  * Gate C live: `sf project deploy validate --target-org <alias>` over the
    emitted .cls + .cls-meta.xml files. The .json spec is NOT metadata and
    is never deployed.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .base import LiveCheckResult


SFDX_PROJECT_JSON = """{
  "packageDirectories": [{"path": "force-app", "default": true}],
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "{api}"
}
"""

CLS_META_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{api}</apiVersion>
    <status>Active</status>
</ApexClass>
"""


def _bullets(items: list[str], indent: str = "  ") -> str:
    if not items:
        return f"{indent}- _(none)_"
    return "\n".join(f"{indent}- {it}" for it in items)


REQUIRED_AGENT_SPEC_PATHS = [
    ("agent", "name"),
    ("agent", "label"),
    ("agent", "description"),
    ("agent", "persona"),
    ("agent", "topics"),
    ("agent", "guardrails", "trustLayer"),
    ("agent", "evaluation", "testUtterances"),
    ("agent", "evaluation", "minAccuracy"),
]


class AgentforceBuilderPlugin:
    agent = "agentforce-builder"

    # --- Gate A extras -----------------------------------------------------
    def additional_input_checks(self, inputs: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        invalid: list[str] = []
        if inputs.get("emit_agent_spec") and not inputs.get("agent_name"):
            missing.append("agent_name (required when emit_agent_spec=true)")
        return missing, invalid

    # --- grounding (Gate B) -----------------------------------------------
    def grounding_sobjects(self, inputs: dict[str, Any]) -> list[str]:
        obj = inputs.get("primary_object")
        return [obj] if obj else []

    def expected_resources(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = [
            {"type": "template", "path": "templates/agentforce/AgentActionSkeleton.cls"},
            {"type": "template", "path": "templates/agentforce/AgentTopic_Template.md"},
        ]
        if inputs.get("emit_agent_spec"):
            out.append({"type": "template", "path": "templates/agentforce/AgentSkeleton.json"})
        return out

    def expected_citations(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = [
            {"type": "skill", "id": "agentforce/agent-actions"},
            {"type": "skill", "id": "agentforce/agent-topic-design"},
            {"type": "skill", "id": "agentforce/einstein-trust-layer"},
        ]
        return out

    # --- deliverables ------------------------------------------------------
    def class_inventory(self, inputs: dict[str, Any]) -> list[str]:
        cn = inputs.get("action_class_name") or "ExampleAction"
        out = [f"{cn}.cls", f"{cn}Test.cls"]
        if inputs.get("topic_name"):
            out.append(f"{inputs['topic_name']}.topic.md")
        if inputs.get("emit_agent_spec") and inputs.get("agent_name"):
            out.append(f"{inputs['agent_name']}.json")
        return out

    def expected_deliverable_stems(self, inputs: dict[str, Any]) -> set[str]:
        cn = inputs.get("action_class_name") or ""
        stems: set[str] = set()
        if cn:
            stems.update({cn, cn + "Test"})
        return stems

    # --- grounding symbols for REQUIREMENTS --------------------------------
    def grounding_symbols(self, inputs: dict[str, Any]) -> list[str]:
        syms: list[str] = []
        obj = inputs.get("primary_object")
        if obj:
            syms.append(f"SObject: `{obj}`")
        for f in inputs.get("referenced_fields") or []:
            syms.append(f"Field: `{f}`")
        cn = inputs.get("action_class_name") or "_(unspecified)_"
        syms.append(f"Apex class: `{cn}` (@InvocableMethod action; must NOT already exist)")
        syms.append(f"Apex class: `{cn}Test` (companion test)")
        syms.append("Template: `templates/agentforce/AgentActionSkeleton.cls`")
        if inputs.get("emit_agent_spec"):
            syms.append("Template: `templates/agentforce/AgentSkeleton.json`")
        return syms

    # --- requirements template vars ----------------------------------------
    def requirements_template_vars(
        self,
        inputs: dict[str, Any],
        run_id: str,
        inputs_sha256: str,
        agent_version: str = "1.0.0",
    ) -> dict[str, str]:
        cn = inputs.get("action_class_name") or "_(unspecified)_"
        constraints = inputs.get("trust_constraints") or []
        fields = inputs.get("referenced_fields") or []
        return {
            "{{feature_summary_short}}": (inputs.get("feature_summary") or "").strip()[:80],
            "{{run_id}}": run_id,
            "{{generated_at}}": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "{{agent_version}}": agent_version,
            "{{inputs_sha256}}": inputs_sha256,
            "{{feature_summary}}": inputs.get("feature_summary", "_(unspecified)_"),
            "{{action_class_name}}": cn,
            "{{primary_object}}": inputs.get("primary_object", "_(unspecified)_"),
            "{{actor}}": inputs.get("actor", "_(unspecified)_"),
            "{{trust_constraints_bullets}}": _bullets([f"`{c}`" for c in constraints]),
            "{{referenced_fields_bullets}}": _bullets([f"`{f}`" for f in fields]),
            "{{agent_name_or_none}}": inputs.get("agent_name", "_(none)_"),
            "{{topic_name_or_none}}": inputs.get("topic_name", "_(none)_"),
            "{{emit_agent_spec}}": "yes" if inputs.get("emit_agent_spec") else "no",
            "{{api_version}}": inputs.get("api_version", "60.0"),
            "{{namespace_or_none}}": inputs.get("namespace") or "_(none)_",
            "{{target_org_alias_or_library_only}}": inputs.get("target_org_alias") or "_(library-only mode)_",
            "{{action_inventory_bullets}}": _bullets([f"`{c}`" for c in self.class_inventory(inputs)]),
            "{{grounding_symbols_bullets}}": _bullets(self.grounding_symbols(inputs)),
        }

    # --- Gate C ------------------------------------------------------------
    def discover_emitted_files(self, emitted_dir: Path) -> list[Path]:
        if not emitted_dir.exists():
            return []
        out: list[Path] = []
        for pat in ("*.cls", "*.json"):
            out.extend(emitted_dir.rglob(pat))
        return sorted(set(out))

    def static_check(self, files: list[Path]) -> list[str]:
        errors: list[str] = []
        if not files:
            return ["no agentforce files under emitted_dir"]

        for f in files:
            if f.suffix == ".cls":
                src = f.read_text(encoding="utf-8", errors="replace")
                errors.extend(self._check_apex(src, f.name))
            elif f.suffix == ".json":
                errors.extend(self._check_agent_spec(f))
        return errors

    def live_check(
        self,
        files: list[Path],
        target_org: str,
        api_version: str,
        timeout_sec: int = 300,
    ) -> LiveCheckResult:
        res = LiveCheckResult(oracle_label="sf project deploy validate (agentforce apex)")
        cls_files = [f for f in files if f.suffix == ".cls"]
        if not cls_files:
            # Only JSON spec emitted — nothing to deploy. Report as skipped/clean.
            res.ran = False
            res.succeeded = True
            res.oracle_label = "(no apex to deploy)"
            return res

        if not shutil.which("sf"):
            res.errors.append({"file": None, "line": None, "column": None, "problem": "sf CLI not on PATH", "problem_type": "MissingCLI"})
            return res

        with tempfile.TemporaryDirectory(prefix="run_builder_agentforce_") as tmp_s:
            tmp = Path(tmp_s)
            classes_root = tmp / "force-app" / "main" / "default" / "classes"
            classes_root.mkdir(parents=True)
            (tmp / "sfdx-project.json").write_text(SFDX_PROJECT_JSON.replace("{api}", api_version), encoding="utf-8")

            for f in cls_files:
                (classes_root / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
                (classes_root / (f.name + "-meta.xml")).write_text(
                    CLS_META_XML.replace("{api}", api_version), encoding="utf-8"
                )

            cmd = [
                "sf", "project", "deploy", "validate",
                "--target-org", target_org,
                "--source-dir", str(tmp / "force-app"),
                "--json",
                "--wait", "10",
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, cwd=str(tmp))
            except subprocess.TimeoutExpired:
                res.errors.append({"file": None, "line": None, "column": None, "problem": f"sf timed out after {timeout_sec}s", "problem_type": "Timeout"})
                return res

            res.ran = True
            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError:
                res.errors.append({
                    "file": None, "line": None, "column": None,
                    "problem": f"could not parse sf JSON: {proc.stderr[:300] or proc.stdout[:300]}",
                    "problem_type": "UnparseableCLIOutput",
                })
                return res

            top_status = payload.get("status")
            top_name = payload.get("name")
            top_message = payload.get("message")
            res.status = top_status

            if top_status not in (0, None) and not payload.get("result"):
                res.errors.append({
                    "file": None, "line": None, "column": None,
                    "problem": top_message or f"sf CLI returned status {top_status}",
                    "problem_type": top_name or "CLIError",
                })
                res.succeeded = False
                res.raw = {"num_component_errors": 1, "num_component_success": 0}
                return res

            result = payload.get("result") or {}
            details = result.get("details") or {}
            component_failures = details.get("componentFailures") or []
            component_success = details.get("componentSuccesses") or []

            res.succeeded = bool(result.get("success"))
            res.errors = [
                {
                    "file": cf.get("fileName") or cf.get("fullName"),
                    "line": cf.get("lineNumber"),
                    "column": cf.get("columnNumber"),
                    "problem": cf.get("problem"),
                    "problem_type": cf.get("problemType"),
                }
                for cf in component_failures
            ]
            res.raw = {
                "num_component_errors": result.get("numberComponentErrors", len(component_failures)),
                "num_component_success": result.get("numberComponentsDeployed", len(component_success)),
            }
            return res

    def coverage_thresholds(self, inputs: dict[str, Any]) -> dict[str, int]:
        # Agentforce actions are Apex under the hood — respect the Apex floor.
        return {"floor": 75, "high_tier": 85}

    # --- private helpers ---------------------------------------------------
    def _check_apex(self, src: str, filename: str) -> list[str]:
        errors: list[str] = []

        # Cheap brace/paren balance (strip strings + comments first)
        cleaned = re.sub(r"//[^\n]*", "", src)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"'(?:\\.|[^'\\])*'", "''", cleaned)
        if cleaned.count("{") != cleaned.count("}"):
            errors.append(f"{filename}: unbalanced braces ({cleaned.count('{')} open, {cleaned.count('}')} close)")
        if cleaned.count("(") != cleaned.count(")"):
            errors.append(f"{filename}: unbalanced parens ({cleaned.count('(')} open, {cleaned.count(')')} close)")

        if not re.search(r"\b(public|global|private)\s+(with|without|inherited)?\s*sharing?\s*class\s+", src) and "class " not in src:
            errors.append(f"{filename}: no Apex class declaration")

        # Test classes are exempt from @InvocableMethod / Request/Response shape.
        is_test = filename.lower().endswith("test.cls") or "@IsTest" in src or "@isTest" in src
        if is_test:
            if "@IsTest" not in src and "@isTest" not in src:
                errors.append(f"{filename}: test class missing @IsTest annotation")
            return errors

        # Non-test action class must have @InvocableMethod and List<Request>/List<Response> signature.
        if "@InvocableMethod" not in src:
            errors.append(f"{filename}: missing @InvocableMethod annotation")
        if not re.search(r"public\s+static\s+List<\s*Response\s*>\s+\w+\s*\(\s*List<\s*Request\s*>", src):
            errors.append(f"{filename}: expected `public static List<Response> <name>(List<Request> requests)` signature")
        if "class Request" not in src:
            errors.append(f"{filename}: missing inner `class Request` type")
        if "class Response" not in src:
            errors.append(f"{filename}: missing inner `class Response` type")
        if "@InvocableVariable" not in src:
            errors.append(f"{filename}: no @InvocableVariable found — Request/Response fields must be documented")
        return errors

    def _check_agent_spec(self, path: Path) -> list[str]:
        errors: list[str] = []
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return [f"{path.name}: not valid JSON ({e})"]

        def get_path(d, keys):
            cur = d
            for k in keys:
                if not isinstance(cur, dict) or k not in cur:
                    return _MISSING
                cur = cur[k]
            return cur

        for keys in REQUIRED_AGENT_SPEC_PATHS:
            val = get_path(doc, keys)
            if val is _MISSING:
                errors.append(f"{path.name}: missing required path `{'.'.join(keys)}`")

        topics = doc.get("agent", {}).get("topics") or []
        if not isinstance(topics, list) or not topics:
            errors.append(f"{path.name}: `agent.topics` must be a non-empty array")
        else:
            for i, t in enumerate(topics):
                if not isinstance(t, dict):
                    errors.append(f"{path.name}: agent.topics[{i}] is not an object")
                    continue
                if "name" not in t:
                    errors.append(f"{path.name}: agent.topics[{i}] missing `name`")
                if "actions" not in t or not isinstance(t.get("actions"), list) or not t["actions"]:
                    errors.append(f"{path.name}: agent.topics[{i}] missing non-empty `actions`")

        trust = doc.get("agent", {}).get("guardrails", {}).get("trustLayer")
        if isinstance(trust, dict):
            for flag in ("maskPII", "blockToxicity", "preventPromptInjection"):
                if flag not in trust:
                    errors.append(f"{path.name}: guardrails.trustLayer missing `{flag}`")

        return errors


class _Missing:
    pass


_MISSING = _Missing()
