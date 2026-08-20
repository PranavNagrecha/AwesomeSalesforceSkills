"""Output envelope v2 builder (backward compatible with product drafts)."""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "2.0.0"
TERMINAL = {"completed", "partial", "refused", "failed"}


def normalize_evidence_review(review: dict[str, Any] | None) -> dict[str, Any]:
    review = review or {}
    status = review.get("status") or ("blocked" if review.get("blocking_findings") else "pass")
    if status == "fail":
        status = "blocked"
    if status not in {"pass", "pass-with-warnings", "blocked"}:
        status = "blocked" if review.get("blocking_findings") else "pass-with-warnings"
    blocking = review.get("blocking_findings") or []
    if isinstance(blocking, list) and blocking and isinstance(blocking[0], dict):
        blocking = [str(item.get("code") or item) for item in blocking]
    warnings = review.get("warnings") or []
    if isinstance(warnings, list) and warnings and isinstance(warnings[0], dict):
        warnings = [str(item.get("code") or item) for item in warnings]
    return {
        "status": status,
        "blocking_findings": [str(x) for x in blocking],
        "warnings": [str(x) for x in warnings],
    }


def build_output_envelope(
    *,
    run_id: str,
    product_id: str,
    status: str,
    mode: str,
    summary: str,
    findings: list[dict[str, Any]] | None = None,
    unknowns: list[str] | None = None,
    evidence_review: dict[str, Any] | None = None,
    provenance: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    recommendations: list[dict[str, Any]] | None = None,
    contradictions: list[dict[str, Any]] | None = None,
    persisted: bool = False,
    report_path: str | None = None,
    envelope_path: str | None = None,
) -> dict[str, Any]:
    if status not in TERMINAL:
        raise ValueError(f"status must be one of {sorted(TERMINAL)}")
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "product_id": product_id,
        "status": status,
        "mode": mode,
        "summary": summary,
        "findings": findings or [],
        "unknowns": unknowns or [],
        "recommendations": recommendations or [],
        "contradictions": contradictions or [],
        "evidence_review": normalize_evidence_review(evidence_review),
        "provenance": provenance or {},
        "metrics": metrics or {},
        "persisted": persisted,
        "report_path": report_path,
        "envelope_path": envelope_path,
    }


def envelope_from_product_draft(draft: dict[str, Any], *, product_id: str, mode: str, run_id: str | None = None) -> dict[str, Any]:
    """Map inherited P01 draft shapes into envelope v2."""
    status = str(draft.get("status") or draft.get("outcome") or "partial").lower()
    if status not in TERMINAL:
        status = "partial"
    lint = draft.get("deterministic_lint") or draft.get("lint") or {}
    review_status = "blocked" if lint.get("errors") or lint.get("verdict") == "fail" else "pass"
    if lint.get("warnings"):
        review_status = "pass-with-warnings"
    findings = draft.get("findings") or []
    if not findings and draft.get("hypotheses"):
        findings = [
            {
                "id": f"F-{index+1}",
                "title": str(h.get("summary") or h.get("title") or "hypothesis"),
                "severity": "medium",
                "claim_ids": [],
            }
            for index, h in enumerate(draft.get("hypotheses") or [])
            if isinstance(h, dict)
        ]
    return build_output_envelope(
        run_id=run_id or str(draft.get("run_id") or "RUN-UNKNOWN"),
        product_id=product_id,
        status=status,
        mode=mode,
        summary=str(draft.get("summary") or draft.get("executive_summary") or "Deployment triage draft"),
        findings=findings,
        unknowns=[str(u) for u in (draft.get("unknowns") or [])],
        evidence_review={
            "status": review_status,
            "blocking_findings": [e.get("code", str(e)) for e in (lint.get("errors") or []) if isinstance(e, dict)],
            "warnings": [w.get("code", str(w)) for w in (lint.get("warnings") or []) if isinstance(w, dict)],
        },
        provenance={"source": "product-draft"},
        metrics=draft.get("context_metrics") or {},
        persisted=bool(draft.get("persisted", False)),
        report_path=draft.get("report_path"),
        envelope_path=draft.get("envelope_path"),
    )
