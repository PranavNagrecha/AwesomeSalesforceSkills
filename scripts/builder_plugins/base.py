"""BuilderPlugin — the per-agent contract run_builder.py depends on.

Every builder agent owns the behavior of:
  * what deliverables its emitted output should contain (class_inventory)
  * which symbols Gate B must resolve against an org or stub (grounding_symbols)
  * which {{variables}} its REQUIREMENTS_TEMPLATE.md uses (requirements_template_vars)
  * how Gate C discovers, statically checks, and live-checks emitted files

The harness calls these hooks. The plugin never imports the harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class LiveCheckResult:
    """Uniform shape for Gate C live-oracle results across plugins.

    ran           — True iff the oracle was actually invoked (e.g. sf CLI on PATH,
                    target org alias resolvable).
    succeeded     — True iff the oracle reported zero errors.
    status        — raw exit status or status code from the oracle.
    errors        — list of {file, line, column, problem, problem_type}. Always a
                    list; empty when succeeded.
    warnings      — list of strings; not fatal.
    oracle_label  — short human-readable name for rubric/report ("sf deploy-validate",
                    "lwc jest", "flow xml schema", etc.).
    raw           — plugin-specific extra data (number of components, coverage, etc.).
    """
    ran: bool = False
    succeeded: bool = False
    status: Any = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    oracle_label: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ran": self.ran,
            "succeeded": self.succeeded,
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "oracle_label": self.oracle_label,
            "num_errors": len(self.errors),
            "raw": self.raw,
        }


class BuilderPlugin(Protocol):
    """Per-agent behavior the harness delegates to."""

    agent: str  # e.g. "apex-builder"

    # --- deliverables ------------------------------------------------------
    def class_inventory(self, inputs: dict[str, Any]) -> list[str]:
        """Human-readable list of expected deliverable names.

        Used by Gate A.5 (requirements render) AND Gate C (expected_classes).
        Return display names (e.g. `AccountTrigger.trigger`, `AccountTriggerHandler`).
        """
        ...

    def expected_deliverable_stems(self, inputs: dict[str, Any]) -> set[str]:
        """Stems/filenames Gate C expects to find in emitted_dir.

        For Apex: class stems like 'AccountTrigger' (matched against Path.stem of .cls).
        For LWC: bundle names. For Flow: flow developer names.
        """
        ...

    # --- grounding ---------------------------------------------------------
    def grounding_symbols(self, inputs: dict[str, Any]) -> list[str]:
        """Display-ready grounding bullets for the requirements doc.

        Gate B also consults inputs directly (primary_sobject, referenced_fields,
        etc.) — this hook is purely for human-readable enumeration.
        """
        ...

    # --- requirements render -----------------------------------------------
    def requirements_template_vars(self, inputs: dict[str, Any], run_id: str, inputs_sha256: str, agent_version: str = "1.0.0") -> dict[str, str]:
        """Map of {{var}} → rendered string for this agent's REQUIREMENTS_TEMPLATE.md."""
        ...

    # --- Gate C -----------------------------------------------------------
    def discover_emitted_files(self, emitted_dir: Path) -> list[Path]:
        """Return the files Gate C should check (Apex: .cls/.trigger; LWC: bundle files; Flow: .flow-meta.xml)."""
        ...

    def static_check(self, files: list[Path]) -> list[str]:
        """Cheap offline check. Return list of error strings (empty on clean).

        This is the fast-fallback path — runs even when no live oracle is available.
        """
        ...

    def live_check(
        self,
        files: list[Path],
        target_org: str,
        api_version: str,
        timeout_sec: int = 300,
    ) -> LiveCheckResult:
        """Authoritative oracle against a real org / real validator.

        Plugins that don't need live validation (e.g. pure schema plugins) can
        return LiveCheckResult(ran=False, succeeded=True, oracle_label="(none)").
        """
        ...
