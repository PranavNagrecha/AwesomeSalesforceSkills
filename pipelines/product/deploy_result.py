"""Normalize Salesforce CLI ``project deploy report --json`` payloads.

The CLI shape has drifted across versions. This module produces one stable
schema with:

- component failures, Apex test failures, coverage issues, warnings, messages
- stable evidence IDs
- symptom grouping with occurrence counts
- pagination / truncation metadata

It never invokes the Salesforce CLI. Callers pass already-captured JSON.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

DEFAULT_FAILURE_LIMIT = 100
MAX_INJECT_BYTES = 32 * 1024


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _unwrap_cli_payload(payload: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (result_object, envelope_meta)."""
    if not isinstance(payload, dict):
        return {}, {"cli_status": None, "malformed": True}
    if "result" in payload and isinstance(payload["result"], dict):
        return payload["result"], {
            "cli_status": payload.get("status"),
            "cli_warnings": payload.get("warnings") or payload.get("warn"),
            "malformed": False,
        }
    # Bare DeployResult-shaped object.
    if any(k in payload for k in ("id", "status", "details", "done", "success")):
        return payload, {"cli_status": 0, "malformed": False}
    return payload, {"cli_status": payload.get("status"), "malformed": False}


def _stable_id(kind: str, *parts: str) -> str:
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"ev:{kind}:{digest}"


def _component_row(item: dict[str, Any]) -> dict[str, Any]:
    component_type = str(item.get("componentType") or item.get("type") or "")
    full_name = str(item.get("fullName") or item.get("fileName") or item.get("name") or "")
    problem = str(item.get("problem") or item.get("message") or item.get("error") or "")
    problem_type = str(item.get("problemType") or item.get("lineNumber") or "Error")
    file_name = str(item.get("fileName") or item.get("file") or "")
    line = item.get("lineNumber") or item.get("line")
    column = item.get("columnNumber") or item.get("column")
    evidence_id = _stable_id(
        "cf",
        component_type,
        full_name,
        problem,
        str(line or ""),
        str(column or ""),
    )
    return {
        "evidence_id": evidence_id,
        "kind": "component_failure",
        "component_type": component_type,
        "full_name": full_name,
        "file_name": file_name,
        "problem": problem,
        "problem_type": str(problem_type),
        "line": line,
        "column": column,
        "success": bool(item.get("success", False)),
    }


def _test_row(item: dict[str, Any]) -> dict[str, Any]:
    class_name = str(item.get("name") or item.get("className") or "")
    method = str(item.get("methodName") or item.get("method") or "")
    message = str(item.get("message") or item.get("problem") or "")
    stack = str(item.get("stackTrace") or "")
    evidence_id = _stable_id("tf", class_name, method, message)
    return {
        "evidence_id": evidence_id,
        "kind": "test_failure",
        "class_name": class_name,
        "method_name": method,
        "message": message,
        "stack_trace": stack,
    }


def _coverage_row(item: dict[str, Any], *, warning: bool) -> dict[str, Any]:
    name = str(item.get("name") or item.get("id") or "")
    message = str(item.get("message") or item.get("problem") or "")
    num_locs = item.get("numLocations")
    uncovered = item.get("numLocationsNotCovered")
    evidence_id = _stable_id("cov", "warn" if warning else "fail", name, message, str(uncovered or ""))
    return {
        "evidence_id": evidence_id,
        "kind": "coverage_warning" if warning else "coverage",
        "name": name,
        "message": message,
        "num_locations": num_locs,
        "num_locations_not_covered": uncovered,
    }


def _message_row(text: str, *, kind: str) -> dict[str, Any]:
    evidence_id = _stable_id("msg", kind, text)
    return {"evidence_id": evidence_id, "kind": kind, "message": text}


