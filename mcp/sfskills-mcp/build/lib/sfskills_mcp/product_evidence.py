"""Fixture-first product evidence tools for P03–P12."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def _from_file(
    path: str,
    normalizer: Callable[..., dict[str, Any]],
    *,
    item_limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_file():
        return {"ok": False, "error": "fixture_not_found", "path": path}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": "malformed_json", "detail": str(exc), "path": path}
    return normalizer(
        payload,
        item_limit=item_limit,
        cursor=cursor,
        source=f"file:{file_path.name}",
    )


def get_user_access_evidence_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.user_access_result import normalize_user_access

    return _from_file(path, normalize_user_access, item_limit=item_limit, cursor=cursor)

def get_component_dependency_evidence_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.component_dependency_result import normalize_component_dependency

    return _from_file(path, normalize_component_dependency, item_limit=item_limit, cursor=cursor)

def get_automation_inventory_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.automation_inventory_result import normalize_automation_inventory

    return _from_file(path, normalize_automation_inventory, item_limit=item_limit, cursor=cursor)

def get_flow_test_result_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.flow_test_result import normalize_flow_test

    return _from_file(path, normalize_flow_test, item_limit=item_limit, cursor=cursor)

def get_code_analysis_result_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.code_analysis_result import normalize_code_analysis

    return _from_file(path, normalize_code_analysis, item_limit=item_limit, cursor=cursor)

def get_integration_config_summary_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.integration_config_result import normalize_integration_config

    return _from_file(path, normalize_integration_config, item_limit=item_limit, cursor=cursor)

def get_data_load_result_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.data_load_result import normalize_data_load

    return _from_file(path, normalize_data_load, item_limit=item_limit, cursor=cursor)

def get_org_snapshot_manifest_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.org_snapshot_result import normalize_org_snapshot

    return _from_file(path, normalize_org_snapshot, item_limit=item_limit, cursor=cursor)

def get_agentforce_test_result_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.agentforce_test_result import normalize_agentforce_test

    return _from_file(path, normalize_agentforce_test, item_limit=item_limit, cursor=cursor)

def compare_org_snapshots_from_file(path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    from pipelines.product.org_compare_result import normalize_org_compare

    return _from_file(path, normalize_org_compare, item_limit=item_limit, cursor=cursor)


def _require_path(result_path: str, loader: Callable[..., dict[str, Any]], item_limit: int, cursor: str | None) -> dict[str, Any]:
    if not result_path or not str(result_path).strip():
        return {"ok": False, "error": "result_path is required", "refusal_code": "missing_evidence_source"}
    return loader(str(result_path).strip(), item_limit=item_limit, cursor=cursor)


def get_user_access_evidence(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, get_user_access_evidence_from_file, item_limit, cursor)


def get_component_dependency_evidence(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, get_component_dependency_evidence_from_file, item_limit, cursor)


def get_automation_inventory(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, get_automation_inventory_from_file, item_limit, cursor)


def get_flow_test_result(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, get_flow_test_result_from_file, item_limit, cursor)


def get_code_analysis_result(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, get_code_analysis_result_from_file, item_limit, cursor)


def get_integration_config_summary(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, get_integration_config_summary_from_file, item_limit, cursor)


def get_data_load_result(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, get_data_load_result_from_file, item_limit, cursor)


def get_org_snapshot_manifest(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, get_org_snapshot_manifest_from_file, item_limit, cursor)


def get_agentforce_test_result(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, get_agentforce_test_result_from_file, item_limit, cursor)


def compare_org_snapshots(result_path: str, item_limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
    return _require_path(result_path, compare_org_snapshots_from_file, item_limit, cursor)
