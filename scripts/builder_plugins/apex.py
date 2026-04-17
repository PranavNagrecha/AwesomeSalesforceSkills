"""ApexBuilderPlugin — extracted from the original apex-builder pipeline.

Owns everything Apex-specific: class inventory (by kind), grounding symbol
list, Apex-flavoured requirements template variables, static parse, and
live `sf project deploy validate` against a real org.
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


APEX_CLASS_RE = re.compile(
    r"(?:public|global|private)\s+(?:with\s+sharing\s+|without\s+sharing\s+|inherited\s+sharing\s+)?"
    r"(?:abstract\s+|virtual\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)"
)
APEX_TRIGGER_RE = re.compile(
    r"^\s*trigger\s+([A-Za-z_][A-Za-z0-9_]*)\s+on\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]+)\)",
    re.MULTILINE,
)

CLS_META_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{api}</apiVersion>
    <status>Active</status>
</ApexClass>
"""

TRIGGER_META_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{api}</apiVersion>
    <status>Active</status>
</ApexTrigger>
"""

SFDX_PROJECT_JSON = """{
  "packageDirectories": [{"path": "force-app", "default": true}],
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "{api}"
}
"""


def _bullets(items: list[str], indent: str = "  ") -> str:
    if not items:
        return f"{indent}- _(none)_"
    return "\n".join(f"{indent}- {i}" for i in items)


def _strip_strings_and_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"'(?:\\.|[^'\\])*'", "''", src)
    return src


class ApexBuilderPlugin:
    agent = "apex-builder"

    # --- Gate A extras -----------------------------------------------------
    def additional_input_checks(self, inputs: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        invalid: list[str] = []
        sobject_kinds = {"trigger", "selector", "domain", "batch", "cdc_subscriber"}
        if inputs.get("kind") in sobject_kinds and not inputs.get("primary_sobject"):
            missing.append("primary_sobject (required because kind implies an SObject target)")
        sobject_named = {"trigger", "selector", "domain", "cdc_subscriber"}
        if inputs.get("kind") not in sobject_named and not inputs.get("feature_token"):
            missing.append("feature_token (required PascalCase stem for class names)")
        ft = inputs.get("feature_token")
        if ft and not re.match(r"^[A-Z][A-Za-z0-9]+$", ft):
            invalid.append(f"feature_token: '{ft}' must match ^[A-Z][A-Za-z0-9]+$")
        if inputs.get("sharing_mode") == "without_sharing":
            bj = inputs.get("business_justification") or ""
            if len(bj) < 40:
                invalid.append("business_justification: required ≥40 chars when sharing_mode=without_sharing")
        return missing, invalid

    # --- grounding (Gate B) -----------------------------------------------
    def grounding_sobjects(self, inputs: dict[str, Any]) -> list[str]:
        sobj = inputs.get("primary_sobject")
        return [sobj] if sobj else []

    def expected_resources(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        out = [
            {"type": "template", "path": "templates/apex/BaseService.cls"},
            {"type": "template", "path": "templates/apex/SecurityUtils.cls"},
        ]
        if inputs.get("include_logger", True):
            out.append({"type": "template", "path": "templates/apex/ApplicationLogger.cls"})
        return out

    def expected_citations(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        kind = inputs.get("kind", "")
        if kind in ("queueable", "batch", "schedulable", "platform_event_subscriber", "cdc_subscriber", "continuation"):
            out += [
                {"type": "skill", "id": "apex/async-apex"},
                {"type": "decision_tree", "id": "async-selection.md"},
            ]
        kind_to_skill = {
            "queueable": "apex/apex-queueable-patterns",
            "batch": "apex/batch-apex-patterns",
            "schedulable": "apex/apex-scheduled-jobs",
            "rest": "apex/apex-rest-services",
            "invocable": "apex/invocable-methods",
            "platform_event_subscriber": "apex/platform-events-apex",
            "cdc_subscriber": "apex/change-data-capture-apex",
            "trigger": "apex/trigger-framework",
        }
        if kind in kind_to_skill:
            out.append({"type": "skill", "id": kind_to_skill[kind]})
        return out

    # --- deliverables ------------------------------------------------------
    def class_inventory(self, inputs: dict[str, Any]) -> list[str]:
        kind = inputs.get("kind")
        sobj = inputs.get("primary_sobject") or "Feature"
        token = inputs.get("feature_token") or sobj
        mapping = {
            "trigger":   [f"{sobj}Trigger.trigger", f"{sobj}TriggerHandler", f"{sobj}Service", f"{sobj}Selector", f"{sobj}Domain", f"{sobj}TriggerHandlerTest"],
            "service":   [f"{token}Service", f"{token}ServiceTest"],
            "selector":  [f"{sobj}Selector", f"{sobj}SelectorTest"],
            "domain":    [f"{sobj}Domain", f"{sobj}DomainTest"],
            "batch":     [f"{token}Batch", f"{token}BatchSchedule", f"{token}BatchTest"],
            "queueable": [f"{token}Queueable", f"{token}QueueableTest"],
            "schedulable": [f"{token}Schedulable", f"{token}SchedulableTest"],
            "invocable": [f"{token}InvocableActions", f"{token}InvocableActionsTest"],
            "rest":      [f"{token}RestResource", f"{token}RestResourceTest"],
            "soap":      [f"{token}SoapService", f"{token}SoapServiceTest"],
            "platform_event_subscriber": [f"{token}EventSubscriber", f"{token}EventSubscriberTest"],
            "cdc_subscriber": [f"{sobj}ChangeEventTriggerHandler", f"{sobj}ChangeEventTrigger.trigger", f"{sobj}ChangeEventHandlerTest"],
            "continuation": [f"{token}ContinuationController", f"{token}ContinuationControllerTest"],
            "iterator":  [f"{token}Iterator", f"{token}IteratorTest"],
            "controller": [f"{token}Controller", f"{token}ControllerTest"],
            "test_only": [f"{token}Test"],
        }
        return mapping.get(kind, [f"{token}{kind.title() if kind else 'Class'}"])

    def expected_deliverable_stems(self, inputs: dict[str, Any]) -> set[str]:
        return set(c for c in self.class_inventory(inputs) if not c.endswith(".trigger"))

    # --- grounding ---------------------------------------------------------
    def grounding_symbols(self, inputs: dict[str, Any]) -> list[str]:
        syms: list[str] = []
        if inputs.get("primary_sobject"):
            syms.append(f"SObject: `{inputs['primary_sobject']}`")
        for f in inputs.get("referenced_fields") or []:
            syms.append(f"Field: `{f}`")
        for c in self.class_inventory(inputs):
            if not c.endswith("Test") and not c.endswith(".trigger"):
                syms.append(f"Apex class declaration: `{c}` (must NOT already exist under repo_path)")
        syms.append("Template: `templates/apex/BaseService.cls`")
        syms.append("Template: `templates/apex/SecurityUtils.cls`")
        if inputs.get("include_logger", True):
            syms.append("Template: `templates/apex/ApplicationLogger.cls`")
        return syms

    # --- requirements template vars ----------------------------------------
    def requirements_template_vars(
        self,
        inputs: dict[str, Any],
        run_id: str,
        inputs_sha256: str,
        agent_version: str = "1.0.0",
    ) -> dict[str, str]:
        classes = self.class_inventory(inputs)
        budget = self._governor_budget(inputs)
        return {
            "{{feature_summary_short}}": (inputs.get("feature_summary") or "").strip()[:80],
            "{{run_id}}": run_id,
            "{{generated_at}}": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "{{agent_version}}": agent_version,
            "{{inputs_sha256}}": inputs_sha256,
            "{{feature_summary}}": inputs.get("feature_summary", "_(unspecified)_"),
            "{{kind}}": inputs.get("kind", "_(unspecified)_"),
            "{{primary_sobject_or_na}}": inputs.get("primary_sobject") or "_(n/a)_",
            "{{class_inventory_bullets}}": _bullets([f"`{c}`" for c in classes]),
            "{{trigger_or_none}}": self._trigger_or_none(classes),
            "{{test_class_name}}": self._test_class_name(classes),
            "{{api_version}}": inputs.get("api_version", "60.0"),
            "{{namespace_or_none}}": inputs.get("namespace") or "_(none)_",
            "{{sharing_mode}}": inputs.get("sharing_mode", "with_sharing"),
            "{{include_logger}}": "yes" if inputs.get("include_logger", True) else "no",
            "{{async_hint_or_na}}": inputs.get("async_hint") or "_(n/a)_",
            "{{test_bulk_size}}": str(inputs.get("test_bulk_size", 200)),
            "{{repo_path}}": inputs.get("repo_path", "./force-app"),
            "{{target_org_alias_or_library_only}}": inputs.get("target_org_alias") or "_(library-only mode)_",
            "{{sharing_mode_prose}}": self._sharing_mode_prose(inputs),
            "{{soql_budget}}": budget["soql"],
            "{{dml_budget}}": budget["dml"],
            "{{heap_budget}}": budget["heap"],
            "{{cpu_budget}}": budget["cpu"],
            "{{uncovered_branches_bullets}}": _bullets(["_(generator fills during Gate C)_"]),
            "{{grounding_symbols_bullets}}": _bullets(self.grounding_symbols(inputs)),
        }

    # --- Gate C ------------------------------------------------------------
    def discover_emitted_files(self, emitted_dir: Path) -> list[Path]:
        if not emitted_dir.exists():
            return []
        out: list[Path] = []
        for ext in ("*.cls", "*.trigger"):
            out.extend(emitted_dir.rglob(ext))
        return sorted(out)

    def static_check(self, files: list[Path]) -> list[str]:
        errors: list[str] = []
        for f in files:
            src = f.read_text(encoding="utf-8", errors="replace")
            errors.extend(self._static_parse_apex(src, f.name))
        return errors

    def live_check(
        self,
        files: list[Path],
        target_org: str,
        api_version: str,
        timeout_sec: int = 300,
    ) -> LiveCheckResult:
        res = LiveCheckResult(oracle_label="sf project deploy validate")
        if not shutil.which("sf"):
            res.errors.append({"file": None, "line": None, "column": None, "problem": "sf CLI not on PATH", "problem_type": "MissingCLI"})
            return res

        with tempfile.TemporaryDirectory(prefix="run_builder_apex_") as tmp_s:
            tmp = Path(tmp_s)
            classes_dir = tmp / "force-app" / "main" / "default" / "classes"
            triggers_dir = tmp / "force-app" / "main" / "default" / "triggers"
            classes_dir.mkdir(parents=True)
            triggers_dir.mkdir(parents=True)
            (tmp / "sfdx-project.json").write_text(SFDX_PROJECT_JSON.replace("{api}", api_version), encoding="utf-8")

            for f in files:
                if f.suffix == ".cls":
                    target = classes_dir / f.name
                    target.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
                    meta = classes_dir / (f.name + "-meta.xml")
                    if not meta.exists():
                        meta.write_text(CLS_META_XML.replace("{api}", api_version), encoding="utf-8")
                elif f.suffix == ".trigger":
                    target = triggers_dir / f.name
                    target.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
                    meta = triggers_dir / (f.name + "-meta.xml")
                    if not meta.exists():
                        meta.write_text(TRIGGER_META_XML.replace("{api}", api_version), encoding="utf-8")

            cmd = [
                "sf", "project", "deploy", "validate",
                "--target-org", target_org,
                "--source-dir", str(tmp / "force-app"),
                "--json",
                "--wait", "10",
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    cwd=str(tmp),
                )
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

            # Top-level CLI error (bad flag, auth failure) — no result block.
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
        # Apex demands deploy-validate + ≥75% coverage as the bar.
        return {"floor": 75, "high_tier": 85}

    # --- private helpers ---------------------------------------------------
    def _test_class_name(self, classes: list[str]) -> str:
        for c in classes:
            if c.endswith("Test"):
                return c
        return classes[-1] + "Test"

    def _trigger_or_none(self, classes: list[str]) -> str:
        for c in classes:
            if c.endswith(".trigger"):
                return c
        return "_(none)_"

    def _sharing_mode_prose(self, inputs: dict[str, Any]) -> str:
        mode = inputs.get("sharing_mode", "with_sharing")
        if mode == "with_sharing":
            return "Emitted classes use `with sharing`. Record-level security is enforced by the platform for every SOQL/DML path."
        if mode == "inherited_sharing":
            return "Emitted classes use `inherited sharing`. Sharing behavior is inherited from the caller context; every entry point must be reviewed for whether it is `with sharing` safe."
        bj = inputs.get("business_justification", "").strip()
        return (
            f"Emitted classes use `without sharing` per explicit business justification:\n\n"
            f"> {bj}\n\n"
            "This justification is copied verbatim into a header comment on every emitted class."
        )

    def _governor_budget(self, inputs: dict[str, Any]) -> dict[str, str]:
        kind = inputs.get("kind", "")
        bulk = int(inputs.get("test_bulk_size") or 200)
        if kind in ("batch",):
            return {"soql": "100 per execute()", "dml": "150 per execute()", "heap": "12", "cpu": "60000"}
        if kind in ("queueable", "schedulable", "platform_event_subscriber", "cdc_subscriber"):
            return {"soql": "100 per job", "dml": "150 per job", "heap": "6", "cpu": "60000"}
        if kind == "trigger":
            return {"soql": "20 per transaction", "dml": "20 per transaction", "heap": "6", "cpu": "10000"}
        if kind in ("rest", "soap", "controller", "invocable", "continuation"):
            return {"soql": "10 per invocation", "dml": "10 per invocation", "heap": "6", "cpu": "10000"}
        return {"soql": str(min(100, bulk // 4)), "dml": "≤ 10", "heap": "6", "cpu": "10000"}

    def _static_parse_apex(self, source: str, filename: str) -> list[str]:
        errors: list[str] = []
        cleaned = _strip_strings_and_comments(source)
        if cleaned.count("{") != cleaned.count("}"):
            errors.append(f"{filename}: unbalanced braces ({cleaned.count('{')} open, {cleaned.count('}')} close)")
        if cleaned.count("(") != cleaned.count(")"):
            errors.append(f"{filename}: unbalanced parens ({cleaned.count('(')} open, {cleaned.count(')')} close)")

        is_trigger = filename.endswith(".trigger") or ".trigger" in filename
        if is_trigger:
            if not APEX_TRIGGER_RE.search(cleaned):
                errors.append(f"{filename}: no `trigger X on SObject (...)` declaration found")
        else:
            if not APEX_CLASS_RE.search(cleaned):
                errors.append(f"{filename}: no class declaration found")

        if filename.lower().endswith("test.cls"):
            if "@isTest" not in source and "@IsTest" not in source:
                errors.append(f"{filename}: test class missing @IsTest annotation")
            if "Test.startTest" not in source and "Test.stopTest" not in source and "testMethod" not in source:
                if "@IsTest" not in source and "@isTest" not in source:
                    errors.append(f"{filename}: test class has no @IsTest methods")

        for bad in ("public voide ", "publik class ", "privte class ", "triger ", "insted of"):
            if bad in source:
                errors.append(f"{filename}: likely typo `{bad.strip()}`")

        return errors
