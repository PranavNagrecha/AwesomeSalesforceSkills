#!/usr/bin/env python3
"""Checker script for the postman-for-salesforce skill.

Audits a `.postman_collection.json` (and optional `.postman_environment.json`)
for the most common Salesforce-Postman authoring mistakes covered in this
skill's gotchas:

- Pre-request script that calls `/services/oauth2/token` without checking a
  cached `accessTokenExpiry` (every-request auth).
- JWT bearer flow with `aud` set to a token-endpoint URL instead of the
  login URL (contains `/services/oauth2/token`).
- Hard-coded `https://*.salesforce.com` or `https://*.force.com` URLs
  outside `{{instanceUrl}}` substitution.
- Hard-coded API version path without ``{{apiVersion}}`` substitution.
- Bulk API 2.0 chained upload using a method other than `PUT`.
- Tests that thread state via `pm.variables.set` instead of
  `pm.collectionVariables.set` (likely re-run breakage).
- Secrets stored as default-value environment variables instead of Vault
  references (`{{vault:KEY}}`).

Stdlib only — no pip dependencies.

Usage:
    python3 check_postman_for_salesforce.py --collection my.postman_collection.json
    python3 check_postman_for_salesforce.py --collection coll.json --env env.json --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


HARD_HOST_RE = re.compile(
    r"https?://[a-zA-Z0-9\-.]+\.(salesforce|force|cloudforce)\.com",
)
HARD_API_VERSION_RE = re.compile(
    r"/services/data/v\d+\.\d+/",
)
TOKEN_ENDPOINT_RE = re.compile(
    r"/services/oauth2/token",
)
JWT_AUD_RE = re.compile(
    r"aud['\"]?\s*[:=]\s*['\"`]([^'\"`]+)['\"`]",
)
PM_VAR_SET_RE = re.compile(
    r"\bpm\.variables\.set\s*\(",
)
PM_COLLVAR_SET_RE = re.compile(
    r"\bpm\.collectionVariables\.set\s*\(",
)
ACCESS_TOKEN_REFRESH_RE = re.compile(
    r"sendRequest[^)]*services/oauth2/token",
    re.IGNORECASE,
)
EXPIRY_CHECK_RE = re.compile(
    r"accessTokenExpiry|expires_in|tokenExpiry",
)
BULK_INGEST_PUT_HINT_RE = re.compile(
    r"jobs/ingest/[^\"'`]*/?",
)
SENSITIVE_KEY_NAMES = {
    "clientSecret", "client_secret", "jwtPrivateKey", "private_key",
    "password", "passwordWithToken",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a Postman collection for Salesforce-specific mistakes.",
    )
    parser.add_argument(
        "--collection",
        default="postman_collection.json",
        help="Path to the .postman_collection.json file.",
    )
    parser.add_argument(
        "--env",
        default=None,
        help="Optional path to a .postman_environment.json for secret-storage checks.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on any finding (default: only on errors).",
    )
    return parser.parse_args()


def iter_items(items: list) -> list:
    """Recurse Postman v2.1 folder structure, yielding leaf request items."""
    out = []
    for it in items or []:
        if isinstance(it, dict):
            if it.get("item"):
                out.extend(iter_items(it.get("item", [])))
            elif it.get("request"):
                out.append(it)
    return out


def event_scripts(events: list) -> list[tuple[str, str]]:
    """Extract (event-listen, joined-script-text) pairs."""
    out: list[tuple[str, str]] = []
    for ev in events or []:
        listen = ev.get("listen", "")
        script_obj = ev.get("script", {})
        exec_lines = script_obj.get("exec", [])
        if isinstance(exec_lines, list):
            text = "\n".join(exec_lines)
        else:
            text = str(exec_lines)
        out.append((listen, text))
    return out


def check_collection(coll_path: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    try:
        coll = json.loads(coll_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        findings.append(("ERROR", f"{coll_path}: cannot parse — {e}"))
        return findings

    # Collection-level events.
    coll_events = coll.get("event", [])
    coll_scripts_text = "\n".join(text for _, text in event_scripts(coll_events))

    if ACCESS_TOKEN_REFRESH_RE.search(coll_scripts_text):
        if not EXPIRY_CHECK_RE.search(coll_scripts_text):
            findings.append((
                "WARN",
                f"{coll_path}: collection-level pre-request script calls /services/oauth2/token "
                "without an accessTokenExpiry / expires_in cache check. Will re-auth on every "
                "request and exhaust per-user login limits.",
            ))

    # Look for JWT aud claim inside pre-request scripts.
    for match in JWT_AUD_RE.finditer(coll_scripts_text):
        value = match.group(1)
        if "{{" in value:
            continue
        if TOKEN_ENDPOINT_RE.search(value):
            findings.append((
                "ERROR",
                f"{coll_path}: JWT bearer 'aud' claim contains the token endpoint path "
                f"({value!r}). Salesforce JWT 'aud' must be the login URL only "
                "(e.g. https://login.salesforce.com), no /services/oauth2/token suffix.",
            ))

    # Walk requests.
    items = iter_items(coll.get("item", []))
    for it in items:
        name = it.get("name", "<unnamed>")
        req = it.get("request", {}) or {}
        url = req.get("url", "")
        if isinstance(url, dict):
            url_text = url.get("raw", "")
        else:
            url_text = str(url)
        method = (req.get("method") or "GET").upper()

        # Hard-coded Salesforce host.
        for m in HARD_HOST_RE.finditer(url_text):
            findings.append((
                "ERROR",
                f"{coll_path}: request '{name}' uses hard-coded Salesforce host "
                f"{m.group(0)!r}. Use {{{{instanceUrl}}}} (set by the pre-request script).",
            ))

        # Hard-coded API version.
        if HARD_API_VERSION_RE.search(url_text) and "{{apiVersion}}" not in url_text:
            findings.append((
                "WARN",
                f"{coll_path}: request '{name}' has a literal API version path. "
                "Use /services/data/{{apiVersion}}/... for portability.",
            ))

        # Bulk API 2.0 upload step using non-PUT.
        if "/jobs/ingest/" in url_text and "/batches" not in url_text:
            # The "upload" step is PUT to the contentUrl; if the URL ends in `/...batches` or
            # references {{bulkContentUrl}}, treat as upload.
            is_upload = ("{{bulkContentUrl}}" in url_text or url_text.endswith("/batches"))
            if is_upload and method != "PUT":
                findings.append((
                    "ERROR",
                    f"{coll_path}: request '{name}' looks like a Bulk API 2.0 upload step "
                    f"but uses {method}. The upload step must be PUT.",
                ))

        # Walk per-request events.
        for listen, text in event_scripts(it.get("event", [])):
            # JWT aud at request scope.
            for m in JWT_AUD_RE.finditer(text):
                value = m.group(1)
                if "{{" in value:
                    continue
                if TOKEN_ENDPOINT_RE.search(value):
                    findings.append((
                        "ERROR",
                        f"{coll_path}: JWT 'aud' in request '{name}' script contains "
                        f"the token endpoint path ({value!r}). Use the login URL only.",
                    ))
            # pm.variables.set vs collection.
            if PM_VAR_SET_RE.search(text) and not PM_COLLVAR_SET_RE.search(text):
                # Heuristic: only warn when the value being set looks chain-significant.
                if re.search(r"pm\.variables\.set\s*\(\s*['\"`](bulk|job|content|run|ref)", text, re.IGNORECASE):
                    findings.append((
                        "WARN",
                        f"{coll_path}: request '{name}' threads chain state via "
                        "pm.variables.set (run-scoped). Use pm.collectionVariables.set so "
                        "the chain is re-runnable.",
                    ))

    return findings


def check_environment(env_path: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    try:
        env = json.loads(env_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        findings.append(("ERROR", f"{env_path}: cannot parse — {e}"))
        return findings

    for var in env.get("values", []):
        key = var.get("key", "")
        value = var.get("value", "")
        if key in SENSITIVE_KEY_NAMES and value and not value.startswith("{{vault:"):
            findings.append((
                "WARN",
                f"{env_path}: variable {key!r} has an inline value. Per-developer "
                "secrets should reference Postman Vault via {{vault:KEY}}, not be "
                "stored in the synced environment.",
            ))

    return findings


def main() -> int:
    args = parse_args()
    coll_path = Path(args.collection)
    if not coll_path.exists():
        # Skill is template-shaped; if the input doesn't exist, return 0 gracefully so the
        # checker can be exercised against partial inputs without failing CI hooks.
        print(f"No Postman collection at {coll_path} — nothing to check.")
        return 0

    findings = check_collection(coll_path)

    if args.env:
        env_path = Path(args.env)
        if env_path.exists():
            findings.extend(check_environment(env_path))
        else:
            findings.append(("WARN", f"--env path not found: {env_path}"))

    if not findings:
        print("No issues found.")
        return 0

    errors = [f for f in findings if f[0] == "ERROR"]
    warns = [f for f in findings if f[0] == "WARN"]

    for severity, message in findings:
        stream = sys.stderr if severity == "ERROR" else sys.stdout
        print(f"{severity}: {message}", file=stream)

    if errors:
        return 1
    if args.strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
