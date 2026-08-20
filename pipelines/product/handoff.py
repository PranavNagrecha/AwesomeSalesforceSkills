"""Structured subagent handoff. Transcripts are not allowed."""

from __future__ import annotations

from typing import Any

HANDOFF_TASKS = {
    "context_librarian",
    "project_inspector",
    "org_grounder",
    "deployment_triager",
    "evidence_reviewer",
}

REQUIRED_KEYS = {
    "run_id",
    "task",
    "facts",
    "evidence_refs",
    "hypotheses",
    "unknowns",
    "recommended_next_agent",
    "context_metrics",
}


def empty_metrics() -> dict[str, Any]:
    return {
        "files_loaded": 0,
        "estimated_tokens": 0,
        "tool_output_bytes": 0,
        "truncated": False,
    }


def make_handoff(
    *,
    run_id: str,
    task: str,
    facts: list[Any] | None = None,
    evidence_refs: list[Any] | None = None,
    hypotheses: list[Any] | None = None,
    unknowns: list[Any] | None = None,
    recommended_next_agent: str | None = None,
    context_metrics: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "run_id": run_id,
        "task": task,
        "facts": facts or [],
        "evidence_refs": evidence_refs or [],
        "hypotheses": hypotheses or [],
        "unknowns": unknowns or [],
        "recommended_next_agent": recommended_next_agent,
        "context_metrics": {**empty_metrics(), **(context_metrics or {})},
    }
    if extra:
        # Ban transcript-sized blobs.
        if "transcript" in extra or "messages" in extra:
            raise ValueError("handoff must not include transcripts or message lists")
        payload.update(extra)
    return payload


def validate_handoff(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["handoff must be an object"]
    for key in REQUIRED_KEYS:
        if key not in payload:
            errors.append(f"missing {key}")
    if payload.get("task") and payload["task"] not in HANDOFF_TASKS:
        errors.append(f"unknown task {payload.get('task')!r}")
    metrics = payload.get("context_metrics")
    if not isinstance(metrics, dict):
        errors.append("context_metrics must be an object")
    else:
        for key in ("files_loaded", "estimated_tokens", "tool_output_bytes", "truncated"):
            if key not in metrics:
                errors.append(f"context_metrics missing {key}")
    for banned in ("transcript", "messages", "raw_subagent_output"):
        if banned in payload:
            errors.append(f"banned key {banned}")
    facts = payload.get("facts")
    if facts is not None and not isinstance(facts, list):
        errors.append("facts must be a list")
    return errors
