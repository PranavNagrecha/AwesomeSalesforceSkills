"""Read-only MCP tool: retrieve an existing Salesforce deploy job result."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import sf_cli


def get_deployment_result(
    job_id: str,
    target_org: str | None = None,
    wait_minutes: int = 0,
    failure_limit: int = 100,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Retrieve ``sf project deploy report --job-id`` and normalize it.

    Never starts, cancels, retries, or quick-deploys. ``job_id`` is required.
    ``wait_minutes`` may poll an in-progress job (still report-only).
    """
    try:
        from . import paths as _paths

        _paths.ensure_pipelines_on_path()
        from pipelines.product.deploy_result import normalize_deploy_report
        from pipelines.product.job_id import is_well_formed_job_id
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"product libraries unavailable: {exc}"}

    if not job_id or not str(job_id).strip():
        return {"ok": False, "error": "job_id is required", "refusal_code": "missing_job_id"}
    job_id = str(job_id).strip()
    if not is_well_formed_job_id(job_id):
        return {
            "ok": False,
            "error": "malformed_job_id",
            "job_id": job_id,
            "hint": "Expected a Metadata API deploy id (15/18 chars starting with 0Af).",
        }

    try:
        wait_minutes_i = int(wait_minutes or 0)
    except (TypeError, ValueError):
        wait_minutes_i = 0
    wait_minutes_i = max(0, wait_minutes_i)
    try:
        failure_limit_i = int(failure_limit or 100)
    except (TypeError, ValueError):
        failure_limit_i = 100
    failure_limit_i = max(1, min(failure_limit_i, 500))

    args = ["project", "deploy", "report", "--job-id", job_id]
    if wait_minutes_i > 0:
        args.extend(["--wait", str(wait_minutes_i)])

    timeout = sf_cli.DEFAULT_TIMEOUT_SECONDS
    if wait_minutes_i > 0:
        timeout = max(timeout, wait_minutes_i * 60 + 30)

    raw = sf_cli.run_sf_json(args, target_org=target_org, timeout=timeout)
    cli_version = None
    version_payload = sf_cli.run_sf_json(["--version"], timeout=15)
    if isinstance(version_payload, dict) and not version_payload.get("error"):
        result = version_payload.get("result")
        if isinstance(result, dict):
            cli_version = result.get("cliVersion") or result.get("version")
        cli_version = cli_version or version_payload.get("cliVersion")

    if isinstance(raw, dict) and raw.get("error"):
        err = str(raw.get("error") or "")
        lowered = err.lower()
        status = raw.get("status")
        kind = "cli_error"
        if status == 124 or "timed out" in lowered:
            kind = "cli_timeout"
        elif any(s in lowered for s in ("not found", "couldn't find", "could not find", "no_job", "unknown")):
            kind = "unknown_or_expired_job"
        elif any(s in lowered for s in ("authenticated", "no default org", "no org found", "not logged")):
            kind = "unauthenticated_org"
        elif "did not return valid json" in lowered:
            kind = "malformed_json"
        if "access token" in lowered or "refreshtoken" in lowered:
            kind = "redacted_auth_error"
        normalized = normalize_deploy_report(
            raw,
            failure_limit=failure_limit_i,
            cursor=cursor,
            source="sf_cli",
            cli_version=str(cli_version) if cli_version else None,
        )
        normalized["ok"] = False
        normalized["error"] = kind
        normalized["error_detail"] = err
        return normalized

    return normalize_deploy_report(
        raw,
        failure_limit=failure_limit_i,
        cursor=cursor,
        source="sf_cli",
        cli_version=str(cli_version) if cli_version else None,
    )


def get_deployment_result_from_file(
    path: str,
    failure_limit: int = 100,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Credential-free fixture path used by tests and /triage-deployment mode B."""
    from pipelines.product.deploy_result import normalize_deploy_report

    file_path = Path(path)
    if not file_path.is_file():
        return {"ok": False, "error": "fixture_not_found", "path": path}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": "malformed_json", "detail": str(exc), "path": path}
    return normalize_deploy_report(
        payload,
        failure_limit=failure_limit,
        cursor=cursor,
        source=f"file:{file_path.name}",
    )
