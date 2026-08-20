"""Independent review result contract and completion gate."""

from __future__ import annotations

from typing import Any

from .envelope import normalize_evidence_review


def build_independent_review(
    *,
    reviewer: str,
    deterministic_lint: dict[str, Any],
    draft_findings: list[dict[str, Any]] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    blocking: list[str] = []
    warnings: list[str] = []
    for item in deterministic_lint.get("errors") or []:
        if isinstance(item, dict):
            blocking.append(str(item.get("code") or "lint_error"))
        else:
            blocking.append(str(item))
    for item in deterministic_lint.get("warnings") or []:
        if isinstance(item, dict):
            warnings.append(str(item.get("code") or "lint_warning"))
        else:
            warnings.append(str(item))
    for finding in draft_findings or []:
        if isinstance(finding, dict) and finding.get("severity") == "blocking":
            blocking.append(str(finding.get("code") or finding.get("id") or "review_blocking"))
    status = "blocked" if blocking else ("pass-with-warnings" if warnings else "pass")
    return {
        "reviewer": reviewer,
        "status": status,
        "blocking_findings": blocking,
        "warnings": warnings,
        "notes": notes or [],
    }


def can_complete(
    *,
    output_envelope: dict[str, Any],
    deterministic_lint: dict[str, Any],
    independent_review: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if output_envelope.get("status") == "completed":
        if deterministic_lint.get("errors") or deterministic_lint.get("verdict") == "fail":
            reasons.append("deterministic lint has blocking errors")
        review = normalize_evidence_review(independent_review or output_envelope.get("evidence_review"))
        if review["status"] == "blocked":
            reasons.append("independent review blocked")
        if review["blocking_findings"]:
            reasons.append("blocking review findings present")
    return (not reasons, reasons)
