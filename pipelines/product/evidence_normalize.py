"""Shared helpers for product evidence normalizers (P03–P12).

Stable evidence IDs, pagination, and a 32 KiB inject bound. Never calls Salesforce.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

MAX_INJECT_BYTES = 32 * 1024
DEFAULT_ITEM_LIMIT = 100


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def stable_id(kind: str, *parts: str) -> str:
    digest = hashlib.sha256("\n".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12]
    return f"ev:{kind}:{digest}"


def unwrap_cli_payload(payload: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}, {"cli_status": None, "malformed": True}
    if "result" in payload and isinstance(payload["result"], dict):
        return payload["result"], {
            "cli_status": payload.get("status"),
            "cli_warnings": payload.get("warnings") or payload.get("warn"),
            "malformed": False,
        }
    return payload, {"cli_status": payload.get("status"), "malformed": False}


def paginate(items: list[Any], *, item_limit: int, cursor: str | None) -> tuple[list[Any], str | None, bool]:
    start = 0
    if cursor:
        try:
            start = max(0, int(cursor))
        except (TypeError, ValueError):
            start = 0
    limit = max(1, int(item_limit or DEFAULT_ITEM_LIMIT))
    end = start + limit
    page = items[start:end]
    truncated = end < len(items)
    next_cursor = str(end) if truncated else None
    return page, next_cursor, truncated


def encoded_size(obj: dict[str, Any]) -> int:
    return len(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def bound_payload(
    payload: dict[str, Any],
    *,
    list_keys: tuple[str, ...],
    max_bytes: int = MAX_INJECT_BYTES,
) -> dict[str, Any]:
    slim = dict(payload)
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


def row_from_mapping(item: dict[str, Any], *, kind: str, id_prefix: str) -> dict[str, Any]:
    name = str(item.get("name") or item.get("id") or item.get("component") or item.get("layer") or "")
    message = str(item.get("message") or item.get("reason") or item.get("summary") or "")
    evidence_id = stable_id(id_prefix, name, message, json.dumps(item, sort_keys=True, default=str)[:500])
    row = dict(item)
    row["evidence_id"] = evidence_id
    row["kind"] = kind
    if name and "name" not in row:
        row["name"] = name
    if message and "message" not in row:
        row["message"] = message
    return row


def extract_items(result: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key in keys:
        for raw in as_list(result.get(key)):
            if isinstance(raw, dict):
                items.append(raw)
    return items
