"""Normalize Salesforce CLI ``apex get test --json`` payloads.

Produces a stable schema with method failures, coverage, timing, symptom
grouping, and shared-root-cause clustering. Never invokes the Salesforce CLI.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from pipelines.product.deploy_result import bound_for_model, group_symptoms

DEFAULT_METHOD_LIMIT = 100
MAX_INJECT_BYTES = 32 * 1024

_STACK_ROOT_RE = re.compile(r"(Class\.[^\s:]+(?::\s*line\s*\d+)?)", re.IGNORECASE)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _stable_id(kind: str, *parts: str) -> str:
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"ev:{kind}:{digest}"


def _unwrap_cli_payload(payload: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}, {"cli_status": None, "malformed": True}
    if "result" in payload and isinstance(payload["result"], dict):
        return payload["result"], {
            "cli_status": payload.get("status"),
            "cli_warnings": payload.get("warnings") or payload.get("warn"),
            "malformed": False,
        }
    if any(k in payload for k in ("summary", "tests", "testRunId", "outcome")):
        return payload, {"cli_status": 0, "malformed": False}
    return payload, {"cli_status": payload.get("status"), "malformed": False}


def _class_name(item: dict[str, Any]) -> str:
    apex = item.get("ApexClass")
    if isinstance(apex, dict) and apex.get("Name"):
        return str(apex["Name"])
    full = str(item.get("FullName") or "")
    if "." in full:
        return full.split(".", 1)[0]
    return str(item.get("className") or item.get("name") or "")


def _method_name(item: dict[str, Any]) -> str:
    if item.get("MethodName"):
        return str(item["MethodName"])
    full = str(item.get("FullName") or "")
    if "." in full:
        return full.split(".", 1)[1]
    return str(item.get("methodName") or item.get("method") or "")


def _stack_root(stack: str) -> str:
    match = _STACK_ROOT_RE.search(stack or "")
    return match.group(1) if match else ""


def classify_failure_kind(message: str, stack: str = "") -> str:
    text = f"{message}\n{stack}".lower()
    if "mixed dml" in text or "mixed_dml" in text:
        return "mixed_dml"
    if "callout" in text or "test.setmock" in text or "uncommitted work" in text:
        return "missing_mock"
    if any(s in text for s in ("too many", "limit", "governor", "heap size", "cpu time")):
        return "governor"
    if any(s in text for s in ("insufficient access", "field is not writeable", "sharing", "row cause")):
        return "sharing_context"
    if any(s in text for s in ("queueable", "future method", "batch ", "async")):
        return "async_boundary"
    if "assert" in text:
        return "assertion"
    return "unknown"


def _method_row(item: dict[str, Any]) -> dict[str, Any]:
    class_name = _class_name(item)
    method = _method_name(item)
    message = str(item.get("Message") or item.get("message") or "")
    stack = str(item.get("StackTrace") or item.get("stackTrace") or "")
    outcome = str(item.get("Outcome") or item.get("outcome") or "")
    run_time = item.get("RunTime") or item.get("runTime")
    evidence_id = _stable_id("am", class_name, method, message, stack)
    kind = classify_failure_kind(message, stack)
    return {
        "evidence_id": evidence_id,
        "kind": "method_failure",
        "class_name": class_name,
        "method_name": method,
        "full_name": f"{class_name}.{method}" if class_name and method else class_name or method,
        "message": message,
        "stack_trace": stack,
        "stack_root": _stack_root(stack),
        "outcome": outcome,
        "run_time_ms": run_time,
        "failure_kind": kind,
    }


def _coverage_row(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("name") or item.get("ApexClassOrTrigger") or item.get("Name") or "")
    num_locs = item.get("NumLinesCovered") or item.get("numLocationsCovered")
    total = item.get("NumLinesUncovered") or item.get("numLocations")
    message = str(item.get("message") or "")
    evidence_id = _stable_id("cov", name, str(num_locs or ""), str(total or ""), message)
    return {
        "evidence_id": evidence_id,
        "kind": "coverage",
        "name": name,
        "num_lines_covered": num_locs,
        "num_lines_uncovered": total,
        "message": message,
    }


def cluster_shared_roots(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group failing methods by failure_kind + stack_root or normalized message."""
    buckets: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in rows:
        if row.get("kind") != "method_failure":
            continue
        root = row.get("stack_root") or row.get("message") or ""
        key = "|".join([str(row.get("failure_kind") or ""), str(root)])
        if key not in buckets:
            buckets[key] = {
                "cluster_id": _stable_id("root", key),
                "failure_kind": row.get("failure_kind"),
                "stack_root": row.get("stack_root") or None,
                "symptom": row.get("message") or "",
                "methods": [],
                "occurrence_count": 0,
                "evidence_ids": [],
            }
            order.append(key)
        buckets[key]["occurrence_count"] += 1
        buckets[key]["evidence_ids"].append(row["evidence_id"])
        full = row.get("full_name")
        if full and full not in buckets[key]["methods"]:
            buckets[key]["methods"].append(full)
    return [buckets[k] for k in order]


