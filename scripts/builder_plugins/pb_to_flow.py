"""PbToFlowMigratorPlugin — Process-Builder-to-Flow migrator under the 5-gate protocol.

Migrates a Process Builder (WorkflowFlow metadata type) into an equivalent
Flow. Inputs name the source PB; outputs are one (or more) Flow metadata
files. Gate C reuses the FlowBuilderPlugin's static + live checks against
the emitted `*.flow-meta.xml`, plus a migrator-specific parity check that
the new Flow targets the same SObject as the source PB.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

from .base import LiveCheckResult
from .flow import FlowBuilderPlugin, _bullets


class PbToFlowMigratorPlugin(FlowBuilderPlugin):
    agent = "process-builder-to-flow-migrator"

    # --- Gate A extras -----------------------------------------------------
    def additional_input_checks(self, inputs: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        invalid: list[str] = []
        if not inputs.get("source_process_name"):
            missing.append("source_process_name (API name of the Process Builder being migrated)")
        if not inputs.get("trigger_sobject"):
            missing.append("trigger_sobject (the SObject the source PB was bound to)")
        return missing, invalid

    # --- grounding symbols for REQUIREMENTS --------------------------------
    def grounding_symbols(self, inputs: dict[str, Any]) -> list[str]:
        base = super().grounding_symbols(inputs)
        src = inputs.get("source_process_name") or "_(unspecified)_"
        return [
            f"Source Process Builder: `{src}` (must exist in source org metadata)",
            *base,
        ]

    # --- Gate B extras -----------------------------------------------------
    # Note: the source Process Builder is a reference to existing org metadata,
    # not a repo-resolvable path, so we don't add it to expected_resources. It
    # is surfaced in grounding_symbols for the REQUIREMENTS doc instead.

    def expected_citations(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        out = list(super().expected_citations(inputs))
        out.append({"type": "skill", "id": "flow/process-builder-to-flow-migration"})
        out.append({"type": "decision_tree", "id": "automation-selection.md"})
        return out

    # --- requirements template vars ----------------------------------------
    def requirements_template_vars(
        self,
        inputs: dict[str, Any],
        run_id: str,
        inputs_sha256: str,
        agent_version: str = "1.0.0",
    ) -> dict[str, str]:
        vars_ = super().requirements_template_vars(inputs, run_id, inputs_sha256, agent_version)
        vars_["{{source_process_name}}"] = inputs.get("source_process_name", "_(unspecified)_")
        vars_["{{migration_rationale}}"] = inputs.get("migration_rationale", "_(unspecified)_")
        vars_["{{parity_checklist_bullets}}"] = _bullets([
            f"`{c}`" for c in (inputs.get("parity_checklist") or [
                "entry criteria preserved",
                "all criteria nodes become decision branches",
                "immediate actions become same-transaction elements",
                "scheduled actions become scheduled paths",
                "field updates preserved with identical values",
                "process order preserved",
            ])
        ])
        return vars_
