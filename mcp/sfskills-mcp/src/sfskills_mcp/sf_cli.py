"""Thin wrapper around the Salesforce CLI (``sf``).

All ``sf`` commands used in this MCP server support ``--json``; we shell out,
capture JSON, and normalize the result. Errors surface as a structured
``{"error": ..., "stderr": ...}`` dict rather than raising, so MCP tools can
return them without the server dying.

The ``sf`` binary is resolved via the ``SFSKILLS_SF_BIN`` env var (useful when
agents run the server outside the user's interactive shell and ``sf`` isn't on
PATH), falling back to ``sf`` on PATH.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, Sequence


DEFAULT_TIMEOUT_SECONDS = 90


class SfCliError(RuntimeError):
    """Raised for unrecoverable CLI wrapper failures (e.g. binary missing)."""


def sf_binary() -> str:
    explicit = os.environ.get("SFSKILLS_SF_BIN")
    if explicit:
        return explicit
    resolved = shutil.which("sf")
    if resolved:
        return resolved
    raise SfCliError(
        "Salesforce CLI ('sf') was not found on PATH. Install it from "
        "https://developer.salesforce.com/tools/salesforcecli or set "
        "SFSKILLS_SF_BIN to the absolute path of the sf binary."
    )


def run_sf_json(
    args: Sequence[str],
    *,
    target_org: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Execute ``sf <args> --json`` and return the parsed payload.

    On command failure, returns a dict shaped as
    ``{"status": <int>, "error": <str>, "stderr": <str>, "args": [...]}``
    so callers can surface the error to the MCP client without raising.
    """
    try:
        binary = sf_binary()
    except SfCliError as exc:
        return {"status": 127, "error": str(exc), "args": list(args)}

    full_args: list[str] = [binary, *args]
    if target_org:
        full_args.extend(["--target-org", target_org])
    if "--json" not in full_args:
        full_args.append("--json")

    try:
        completed = subprocess.run(  # noqa: S603 — arguments are constructed, not shell-interpreted
            full_args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": 124,
            "error": f"sf command timed out after {timeout}s",
            "stderr": (exc.stderr or "")[:2000],
            "args": full_args[1:],
        }
    except OSError as exc:
        return {"status": 126, "error": f"failed to execute sf: {exc}", "args": full_args[1:]}

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    parsed: Any
    try:
        parsed = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError:
        return {
            "status": completed.returncode,
            "error": "sf did not return valid JSON",
            "stdout": stdout[:2000],
            "stderr": stderr[:2000],
            "args": full_args[1:],
        }

    if completed.returncode != 0 or (isinstance(parsed, dict) and parsed.get("status", 0) != 0):
        return {
            "status": completed.returncode,
            "error": _extract_error_message(parsed) or "sf command failed",
            "stderr": stderr[:2000],
            "args": full_args[1:],
            "payload": parsed,
        }

    return parsed if isinstance(parsed, dict) else {"result": parsed}


def _extract_error_message(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in ("message", "error", "name"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None
