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
import re
import shutil
import subprocess
from typing import Any, Sequence


# --------------------------------------------------------------------------- #
# Credential redaction                                                         #
# --------------------------------------------------------------------------- #
#
# A live test session (2026-05-10) leaked an `accessToken` because:
#   1. ``sf org display --json`` prepended an "update available" warning line
#      to stdout.
#   2. ``json.loads`` failed.
#   3. The error path returned ``stdout[:2000]`` unredacted — and stdout
#      contained the access token.
#
# Defense in depth: redact at two layers.
#   - ``_redact_credentials_text`` — regex scrub for any code path that
#     puts raw stdout/stderr text into a return value or log.
#   - ``_redact_credentials_in_payload`` — walks parsed JSON and replaces
#     sensitive-keyed values BEFORE the payload reaches any caller. So even
#     if a downstream tool naively prints the payload, no token escapes.

_REDACTED = "[REDACTED]"

# Salesforce session/access token. Starts with the 15- or 18-char org id
# prefix (``00D...``), a literal ``!``, then a base64-ish blob.
_SF_TOKEN_RE = re.compile(r"\b00[A-Z][A-Za-z0-9]{12,15}![A-Za-z0-9._\-]{20,200}")

# OAuth refresh / connected-app secret. Starts with ``5Aep`` / ``5At`` etc.
# Length floor (30) avoids matching short legitimate strings that share the
# prefix.
_OAUTH_REFRESH_RE = re.compile(r"\b5A[a-zA-Z][A-Za-z0-9._\-]{30,200}")

# Bearer header token (defensive — sf CLI doesn't emit these but downstream
# wrappers might log curl-style HTTP captures).
_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE)

# Lowercase keys that always carry credentials. We compare lowercased keys
# at lookup time, so the frozenset stays case-folded.
_SENSITIVE_KEYS = frozenset({
    "accesstoken", "refreshtoken", "password", "clientsecret",
    "securitytoken", "sessionid", "apitoken", "authtoken",
})


def _redact_credentials_text(text: str) -> str:
    """Replace credential-shaped substrings in arbitrary text with ``[REDACTED]``.

    Applied to every code path that surfaces raw stdout/stderr from ``sf``
    subprocess invocations. Catches:
      - Salesforce session tokens (``00D…!…``)
      - OAuth refresh / connected-app tokens (``5A…``)
      - ``Bearer …`` Authorization headers
    """
    if not text:
        return text
    text = _SF_TOKEN_RE.sub(_REDACTED, text)
    text = _OAUTH_REFRESH_RE.sub(_REDACTED, text)
    text = _BEARER_RE.sub(f"Bearer {_REDACTED}", text)
    return text


def _redact_credentials_in_payload(obj: Any) -> Any:
    """Walk a parsed JSON payload and redact credential-keyed values + any
    credential-shaped strings found in non-sensitive fields.

    Pure (returns a redacted copy; does not mutate input). Idempotent.
    """
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(k, str) and k.lower() in _SENSITIVE_KEYS and isinstance(v, str):
                out[k] = _REDACTED
            else:
                out[k] = _redact_credentials_in_payload(v)
        return out
    if isinstance(obj, list):
        return [_redact_credentials_in_payload(item) for item in obj]
    if isinstance(obj, str):
        return _redact_credentials_text(obj)
    return obj


def _default_timeout() -> int:
    """Resolve the default ``sf`` subprocess timeout.

    Environment override: ``SFSKILLS_TIMEOUT_SECONDS`` (positive int). Lets
    a deployer raise the cap for orgs with thousands of Apex classes /
    Flow versions without changing every tool call site. Falls back to
    90s — covers ~95% of probes against typical orgs.
    """
    raw = os.environ.get("SFSKILLS_TIMEOUT_SECONDS")
    if raw and raw.isdigit() and int(raw) > 0:
        return int(raw)
    return 90


# Re-export so existing call sites that import this constant keep working.
DEFAULT_TIMEOUT_SECONDS = _default_timeout()


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
    timeout: int | None = None,
) -> dict[str, Any]:
    """Execute ``sf <args> --json`` and return the parsed payload.

    Timeout precedence (highest first):
      1. The ``timeout`` keyword arg (per-call override)
      2. The ``SFSKILLS_TIMEOUT_SECONDS`` env var (deployer-wide override)
      3. The 90-second default

    On command failure, returns a dict shaped as
    ``{"status": <int>, "error": <str>, "stderr": <str>, "args": [...]}``
    so callers can surface the error to the MCP client without raising.
    """
    if timeout is None:
        timeout = _default_timeout()
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
            "stderr": _redact_credentials_text((exc.stderr or "")[:2000]),
            "args": full_args[1:],
        }
    except OSError as exc:
        return {"status": 126, "error": f"failed to execute sf: {exc}", "args": full_args[1:]}

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    parsed: Any
    try:
        # sf CLI sometimes prepends update-available / deprecation warning
        # lines BEFORE its JSON output:
        #   "›   Warning: @salesforce/cli update available from 2.103 to 2.133"
        #   '{"status": 0, "result": {...}}'
        # If json.loads() sees the warning, it raises — and the legacy
        # error path returned raw stdout (which contained the access
        # token; see fix #1). Strip lines until the first '{' or '['
        # before parsing.
        parseable = _strip_to_json_start(stdout)
        parsed = json.loads(parseable) if parseable.strip() else {}
    except json.JSONDecodeError:
        return {
            "status": completed.returncode,
            "error": "sf did not return valid JSON",
            "stdout": _redact_credentials_text(stdout[:2000]),
            "stderr": _redact_credentials_text(stderr[:2000]),
            "args": full_args[1:],
        }

    # Redact credential-keyed fields in the parsed payload BEFORE it leaves
    # this function. So even if a downstream caller naively serialises the
    # whole payload (e.g. a debug log), no token escapes.
    parsed = _redact_credentials_in_payload(parsed)

    if completed.returncode != 0 or (isinstance(parsed, dict) and parsed.get("status", 0) != 0):
        return {
            "status": completed.returncode,
            "error": _extract_error_message(parsed) or "sf command failed",
            "stderr": _redact_credentials_text(stderr[:2000]),
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


def _strip_to_json_start(text: str) -> str:
    """Return ``text`` from the first ``{`` or ``[`` onward.

    sf CLI prepends warning lines like ``›   Warning: update available``
    before its JSON output. ``json.loads`` doesn't tolerate the prefix;
    this helper finds the start of the actual JSON document.

    Returns the empty string if no JSON-start character is found —
    callers should treat that as "no JSON payload" rather than an empty
    success.
    """
    if not text:
        return ""
    obj_start = text.find("{")
    arr_start = text.find("[")
    # Choose whichever comes first (and is non-negative).
    candidates = [pos for pos in (obj_start, arr_start) if pos >= 0]
    if not candidates:
        return ""
    return text[min(candidates):]
