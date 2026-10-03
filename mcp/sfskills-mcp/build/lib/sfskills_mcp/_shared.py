"""Shared SOQL plumbing for any module that needs to talk to ``sf``.

Lifted out of ``admin.py`` once a second consumer (``dev_org.py``) appeared.
Keeping these in one place avoids the silent-drift bug we already saw between
``admin.py`` and ``probes.py`` in the prototype, where the same SOQL recipe
diverged because two modules pasted slightly different versions.

Backwards compatibility: ``admin.py`` re-exports the public names so any
external caller importing ``from .admin import _run_soql`` keeps working.
"""

from __future__ import annotations

import re
from typing import Any

from . import sf_cli


_API_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _validate_api_name(value: str | None, *, kind: str) -> str | None:
    """Return an error message if ``value`` is not a safe API name, else ``None``.

    Used as the first line of defence against SOQL injection on
    string-interpolated object / field / permission-set names. Tighter than
    the SOQL spec — Salesforce does technically allow underscores at any
    position — but no real custom API name leads with one.
    """
    if not value or not _API_NAME_PATTERN.match(value):
        return f"{kind} must match /^[A-Za-z][A-Za-z0-9_]*$/ (got: {value!r})"
    return None


def _strip_attributes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip the ``attributes`` block Salesforce adds to every SOQL row.

    The block is metadata about the row's type and self-link — useful for
    REST clients, noise for an MCP that already knows what object it queried.
    """
    for record in records:
        if isinstance(record, dict):
            record.pop("attributes", None)
    return records


def _run_soql(
    soql: str,
    *,
    target_org: str | None,
    tooling: bool,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    """Execute a SOQL query via ``sf data query`` and return ``{record_count, records}``.

    ``timeout_seconds`` overrides the default ``sf`` subprocess timeout (90s).
    Use a higher value when probing large orgs — ``probe_apex_references``
    on a 5000-class org needs ~3-5 minutes.

    Surfaces errors as a dict (``{"error": ..., "stderr": ...}``) rather
    than raising — every consumer needs to be able to render the error to
    the MCP client without the server going down.
    """
    args = ["data", "query", "--query", soql]
    if tooling:
        args.append("--use-tooling-api")
    if timeout_seconds is not None:
        payload = sf_cli.run_sf_json(args, target_org=target_org, timeout=int(timeout_seconds))
    else:
        payload = sf_cli.run_sf_json(args, target_org=target_org)
    if "error" in payload and "result" not in payload:
        return payload
    records = (payload.get("result", {}) or {}).get("records", []) or []
    _strip_attributes(records)
    return {"record_count": len(records), "records": records}
