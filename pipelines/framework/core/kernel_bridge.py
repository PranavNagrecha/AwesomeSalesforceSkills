"""Reference-kernel bridge for deterministic V2 core behavior."""

from __future__ import annotations

import sys
from pathlib import Path

KERNEL_ROOT = (
    Path(__file__).resolve().parents[3]
    / "framework"
    / "specification"
    / "reference-kernel"
)
if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from saef_kernel.context import (  # noqa: E402
    ContextBudget,
    ContextCandidate,
    bound_tool_payload,
    compile_context_manifest,
)
from saef_kernel.evidence import calculate_confidence, lint_claims  # noqa: E402
from saef_kernel.ids import new_run_id, stable_claim_id, stable_evidence_id  # noqa: E402
from saef_kernel.policy import Decision, ProductPolicy, evaluate_salesforce_shell  # noqa: E402
from saef_kernel.run_state import InvalidTransition, RunStateMachine  # noqa: E402

__all__ = [
    "ContextBudget",
    "ContextCandidate",
    "Decision",
    "InvalidTransition",
    "ProductPolicy",
    "RunStateMachine",
    "bound_tool_payload",
    "calculate_confidence",
    "compile_context_manifest",
    "evaluate_salesforce_shell",
    "lint_claims",
    "new_run_id",
    "stable_claim_id",
    "stable_evidence_id",
]