def group_symptoms(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group identical problems; preserve occurrence counts and evidence ids."""
    buckets: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in rows:
        key = "|".join(
            [
                str(row.get("kind") or ""),
                str(row.get("problem") or row.get("message") or ""),
                str(row.get("component_type") or ""),
            ]
        )
        if key not in buckets:
            buckets[key] = {
                "group_id": _stable_id("grp", key),
                "kind": row.get("kind"),
                "symptom": row.get("problem") or row.get("message") or "",
                "component_type": row.get("component_type") or "",
                "full_names": [],
                "occurrence_count": 0,
                "evidence_ids": [],
                "sample": row,
            }
            order.append(key)
        buckets[key]["occurrence_count"] += 1
        buckets[key]["evidence_ids"].append(row["evidence_id"])
        name = row.get("full_name") or row.get("class_name") or row.get("name")
        if name and name not in buckets[key]["full_names"]:
            buckets[key]["full_names"].append(name)
    return [buckets[k] for k in order]


def _paginate(items: list[Any], *, failure_limit: int, cursor: str | None) -> tuple[list[Any], str | None, bool]:
    start = 0
    if cursor:
        try:
            start = max(0, int(cursor))
        except (TypeError, ValueError):
            start = 0
    end = start + max(1, failure_limit)
    page = items[start:end]
    truncated = end < len(items)
    next_cursor = str(end) if truncated else None
    return page, next_cursor, truncated


def bound_for_model(payload: dict[str, Any], *, max_bytes: int = MAX_INJECT_BYTES) -> dict[str, Any]:
    """Ensure a payload is inject-safe. Never silently drop groups without truncation flags."""
    slim = dict(payload)

    def encoded_size(obj: dict[str, Any]) -> int:
        return len(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8"))

    size = encoded_size(slim)
    if size <= max_bytes:
        slim.setdefault("truncated", False)
        slim["byte_size"] = size
        return slim

    slim["truncated"] = True
    slim["truncation_reason"] = "exceeded_inject_budget"
    list_keys = ("component_failures", "test_failures", "coverage", "warnings", "messages", "groups", "evidence_ids")
    while encoded_size(slim) > max_bytes:
        shrunk = False
        for key in list_keys:
            values = slim.get(key)
            if isinstance(values, list) and len(values) > 1:
                slim[key] = values[: max(1, len(values) // 2)]
                shrunk = True
        if not shrunk:
            for key in list_keys:
                if isinstance(slim.get(key), list) and slim[key]:
                    slim[key] = slim[key][:1]
            slim["groups"] = slim.get("groups") or []
            if encoded_size(slim) > max_bytes:
                # Strip bulky sample bodies from groups.
                for group in slim.get("groups") or []:
                    if isinstance(group, dict):
                        group.pop("sample", None)
                        ids = group.get("evidence_ids")
                        if isinstance(ids, list) and len(ids) > 3:
                            group["evidence_ids"] = ids[:3]
                            group["evidence_ids_omitted"] = True
            if encoded_size(slim) > max_bytes:
                meta = {
                    "ok": slim.get("ok"),
                    "job_id": slim.get("job_id"),
                    "deploy_status": slim.get("deploy_status"),
                    "truncated": True,
                    "truncation_reason": "exceeded_inject_budget",
                    "next_cursor": slim.get("next_cursor") or "0",
                    "source_counts": slim.get("source_counts"),
                    "groups": (slim.get("groups") or [])[:1],
                    "component_failures": [],
                    "test_failures": [],
                    "coverage": [],
                    "warnings": [],
                    "messages": [],
                    "evidence_ids": (slim.get("evidence_ids") or [])[:5],
                    "source": slim.get("source"),
                }
                slim = meta
            break
    slim["byte_size"] = encoded_size(slim)
    slim["next_cursor"] = slim.get("next_cursor") or "0"
    return slim


def normalize_deploy_report(
    payload: Any,
    *,
    failure_limit: int = DEFAULT_FAILURE_LIMIT,
    cursor: str | None = None,
    source: str = "cli",
    cli_version: str | None = None,
) -> dict[str, Any]:
    if isinstance(payload, dict) and payload.get("error") and "result" not in payload:
        return {
            "ok": False,
            "error": str(payload.get("error")),
            "status_code": payload.get("status"),
            "truncated": False,
            "source": source,
            "cli_version": cli_version,
            "component_failures": [],
            "test_failures": [],
            "coverage": [],
            "warnings": [],
            "messages": [],
            "groups": [],
            "evidence_ids": [],
        }

    result, envelope = _unwrap_cli_payload(payload)
    details = result.get("details") if isinstance(result.get("details"), dict) else {}
    run_tests = details.get("runTestResult") if isinstance(details.get("runTestResult"), dict) else {}

    component_failures = [_component_row(x) for x in _as_list(details.get("componentFailures")) if isinstance(x, dict)]
    test_failures = [_test_row(x) for x in _as_list(run_tests.get("failures")) if isinstance(x, dict)]
    coverage = [_coverage_row(x, warning=False) for x in _as_list(run_tests.get("codeCoverage")) if isinstance(x, dict)]
    coverage_warnings = [
        _coverage_row(x, warning=True)
        for x in _as_list(run_tests.get("codeCoverageWarnings"))
        if isinstance(x, dict)
    ]
    warnings = [
        _message_row(str(x.get("problem") or x.get("message") or x), kind="warning")
        if isinstance(x, dict)
        else _message_row(str(x), kind="warning")
        for x in _as_list(details.get("componentSuccesses") and [])
    ]
    # Real warnings live on DeployMessage problemType=Warning and CLI warn arrays.
    extra_warnings = []
    for item in _as_list(details.get("componentFailures")):
        if isinstance(item, dict) and str(item.get("problemType") or "").lower() == "warning":
            extra_warnings.append(_message_row(str(item.get("problem") or ""), kind="warning"))
    for item in _as_list(envelope.get("cli_warnings")):
        extra_warnings.append(
            _message_row(str(item.get("message") if isinstance(item, dict) else item), kind="warning")
        )
    extra_warnings.extend(coverage_warnings)

    messages = []
    for key in ("errorMessage", "stateDetail", "status"):
        if result.get(key) and key != "status":
            messages.append(_message_row(str(result[key]), kind="message"))
    error_status = result.get("errorStatusCode")
    if error_status:
        messages.append(_message_row(str(error_status), kind="message"))

    all_rows = component_failures + test_failures + coverage + extra_warnings + messages
    groups = group_symptoms(component_failures + test_failures + extra_warnings)

    combined_for_page = component_failures + test_failures
    page, next_cursor, truncated = _paginate(
        combined_for_page, failure_limit=failure_limit, cursor=cursor
    )
    page_cf = [r for r in page if r["kind"] == "component_failure"]
    page_tf = [r for r in page if r["kind"] == "test_failure"]

    deploy_status = str(result.get("status") or result.get("state") or "")
    done = bool(result.get("done", deploy_status.lower() in {"succeeded", "failed", "canceled", "succeededpartial"}))
    success = bool(result.get("success", False))

    source_counts = {
        "component_failures": len(component_failures),
        "test_failures": len(test_failures),
        "coverage": len(coverage),
        "warnings": len(extra_warnings),
        "messages": len(messages),
        "groups": len(groups),
    }

    normalized = {
        "ok": True,
        "job_id": result.get("id") or result.get("jobId"),
        "deploy_status": deploy_status,
        "done": done,
        "success": success,
        "in_progress": (not done) or deploy_status.lower() in {"pending", "inprogress", "in_progress", "cancelinginprogress"},
        "check_only": result.get("checkOnly"),
        "ignore_warnings": result.get("ignoreWarnings"),
        "rollback_on_error": result.get("rollbackOnError"),
        "number_components_deployed": result.get("numberComponentsDeployed"),
        "number_component_errors": result.get("numberComponentErrors") or len(component_failures),
        "number_tests_completed": result.get("numberTestsCompleted"),
        "number_test_errors": result.get("numberTestErrors") or len(test_failures),
        "created_by": result.get("createdBy") or result.get("createdByName"),
        "start_date": result.get("startDate") or result.get("createdDate"),
        "completed_date": result.get("completedDate"),
        "error_status_code": error_status,
        "component_failures": page_cf,
        "test_failures": page_tf,
        "coverage": coverage[:failure_limit],
        "warnings": extra_warnings[:failure_limit],
        "messages": messages,
        "groups": groups[:failure_limit],
        "evidence_ids": [r["evidence_id"] for r in all_rows],
        "source_counts": source_counts,
        "truncated": truncated or len(coverage) > failure_limit or len(extra_warnings) > failure_limit,
        "next_cursor": next_cursor,
        "failure_limit": failure_limit,
        "source": source,
        "cli_version": cli_version,
        "cli_status": envelope.get("cli_status"),
        "malformed": bool(envelope.get("malformed")),
    }
    if envelope.get("malformed"):
        normalized["ok"] = False
        normalized["error"] = "malformed_or_unexpected_json"
    return bound_for_model(normalized)
