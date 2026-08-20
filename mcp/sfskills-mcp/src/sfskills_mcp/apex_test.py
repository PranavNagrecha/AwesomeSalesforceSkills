"""Read-only MCP tool: retrieve an existing Salesforce Apex test run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import sf_cli
from .deploy import resolve_report_cwd


def get_apex_test_run(
    test_run_id: str,
    target_org: str | None = None,
    method_limit: int = 100,
    cursor: str | None = None,
    project_dir: str | None = None,
) -> dict[str, Any]:
    """Retrieve ``sf apex get test --test-run-id`` and normalize it.

    Never starts or reruns tests. ``test_run_id`` is required (707…).
    """
    try:
        from . import paths as _paths

        _paths.ensure_pipelines_on_path()
        from pipelines.product.apex_test_result import normalize_apex_test_run
        from pipelines.product.test_run_id import is_well_formed_test_run_id
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"product libraries unavailable: {exc}"}

    if not test_run_id or not str(test_run_id).strip():
        return {"ok": False, "error": "test_run_id is required", "refusal_code": "missing_test_run_id"}
    test_run_id = str(test_run_id).strip()
    if not is_well_formed_test_run_id(test_run_id):
        return {
            "ok": False,
            "error": "malformed_test_run_id",
            "test_run_id": test_run_id,
            "hint": "Expected an Apex test run id (15/18 chars starting with 707).",
        }

    try:
        method_limit_i = int(method_limit or 100)
    except (TypeError, ValueError):
        method_limit_i = 100
    method_limit_i = max(1, min(method_limit_i, 500))

    args = ["apex", "get", "test", "--test-run-id", test_run_id, "--json"]
    report_cwd = resolve_report_cwd(project_dir)
    raw = sf_cli.run_sf_json(
        args,
        target_org=target_org,
        timeout=sf_cli.DEFAULT_TIMEOUT_SECONDS,
        cwd=str(report_cwd),
    )
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
        elif any(s in lowered for s in ("not found", "couldn't find", "could not find", "unknown")):
            kind = "unknown_or_expired_run"
        elif any(s in lowered for s in ("authenticated", "no default org", "no org found", "not logged")):
            kind = "unauthenticated_org"
        elif "did not return valid json" in lowered:
            kind = "malformed_json"
        elif "malformed" in lowered:
            kind = "malformed_test_run_id"
        normalized = normalize_apex_test_run(
            raw,
            method_limit=method_limit_i,
            cursor=cursor,
            source="sf_cli",
            cli_version=str(cli_version) if cli_version else None,
        )
        normalized["ok"] = False
        normalized["error"] = kind
        normalized["error_detail"] = err
        return normalized

    normalized = normalize_apex_test_run(
        raw,
        method_limit=method_limit_i,
        cursor=cursor,
        source="sf_cli",
        cli_version=str(cli_version) if cli_version else None,
    )
    if target_org:
        normalized["requested_org"] = target_org
    return normalized


def get_apex_test_run_from_file(
    path: str,
    method_limit: int = 100,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Credential-free fixture path used by tests and /triage-apex-tests mode B."""
    from pipelines.product.apex_test_result import normalize_apex_test_run

    file_path = Path(path)
    if not file_path.is_file():
        return {"ok": False, "error": "fixture_not_found", "path": path}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": "malformed_json", "detail": str(exc), "path": path}
    return normalize_apex_test_run(
        payload,
        method_limit=method_limit,
        cursor=cursor,
        source=f"file:{file_path.name}",
    )
