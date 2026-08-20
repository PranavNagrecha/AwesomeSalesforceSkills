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

def validate_why_cant_user_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("user") or "").strip():
        errors.append("missing_user")
    if not str(payload.get("resource") or "").strip():
        errors.append("missing_resource")
    if not str(payload.get("operation") or "").strip():
        errors.append("missing_operation")
    result_path = payload.get("result_path")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_plan_metadata_change_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("component") or "").strip():
        errors.append("missing_component")
    if not str(payload.get("proposed_change") or "").strip():
        errors.append("missing_proposed_change")
    result_path = payload.get("result_path")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_profile_automation_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("object") or "").strip():
        errors.append("missing_object")
    if not str(payload.get("operation") or "").strip():
        errors.append("missing_operation")
    result_path = payload.get("result_path")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_review_release_readiness_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("release_scope") or "").strip():
        errors.append("missing_release_scope")
    result_path = payload.get("result_path")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_review_security_posture_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("scope") or "").strip():
        errors.append("missing_scope")
    result_path = payload.get("result_path")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_triage_integration_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("integration") or "").strip():
        errors.append("missing_integration")
    if not str(payload.get("time_window") or "").strip():
        errors.append("missing_time_window")
    result_path = payload.get("result_path")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_reconcile_data_load_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("migration_manifest") or "").strip():
        errors.append("missing_migration_manifest")
    result_files = payload.get("result_files")
    if not str(result_files or "").strip():
        errors.append("missing_result_files")
    elif not Path(str(result_files)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_assess_org_health_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    target_org = payload.get("target_org")
    evidence_bundle = payload.get("evidence_bundle")
    result_path = payload.get("result_path")
    if not target_org and not evidence_bundle and not result_path:
        errors.append("missing_evidence_source")
    result_path = payload.get("result_path") or payload.get("evidence_bundle")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_review_agentforce_agent_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("agent_metadata_path") or "").strip():
        errors.append("missing_agent_metadata_path")
    if not str(payload.get("agent_developer_name") or "").strip():
        errors.append("missing_agent_developer_name")
    result_path = payload.get("result_path")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors


def validate_compare_orgs_inputs(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("left_org_or_snapshot") or "").strip():
        errors.append("missing_left_org_or_snapshot")
    if not str(payload.get("right_org_or_snapshot") or "").strip():
        errors.append("missing_right_org_or_snapshot")
    result_path = payload.get("result_path")
    if result_path and not Path(str(result_path)).is_file():
        errors.append("result_path_not_found")
    if payload.get("use_most_recent"):
        errors.append("use_most_recent_forbidden")
    return errors
