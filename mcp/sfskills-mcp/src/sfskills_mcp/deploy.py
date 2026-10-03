"""Read-only MCP tool: retrieve an existing Salesforce deploy job result."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import sf_cli


_EMPTY_SF_PROJECT = (
    Path(__file__).resolve().parents[2] / "resources" / "empty-sfdx-project"
)
_EMPTY_SF_PROJECT_FALLBACK: Path | None = None


def _ensure_empty_sf_project() -> Path:
    """Return a directory holding a minimal sfdx-project.json to run `sf` from.

    In a checkout that is `resources/empty-sfdx-project`. In a pip install the
    repo-relative path does not exist (the wheel ships only the package), so a
    minimal project is written once per process to a temp directory - the
    report-only commands only need some project root to run from. Found while
    inspecting the 0.5.0 wheel on 2026-10-03.
    """
    global _EMPTY_SF_PROJECT_FALLBACK
    if (_EMPTY_SF_PROJECT / "sfdx-project.json").is_file():
        return _EMPTY_SF_PROJECT
    fb = _EMPTY_SF_PROJECT_FALLBACK
    if fb is None or not (fb / "sfdx-project.json").is_file():
        import json
        import tempfile
        root = Path(tempfile.mkdtemp(prefix="sfskills-empty-sfdx-"))
        (root / "force-app").mkdir()
        (root / "sfdx-project.json").write_text(json.dumps({
            "packageDirectories": [{"path": "force-app", "default": True}],
            "name": "sfskills-report-cwd", "namespace": "",
            "sfdcLoginUrl": "https://login.salesforce.com", "sourceApiVersion": "67.0",
        }, indent=2) + "\n", encoding="utf-8")
        _EMPTY_SF_PROJECT_FALLBACK = root
    return _EMPTY_SF_PROJECT_FALLBACK


def resolve_report_cwd(project_dir: str | None = None) -> Path:
    """Directory that contains ``sfdx-project.json`` for ``sf project deploy report``.

    The CLI refuses to run that command outside a DX project. Cursor often
    hosts this MCP from a non-DX workspace (including this skill repo), so
    we accept an explicit project, walk parents of cwd, then fall back to a
    bundled empty project that is only a report cwd — never a deploy source.
    """
    candidates: list[Path] = []
    if project_dir and str(project_dir).strip():
        start = Path(project_dir).expanduser()
        try:
            start = start.resolve()
        except OSError:
            start = Path(project_dir).expanduser()
        candidates.append(start)
    candidates.append(Path.cwd())
    seen: set[Path] = set()
    for start in candidates:
        current: Path | None = start
        while current is not None and current not in seen:
            seen.add(current)
            if (current / "sfdx-project.json").is_file():
                return current
            parent = current.parent
            current = None if parent == current else parent
    return _ensure_empty_sf_project()


def get_deployment_result(
    job_id: str,
    target_org: str | None = None,
    wait_minutes: int = 0,
    failure_limit: int = 100,
    cursor: str | None = None,
    project_dir: str | None = None,
) -> dict[str, Any]:
    """Retrieve ``sf project deploy report --job-id`` and normalize it.

    Never starts, cancels, retries, or quick-deploys. ``job_id`` is required.
    ``wait_minutes`` may poll an in-progress job (still report-only).
    ``project_dir`` is an optional Salesforce DX project used only as CLI cwd.
    """
    try:
        from . import paths as _paths

        _paths.ensure_pipelines_on_path()
        from pipelines.product.deploy_cache import cache_target_org, usernames_match
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

    requested_username = None
    if target_org:
        display = sf_cli.run_sf_json(["org", "display"], target_org=target_org, timeout=30)
        requested_username = _username_from_display(display)
        cached = cache_target_org(job_id)
        if cached and requested_username and not usernames_match(cached, requested_username):
            return {
                "ok": False,
                "error": "job_org_mismatch",
                "job_id": job_id,
                "requested_org": target_org,
                "requested_username": requested_username,
                "cache_target_org": cached,
                "hint": (
                    "sf CLI deploy-cache has this job for a different org. "
                    "The product will not treat that result as belonging to "
                    f"{target_org}."
                ),
            }

    report_cwd = resolve_report_cwd(project_dir)
    raw = sf_cli.run_sf_json(
        args,
        target_org=target_org,
        timeout=timeout,
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
        elif any(s in lowered for s in ("not found", "couldn't find", "could not find", "no_job", "unknown")):
            kind = "unknown_or_expired_job"
        elif any(s in lowered for s in ("authenticated", "no default org", "no org found", "not logged")):
            kind = "unauthenticated_org"
        elif "did not return valid json" in lowered:
            kind = "malformed_json"
        elif "does not contain a valid salesforce dx project" in lowered:
            kind = "not_a_dx_project"
        elif "malformed_id" in lowered or "malformed id" in lowered:
            kind = "malformed_job_id"
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

    normalized = normalize_deploy_report(
        raw,
        failure_limit=failure_limit_i,
        cursor=cursor,
        source="sf_cli",
        cli_version=str(cli_version) if cli_version else None,
    )
    if requested_username:
        normalized["requested_org"] = target_org
        normalized["requested_username"] = requested_username
    cached = cache_target_org(job_id)
    if cached:
        normalized["cache_target_org"] = cached
    return normalized


def _username_from_display(payload: Any) -> str | None:
    if not isinstance(payload, dict) or payload.get("error"):
        return None
    result = payload.get("result") if isinstance(payload.get("result"), dict) else payload
    username = result.get("username")
    return str(username) if username else None


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
