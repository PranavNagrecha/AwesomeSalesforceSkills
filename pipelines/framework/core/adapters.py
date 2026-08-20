"""Deterministic core adapters bridging product modules and reference kernel."""

from __future__ import annotations

from typing import Any

from pipelines.product.evidence_lint import lint_diagnosis
from pipelines.product.handoff import validate_handoff

from .kernel_bridge import lint_claims as kernel_lint_claims
from .review import build_independent_review, can_complete


def lint_product_draft(draft: dict[str, Any], *, evidence_ids: list[str] | None = None) -> dict[str, Any]:
    """Run inherited product lint plus kernel claim lint when claims are present."""
    product_result = lint_diagnosis(draft, evidence_ids=evidence_ids)
    kernel_findings: list[dict[str, Any]] = []
    claims = draft.get("claims")
    evidence = draft.get("evidence") or draft.get("evidence_index")
    if isinstance(claims, list) and isinstance(evidence, list):
        kernel_findings = kernel_lint_claims(claims, evidence)
    errors = list(product_result.get("errors") or [])
    warnings = list(product_result.get("warnings") or [])
    for finding in kernel_findings:
        entry = {
            "code": finding.get("code", "kernel_lint"),
            "path": finding.get("claim_id", "$"),
            "message": str(finding),
        }
        if finding.get("severity") == "blocking":
            errors.append(entry)
        else:
            warnings.append(entry)
    passed = not errors
    return {
        **product_result,
        "errors": errors,
        "warnings": warnings,
        "passed": passed,
        "ok": passed,
        "verdict": "pass" if passed else "fail",
        "kernel_findings": kernel_findings,
    }


def validate_structured_handoff(payload: Any) -> list[str]:
    return validate_handoff(payload)


def finalize_review(
    draft: dict[str, Any],
    *,
    reviewer: str = "sf-evidence-reviewer",
    evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    lint = lint_product_draft(draft, evidence_ids=evidence_ids)
    review = build_independent_review(reviewer=reviewer, deterministic_lint=lint)
    return {"deterministic_lint": lint, "independent_review": review}


__all__ = [
    "can_complete",
    "finalize_review",
    "lint_product_draft",
    "validate_structured_handoff",
]