def _paginate(items: list[Any], *, method_limit: int, cursor: str | None) -> tuple[list[Any], str | None, bool]:
    start = 0
    if cursor:
        try:
            start = max(0, int(cursor))
        except (TypeError, ValueError):
            start = 0
    end = start + max(1, method_limit)
    page = items[start:end]
    truncated = end < len(items)
    next_cursor = str(end) if truncated else None
    return page, next_cursor, truncated


def _bound_apex(payload: dict[str, Any], *, max_bytes: int = MAX_INJECT_BYTES) -> dict[str, Any]:
    slim = dict(payload)
    list_keys = (
        "method_failures",
        "coverage",
        "groups",
        "shared_root_clusters",
        "evidence_ids",
        "warnings",
    )

    def encoded_size(obj: dict[str, Any]) -> int:
        return len(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8"))

    size = encoded_size(slim)
    if size <= max_bytes:
        slim.setdefault("truncated", False)
        slim["byte_size"] = size
        return slim

    slim["truncated"] = True
    slim["truncation_reason"] = "exceeded_inject_budget"
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
            break
    slim["byte_size"] = encoded_size(slim)
    return slim


def normalize_apex_test_run(
    payload: Any,
    *,
    method_limit: int = DEFAULT_METHOD_LIMIT,
    cursor: str | None = None,
    source: str = "cli",
    cli_version: str | None = None,
) -> dict[str, Any]:
    if isinstance(payload, dict) and payload.get("error") and "result" not in payload:
        return _bound_apex(
            {
                "ok": False,
                "error": str(payload.get("error")),
                "status_code": payload.get("status"),
                "truncated": False,
                "source": source,
                "cli_version": cli_version,
                "method_failures": [],
                "coverage": [],
                "groups": [],
                "shared_root_clusters": [],
                "evidence_ids": [],
            }
        )

    result, envelope = _unwrap_cli_payload(payload)
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    tests = [_method_row(x) for x in _as_list(result.get("tests")) if isinstance(x, dict)]
    failures = [row for row in tests if str(row.get("outcome") or "").lower() in {"fail", "failed"}]
    if not failures:
        failures = [
            row
            for row in tests
            if row.get("message") or row.get("stack_trace") or str(row.get("outcome") or "").lower() == "fail"
        ]

    coverage_rows = [
        _coverage_row(x)
        for x in _as_list(result.get("coverage") or result.get("codeCoverage"))
        if isinstance(x, dict)
    ]
    warnings = []
    for item in _as_list(envelope.get("cli_warnings")):
        text = str(item.get("message") if isinstance(item, dict) else item)
        warnings.append({"evidence_id": _stable_id("warn", text), "kind": "warning", "message": text})

    groups = group_symptoms(failures)
    shared_roots = cluster_shared_roots(failures)
    page, next_cursor, truncated = _paginate(failures, method_limit=method_limit, cursor=cursor)

    outcome = str(summary.get("outcome") or result.get("outcome") or "")
    test_run_id = summary.get("testRunId") or result.get("testRunId") or result.get("id")
    tests_ran = summary.get("testsRan") or result.get("testsRan")
    passing = summary.get("passing") or result.get("passing")
    failing_count = summary.get("failing") or result.get("failing") or len(failures)
    skipped = summary.get("skipped") or result.get("skipped")

    source_counts = {
        "methods_total": len(tests),
        "method_failures": len(failures),
        "coverage": len(coverage_rows),
        "warnings": len(warnings),
        "groups": len(groups),
        "shared_root_clusters": len(shared_roots),
    }

    all_rows = failures + coverage_rows + warnings
    normalized = {
        "ok": True,
        "test_run_id": test_run_id,
        "outcome": outcome,
        "tests_ran": tests_ran,
        "passing": passing,
        "failing": failing_count,
        "skipped": skipped,
        "org_id": summary.get("orgId") or result.get("orgId"),
        "method_failures": page,
        "coverage": coverage_rows[:method_limit],
        "warnings": warnings[:method_limit],
        "groups": groups[:method_limit],
        "shared_root_clusters": shared_roots[:method_limit],
        "evidence_ids": [r["evidence_id"] for r in all_rows],
        "source_counts": source_counts,
        "truncated": truncated or len(coverage_rows) > method_limit or len(shared_roots) > method_limit,
        "next_cursor": next_cursor,
        "method_limit": method_limit,
        "source": source,
        "cli_version": cli_version,
        "cli_status": envelope.get("cli_status"),
        "malformed": bool(envelope.get("malformed")),
    }
    if envelope.get("malformed"):
        normalized["ok"] = False
        normalized["error"] = "malformed_or_unexpected_json"
    return _bound_apex(normalized)
