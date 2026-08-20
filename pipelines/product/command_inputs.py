"""Typed input checks for /triage-deployment (this command only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .job_id import is_well_formed_job_id


def canonical_project_path(payload: dict[str, Any]) -> str | None:
    """Return the optional DX project path. Canonical key is project_path."""
    for key in ("project_path", "repo_path", "source_path"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def validate_triage_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    job_id = payload.get("job_id")
    result_path = payload.get("result_path")
    if not job_id and not result_path:
        errors.append("missing_evidence_source")
    if job_id and not is_well_formed_job_id(str(job_id)):
        errors.append("malformed_job_id")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_triage_apex_inputs(payload: dict[str, Any]) -> list[str]:
    from .test_run_id import is_well_formed_test_run_id

    errors: list[str] = []
    test_run_id = payload.get("test_run_id")
    result_path = payload.get("result_path") or payload.get("result_file")
    if not test_run_id and not result_path:
        errors.append("missing_evidence_source")
    if test_run_id and not is_well_formed_test_run_id(str(test_run_id)):
        errors.append("malformed_test_run_id")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors
