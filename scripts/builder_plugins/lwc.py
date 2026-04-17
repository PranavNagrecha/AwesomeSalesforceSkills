"""LwcBuilderPlugin — gated QA for lwc-builder.

Scope:
  * Grounding: target_objects + referenced_fields describe against org_stub.
  * Expected resources: LWC component skeleton, jest config, patterns dir,
    and the Apex base helpers when emitting a controller.
  * Gate C static: bundle coherence checks (.js has `extends LightningElement`,
    .html has a `<template>`, .js-meta.xml is valid XML with
    `<LightningComponentBundle>`, no raw `alert()` / `document.`, component
    name in file names matches `component_name`).
  * Gate C live: `sf project deploy validate --target-org <alias>` against a
    real org. The scratch compiler enforces imports (@salesforce/apex/*),
    wire adapters, @api typing, and rejects missing Apex controllers.
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
from xml.etree import ElementTree as ET

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


# binding_kind → (target tags, notes). Mirrors AGENT.md §Step 6.
BINDING_TARGETS: dict[str, list[str]] = {
    "record-page": ["lightning__RecordPage"],
    "flow-screen": ["lightning__FlowScreen"],
    "app-page": ["lightning__AppPage"],
    "experience-cloud": ["lightningCommunity__Page", "lightningCommunity__Default"],
    "utility-bar": ["lightning__UtilityBar"],
    "home-page": ["lightning__HomePage"],
    "standalone": [],
}


class LwcBuilderPlugin:
    agent = "lwc-builder"

    # --- Gate A extras -----------------------------------------------------
    def additional_input_checks(self, inputs: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        invalid: list[str] = []
        if inputs.get("emit_controller"):
            # When a controller is emitted, Gate A.5 will render methods into
            # REQUIREMENTS and Gate C expects the methods to exist. Force the
            # caller to be explicit.
            methods = inputs.get("controller_methods") or []
            if not methods:
                missing.append("controller_methods (emit_controller=true implies ≥1 method)")
        binding = inputs.get("binding_kind")
        if binding == "record-page":
            pub = inputs.get("public_api") or []
            if isinstance(pub, str):
                pub = [s.strip() for s in pub.split(",") if s.strip()]
            if "recordId" not in pub:
                invalid.append("public_api: record-page binding requires `recordId` @api property")
        return missing, invalid

    # --- grounding (Gate B) -----------------------------------------------
    def grounding_sobjects(self, inputs: dict[str, Any]) -> list[str]:
        # target_objects comes in as either a list or a comma-separated string
        raw = inputs.get("target_objects") or []
        if isinstance(raw, str):
            raw = [s.strip() for s in raw.split(",") if s.strip()]
        return list(raw)

    def expected_resources(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = [
            {"type": "template", "path": "templates/lwc/component-skeleton"},
            {"type": "template", "path": "templates/lwc/jest.config.js"},
            {"type": "template", "path": "templates/lwc/patterns"},
        ]
        if inputs.get("emit_controller"):
            out += [
                {"type": "template", "path": "templates/apex/BaseService.cls"},
                {"type": "template", "path": "templates/apex/SecurityUtils.cls"},
            ]
        return out

    def expected_citations(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = [
            {"type": "skill", "id": "lwc/lwc-testing"},
        ]
        data_shape = inputs.get("data_shape", "")
        if data_shape == "record-form":
            out.append({"type": "skill", "id": "lwc/lwc-forms-and-validation"})
            out.append({"type": "skill", "id": "lwc/wire-service-patterns"})
        if data_shape in ("list-view", "search"):
            out.append({"type": "skill", "id": "lwc/wire-service-patterns"})
        if inputs.get("emit_controller"):
            out.append({"type": "skill", "id": "lwc/lwc-imperative-apex"})
        # Accessibility is always in-scope for lwc-builder.
        out.append({"type": "skill", "id": "lwc/lwc-accessibility-patterns"})
        return out

    # --- deliverables ------------------------------------------------------
    def class_inventory(self, inputs: dict[str, Any]) -> list[str]:
        cn = inputs.get("component_name") or "componentSkeleton"
        out = [
            f"{cn}/{cn}.js",
            f"{cn}/{cn}.html",
            f"{cn}/{cn}.css",
            f"{cn}/{cn}.js-meta.xml",
            f"{cn}/__tests__/{cn}.test.js",
        ]
        if inputs.get("emit_controller"):
            ctrl = inputs.get("controller_class_name") or f"{cn[0].upper() + cn[1:]}Controller"
            out += [ctrl + ".cls", ctrl + "Test.cls"]
        return out

    def expected_deliverable_stems(self, inputs: dict[str, Any]) -> set[str]:
        # Gate C's stem-vs-.cls check only sees Apex classes. Bundle coherence
        # (.js/.html/.meta triple) is enforced by static_check, so we return
        # only Apex controller stems here — empty when emit_controller=false.
        stems: set[str] = set()
        if inputs.get("emit_controller"):
            cn = inputs.get("component_name") or ""
            ctrl = inputs.get("controller_class_name") or (
                f"{cn[0].upper() + cn[1:]}Controller" if cn else "Controller"
            )
            stems.update({ctrl, ctrl + "Test"})
        return stems

    # --- grounding symbols for REQUIREMENTS --------------------------------
    def grounding_symbols(self, inputs: dict[str, Any]) -> list[str]:
        syms: list[str] = []
        for obj in self.grounding_sobjects(inputs):
            syms.append(f"SObject: `{obj}`")
        for f in inputs.get("referenced_fields") or []:
            syms.append(f"Field: `{f}`")
        cn = inputs.get("component_name") or "_(unspecified)_"
        syms.append(f"LWC bundle: `lwc/{cn}/` (must NOT already exist under repo_path)")
        if inputs.get("emit_controller"):
            ctrl = inputs.get("controller_class_name") or f"{cn[0].upper() + cn[1:]}Controller"
            syms.append(f"Apex class: `{ctrl}` (@AuraEnabled controller; must NOT already exist)")
        syms.append("Template: `templates/lwc/component-skeleton/`")
        syms.append("Template: `templates/lwc/jest.config.js`")
        if inputs.get("emit_controller"):
            syms.append("Template: `templates/apex/BaseService.cls`")
            syms.append("Template: `templates/apex/SecurityUtils.cls`")
        return syms

    # --- requirements template vars ----------------------------------------
    def requirements_template_vars(
        self,
        inputs: dict[str, Any],
        run_id: str,
        inputs_sha256: str,
        agent_version: str = "1.0.0",
    ) -> dict[str, str]:
        cn = inputs.get("component_name") or "_(unspecified)_"
        targets = BINDING_TARGETS.get(inputs.get("binding_kind", ""), [])
        ctrl_name = ""
        if inputs.get("emit_controller"):
            ctrl_name = inputs.get("controller_class_name") or (
                f"{cn[0].upper() + cn[1:]}Controller" if cn and cn != "_(unspecified)_" else "Controller"
            )
        target_objects = self.grounding_sobjects(inputs)
        public_api = inputs.get("public_api") or []
        if isinstance(public_api, str):
            public_api = [s.strip() for s in public_api.split(",") if s.strip()]

        return {
            "{{feature_summary_short}}": (inputs.get("feature_summary") or "").strip()[:80],
            "{{run_id}}": run_id,
            "{{generated_at}}": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "{{agent_version}}": agent_version,
            "{{inputs_sha256}}": inputs_sha256,
            "{{feature_summary}}": inputs.get("feature_summary", "_(unspecified)_"),
            "{{component_name}}": cn,
            "{{binding_kind}}": inputs.get("binding_kind", "_(unspecified)_"),
            "{{data_shape}}": inputs.get("data_shape", "_(unspecified)_"),
            "{{targets_bullets}}": _bullets([f"`{t}`" for t in targets]) if targets else f"  - _(standalone — no targets)_",
            "{{target_objects_bullets}}": _bullets([f"`{o}`" for o in target_objects]) if target_objects else "  - _(n/a — no-data shape)_",
            "{{public_api_bullets}}": _bullets([f"`@api {p}`" for p in public_api]) if public_api else "  - _(no public API)_",
            "{{a11y_tier}}": inputs.get("a11y_tier", "wcag-aa"),
            "{{emit_controller}}": "yes" if inputs.get("emit_controller") else "no",
            "{{controller_class_name_or_none}}": ctrl_name or "_(none)_",
            "{{api_version}}": inputs.get("api_version", "60.0"),
            "{{target_org_alias_or_library_only}}": inputs.get("target_org_alias") or "_(library-only mode)_",
            "{{bundle_inventory_bullets}}": _bullets([f"`{c}`" for c in self.class_inventory(inputs)]),
            "{{grounding_symbols_bullets}}": _bullets(self.grounding_symbols(inputs)),
        }

    # --- Gate C ------------------------------------------------------------
    def discover_emitted_files(self, emitted_dir: Path) -> list[Path]:
        if not emitted_dir.exists():
            return []
        out: list[Path] = []
        for pat in ("*.js", "*.html", "*.css", "*.js-meta.xml", "*.cls", "*.test.js"):
            out.extend(emitted_dir.rglob(pat))
        return sorted(set(out))

    def static_check(self, files: list[Path]) -> list[str]:
        errors: list[str] = []
        if not files:
            return ["no LWC files under emitted_dir"]

        # Group by bundle dir (parent dir that contains .js + .html + .js-meta.xml)
        # The conventional layout is <bundle>/<bundle>.{js,html,css,js-meta.xml}.
        by_dir: dict[Path, dict[str, list[Path]]] = {}
        for f in files:
            d = f.parent if f.parent.name != "__tests__" else f.parent.parent
            by_dir.setdefault(d, {"js": [], "html": [], "css": [], "meta": [], "test": [], "cls": []})
            if f.suffix == ".js" and "__tests__" in f.parts:
                by_dir[d]["test"].append(f)
            elif f.name.endswith(".js-meta.xml"):
                by_dir[d]["meta"].append(f)
            elif f.suffix == ".js":
                by_dir[d]["js"].append(f)
            elif f.suffix == ".html":
                by_dir[d]["html"].append(f)
            elif f.suffix == ".css":
                by_dir[d]["css"].append(f)
            elif f.suffix == ".cls":
                by_dir[d]["cls"].append(f)

        for d, kinds in by_dir.items():
            # Only bundle dirs need the triple; apex controllers sit alone.
            if kinds["js"] or kinds["html"] or kinds["meta"]:
                if not kinds["js"]:
                    errors.append(f"{d.name}: missing <name>.js")
                if not kinds["html"]:
                    errors.append(f"{d.name}: missing <name>.html")
                if not kinds["meta"]:
                    errors.append(f"{d.name}: missing <name>.js-meta.xml")

                bundle_name = d.name
                for js in kinds["js"]:
                    errors.extend(self._check_js(js, bundle_name))
                for html in kinds["html"]:
                    errors.extend(self._check_html(html))
                for meta in kinds["meta"]:
                    errors.extend(self._check_meta(meta))

        # Apex controller files (sitting in their own dir or at emitted root):
        for f in files:
            if f.suffix == ".cls":
                src = f.read_text(encoding="utf-8", errors="replace")
                errors.extend(self._check_apex_controller(src, f.name))

        return errors

    def live_check(
        self,
        files: list[Path],
        target_org: str,
        api_version: str,
        timeout_sec: int = 300,
    ) -> LiveCheckResult:
        res = LiveCheckResult(oracle_label="sf project deploy validate (lwc)")
        if not shutil.which("sf"):
            res.errors.append({"file": None, "line": None, "column": None, "problem": "sf CLI not on PATH", "problem_type": "MissingCLI"})
            return res

        with tempfile.TemporaryDirectory(prefix="run_builder_lwc_") as tmp_s:
            tmp = Path(tmp_s)
            lwc_root = tmp / "force-app" / "main" / "default" / "lwc"
            classes_root = tmp / "force-app" / "main" / "default" / "classes"
            lwc_root.mkdir(parents=True)
            classes_root.mkdir(parents=True)
            (tmp / "sfdx-project.json").write_text(SFDX_PROJECT_JSON.replace("{api}", api_version), encoding="utf-8")

            # Group LWC files by bundle dir and copy the whole bundle into
            # lwc/<bundleName>/. Apex .cls files get their own meta xml.
            bundles: dict[str, list[Path]] = {}
            for f in files:
                if f.suffix == ".cls":
                    target = classes_root / f.name
                    target.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
                    (classes_root / (f.name + "-meta.xml")).write_text(
                        CLS_META_XML.replace("{api}", api_version), encoding="utf-8"
                    )
                    continue
                # bundle dir is the nearest dir whose name is NOT __tests__
                parent = f.parent
                if parent.name == "__tests__":
                    parent = parent.parent
                bundles.setdefault(parent.name, []).append(f)

            for bundle_name, bundle_files in bundles.items():
                dst = lwc_root / bundle_name
                dst.mkdir(parents=True, exist_ok=True)
                for f in bundle_files:
                    # Preserve __tests__ subdir shape — deploy ignores it but Jest needs it.
                    # Deploy-validate doesn't need __tests__; skip to keep payload clean.
                    if "__tests__" in f.parts:
                        continue
                    (dst / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")

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

    # --- private helpers ---------------------------------------------------
    def _check_js(self, js: Path, bundle_name: str) -> list[str]:
        errors: list[str] = []
        src = js.read_text(encoding="utf-8", errors="replace")

        if js.stem != bundle_name:
            errors.append(f"{js.name}: file stem does not match bundle dir '{bundle_name}'")

        # Cheap brace/paren balance
        cleaned = re.sub(r"//[^\n]*", "", src)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'"(?:\\.|[^"\\])*"', '""', cleaned)
        cleaned = re.sub(r"'(?:\\.|[^'\\])*'", "''", cleaned)
        cleaned = re.sub(r"`(?:\\.|[^`\\])*`", "``", cleaned)
        if cleaned.count("{") != cleaned.count("}"):
            errors.append(f"{js.name}: unbalanced braces ({cleaned.count('{')} open, {cleaned.count('}')} close)")
        if cleaned.count("(") != cleaned.count(")"):
            errors.append(f"{js.name}: unbalanced parens ({cleaned.count('(')} open, {cleaned.count(')')} close)")

        if "import" not in src or "LightningElement" not in src:
            errors.append(f"{js.name}: missing `import {{ LightningElement }}` from 'lwc'")
        if "extends LightningElement" not in src:
            errors.append(f"{js.name}: class does not extend LightningElement")
        if "export default class" not in src:
            errors.append(f"{js.name}: missing `export default class ...`")
        if re.search(r"\balert\s*\(", src):
            errors.append(f"{js.name}: uses raw `alert(...)`; use LightningAlert / ShowToastEvent instead")
        return errors

    def _check_html(self, html: Path) -> list[str]:
        errors: list[str] = []
        src = html.read_text(encoding="utf-8", errors="replace")
        if "<template" not in src:
            errors.append(f"{html.name}: template file missing root `<template>` element")
        # onclick on div/span without role — a11y smell
        if re.search(r"<(div|span)[^>]*\bonclick\s*=", src):
            errors.append(f"{html.name}: onclick on a non-interactive element (use <button>)")
        return errors

    def _check_meta(self, meta: Path) -> list[str]:
        errors: list[str] = []
        try:
            tree = ET.parse(str(meta))
        except ET.ParseError as e:
            return [f"{meta.name}: not valid XML ({e})"]
        root = tree.getroot()
        # Strip namespace from tag for comparison
        tag_local = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        if tag_local != "LightningComponentBundle":
            errors.append(f"{meta.name}: root element is '{tag_local}', expected LightningComponentBundle")
        return errors

    def coverage_thresholds(self, inputs: dict[str, Any]) -> dict[str, int]:
        # Jest is not a Gate C requirement — scratch orgs can't run it.
        return {"floor": 0, "high_tier": 0}

    def _check_apex_controller(self, src: str, filename: str) -> list[str]:
        errors: list[str] = []
        if "class " not in src:
            errors.append(f"{filename}: no class declaration")
        # Controllers usually expose @AuraEnabled(cacheable=true) methods; warn if none.
        if "@AuraEnabled" not in src and not filename.lower().endswith("test.cls"):
            errors.append(f"{filename}: LWC controller has no @AuraEnabled methods")
        return errors
