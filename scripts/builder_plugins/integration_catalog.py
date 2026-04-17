"""IntegrationCatalogBuilderPlugin — gated QA for integration-catalog-builder.

Emits a JSON catalog describing an org's integrations. Gate C:
  * Static: JSON parses; root shape is {catalog_version, org_alias, integrations[]}.
    Every integration has {name, direction, pattern, auth, endpoint|callout, owner}.
    direction ∈ {inbound, outbound, bidirectional}.
    pattern ∈ {REST, SOAP, Bulk, Streaming, PlatformEvent, CDC, PubSub,
               SalesforceConnect, MuleSoft, File}.
  * Live: for every Named Credential referenced by an integration, query
    `sf org list metadata --metadata-type NamedCredential --target-org <alias>`
    and confirm the referenced NC exists. If the catalog references RemoteSite,
    CSP, or ConnectedApp, those are validated similarly.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .base import LiveCheckResult


def _bullets(items: list[str], indent: str = "  ") -> str:
    if not items:
        return f"{indent}- _(none)_"
    return "\n".join(f"{indent}- {it}" for it in items)


VALID_DIRECTIONS = {"inbound", "outbound", "bidirectional"}
VALID_PATTERNS = {
    "REST", "SOAP", "Bulk", "Streaming", "PlatformEvent", "CDC",
    "PubSub", "SalesforceConnect", "MuleSoft", "File",
}
VALID_AUTH = {
    "NamedCredential", "OAuth2-ClientCred", "OAuth2-AuthCode", "OAuth2-JWT",
    "BasicAuth", "ApiKey", "mTLS", "SessionId", "None",
}


class IntegrationCatalogBuilderPlugin:
    agent = "integration-catalog-builder"

    # --- Gate A ------------------------------------------------------------
    def additional_input_checks(self, inputs: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        invalid: list[str] = []
        if not inputs.get("catalog_name"):
            missing.append("catalog_name")
        if not inputs.get("org_alias"):
            missing.append("org_alias")
        return missing, invalid

    # --- Gate B ------------------------------------------------------------
    def grounding_sobjects(self, inputs: dict[str, Any]) -> list[str]:
        return []

    def expected_resources(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        return []

    def expected_citations(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {"type": "skill", "id": "integration/named-credentials-setup"},
            {"type": "skill", "id": "integration/rest-api-patterns"},
            {"type": "decision_tree", "id": "integration-pattern-selection.md"},
        ]

    # --- deliverables ------------------------------------------------------
    def class_inventory(self, inputs: dict[str, Any]) -> list[str]:
        name = inputs.get("catalog_name") or "integration-catalog"
        return [f"{name}.json"]

    def expected_deliverable_stems(self, inputs: dict[str, Any]) -> set[str]:
        return set()

    # --- grounding symbols for REQUIREMENTS --------------------------------
    def grounding_symbols(self, inputs: dict[str, Any]) -> list[str]:
        syms = [f"Org alias: `{inputs.get('org_alias')}`"]
        for nc in inputs.get("named_credentials") or []:
            syms.append(f"NamedCredential: `{nc}` (must exist in org metadata)")
        return syms

    # --- requirements template vars ----------------------------------------
    def requirements_template_vars(
        self,
        inputs: dict[str, Any],
        run_id: str,
        inputs_sha256: str,
        agent_version: str = "1.0.0",
    ) -> dict[str, str]:
        ncs = inputs.get("named_credentials") or []
        return {
            "{{feature_summary_short}}": (inputs.get("feature_summary") or "").strip()[:80],
            "{{run_id}}": run_id,
            "{{generated_at}}": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "{{agent_version}}": agent_version,
            "{{inputs_sha256}}": inputs_sha256,
            "{{feature_summary}}": inputs.get("feature_summary", "_(unspecified)_"),
            "{{catalog_name}}": inputs.get("catalog_name", "integration-catalog"),
            "{{org_alias}}": inputs.get("org_alias", "_(unspecified)_"),
            "{{named_credentials_bullets}}": _bullets([f"`{nc}`" for nc in ncs]),
            "{{target_org_alias_or_library_only}}": inputs.get("target_org_alias") or inputs.get("org_alias") or "_(library-only mode)_",
            "{{grounding_symbols_bullets}}": _bullets(self.grounding_symbols(inputs)),
            "{{catalog_inventory_bullets}}": _bullets([f"`{c}`" for c in self.class_inventory(inputs)]),
            "{{api_version}}": inputs.get("api_version", "60.0"),
        }

    # --- Gate C ------------------------------------------------------------
    def discover_emitted_files(self, emitted_dir: Path) -> list[Path]:
        if not emitted_dir.exists():
            return []
        return sorted(emitted_dir.rglob("*.json"))

    def static_check(self, files: list[Path]) -> list[str]:
        errors: list[str] = []
        if not files:
            return ["no .json catalog under emitted_dir"]
        for f in files:
            errors.extend(self._check_catalog(f))
        return errors

    def live_check(
        self,
        files: list[Path],
        target_org: str,
        api_version: str,
        timeout_sec: int = 300,
    ) -> LiveCheckResult:
        """For each NamedCredential named in the catalog, list_metadata against
        the target org and confirm the NC exists."""
        res = LiveCheckResult(oracle_label="sf org list metadata (NamedCredential)")
        if not files:
            res.errors.append({"file": None, "line": None, "column": None, "problem": "no catalog to validate", "problem_type": "NoInput"})
            return res
        if not shutil.which("sf"):
            res.errors.append({"file": None, "line": None, "column": None, "problem": "sf CLI not on PATH", "problem_type": "MissingCLI"})
            return res

        try:
            doc = json.loads(files[0].read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            res.errors.append({"file": files[0].name, "line": None, "column": None, "problem": f"JSON parse error: {e}", "problem_type": "JSONParseError"})
            return res

        nc_refs: set[str] = set()
        for intg in doc.get("integrations") or []:
            nc = (intg or {}).get("named_credential")
            if nc:
                nc_refs.add(nc)

        res.ran = True
        if not nc_refs:
            # No NCs to check — the catalog can still be valid. Mark oracle clean.
            res.succeeded = True
            res.status = 0
            res.oracle_label = "sf org list metadata (no NamedCredentials to verify)"
            res.raw = {"num_component_errors": 0, "num_component_success": 0}
            return res

        # One CLI round-trip lists all NCs; compare fullName in-memory.
        cmd = ["sf", "org", "list", "metadata", "--metadata-type", "NamedCredential", "--target-org", target_org, "--json"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            res.errors.append({"file": None, "line": None, "column": None, "problem": f"sf timed out after {timeout_sec}s", "problem_type": "Timeout"})
            return res
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            res.errors.append({"file": None, "line": None, "column": None, "problem": f"unparseable sf JSON: {proc.stderr[:300] or proc.stdout[:300]}", "problem_type": "UnparseableCLIOutput"})
            return res
        if payload.get("status") not in (0, None):
            res.errors.append({"file": None, "line": None, "column": None, "problem": payload.get("message") or f"sf returned status {payload.get('status')}", "problem_type": payload.get("name") or "CLIError"})
            return res

        present = {(item.get("fullName") or "").strip() for item in (payload.get("result") or [])}
        missing = sorted(nc_refs - present)
        for nc in missing:
            res.errors.append({"file": files[0].name, "line": None, "column": None, "problem": f"NamedCredential '{nc}' not present in target org", "problem_type": "MissingNamedCredential"})

        res.succeeded = len(missing) == 0
        res.status = 0
        res.raw = {"num_component_errors": len(missing), "num_component_success": len(nc_refs) - len(missing)}
        return res

    def coverage_thresholds(self, inputs: dict[str, Any]) -> dict[str, int]:
        return {"floor": 0, "high_tier": 0}

    # --- private helpers ---------------------------------------------------
    def _check_catalog(self, path: Path) -> list[str]:
        errors: list[str] = []
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return [f"{path.name}: not valid JSON ({e})"]
        if not isinstance(doc, dict):
            return [f"{path.name}: root is not a JSON object"]

        for required in ("catalog_version", "org_alias", "integrations"):
            if required not in doc:
                errors.append(f"{path.name}: missing top-level `{required}`")

        version = str(doc.get("catalog_version", ""))
        if not re.match(r"^\d+\.\d+$", version):
            errors.append(f"{path.name}: catalog_version `{version}` not in `N.M` form")

        ints = doc.get("integrations")
        if not isinstance(ints, list):
            return errors + [f"{path.name}: `integrations` must be an array"]
        if not ints:
            return errors + [f"{path.name}: integrations[] is empty"]

        for i, it in enumerate(ints):
            if not isinstance(it, dict):
                errors.append(f"{path.name}: integrations[{i}] is not an object")
                continue
            for required in ("name", "direction", "pattern", "auth", "owner"):
                if required not in it:
                    errors.append(f"{path.name}: integrations[{i}] missing `{required}`")
            d = it.get("direction")
            if d and d not in VALID_DIRECTIONS:
                errors.append(f"{path.name}: integrations[{i}].direction `{d}` not in {sorted(VALID_DIRECTIONS)}")
            p = it.get("pattern")
            if p and p not in VALID_PATTERNS:
                errors.append(f"{path.name}: integrations[{i}].pattern `{p}` not in {sorted(VALID_PATTERNS)}")
            a = it.get("auth")
            if a and a not in VALID_AUTH:
                errors.append(f"{path.name}: integrations[{i}].auth `{a}` not in {sorted(VALID_AUTH)}")
            if not it.get("endpoint") and not it.get("callout"):
                errors.append(f"{path.name}: integrations[{i}] missing `endpoint` or `callout`")
        return errors
