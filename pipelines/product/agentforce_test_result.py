"""Normalize Agentforce Quality Engineer fixture payloads.

Never invokes the Salesforce CLI. Evidence IDs are stable; output is bounded to 32 KiB.
"""

from __future__ import annotations

from typing import Any

from pipelines.product.evidence_normalize import (
    bound_payload,
    extract_items,
    paginate,
    row_from_mapping,
    unwrap_cli_payload,
)

DEFAULT_ITEM_LIMIT = 100
LIST_KEYS = ("tests", "evidence_ids", "warnings")


def normalize_agentforce_test(
    payload: Any,
    *,
    item_limit: int = DEFAULT_ITEM_LIMIT,
    cursor: str | None = None,
    source: str = "fixture",
) -> dict[str, Any]:
    if isinstance(payload, dict) and payload.get("error") and "result" not in payload:
        return bound_payload(
            {
                "ok": False,
                "error": str(payload.get("error")),
                "truncated": False,
                "source": source,
                "tests": [],
                "evidence_ids": [],
            },
            list_keys=LIST_KEYS,
        )

    result, envelope = unwrap_cli_payload(payload)
    raw_items = extract_items(result, ('tests', 'failures', 'items',))
    rows = [
        row_from_mapping(item, kind="agent_test", id_prefix="afx")
        for item in raw_items
    ]
    page, next_cursor, truncated = paginate(rows, item_limit=item_limit, cursor=cursor)
    evidence_ids = [row["evidence_id"] for row in rows]
    normalized = {
        "ok": not envelope.get("malformed"),
        "tests": page,
        "evidence_ids": evidence_ids,
        "source_counts": {"tests": len(rows)},
        "truncated": truncated,
        "next_cursor": next_cursor,
        "item_limit": item_limit,
        "source": source,
        "cli_status": envelope.get("cli_status"),
        "malformed": bool(envelope.get("malformed")),
        "summary": {
            k: result.get(k)
            for k in result
            if k not in {'tests', 'failures', 'items'} and not isinstance(result.get(k), list)
        },
    }
    if envelope.get("malformed"):
        normalized["error"] = "malformed_or_unexpected_json"
    return bound_payload(normalized, list_keys=LIST_KEYS)
