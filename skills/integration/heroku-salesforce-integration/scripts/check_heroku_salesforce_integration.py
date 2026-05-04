#!/usr/bin/env python3
"""Static checks for Heroku ↔ Salesforce integration project structure.

Scans project files for the high-confidence anti-patterns documented in
this skill's references:

  1. `app.json` referencing `heroku-connect` as an add-on (not supported
     for review apps).
  2. Heroku Connect setup notes / docs / config files mentioning
     `heroku-postgresql:hobby-dev` or the deprecated demo-plan name
     against a production-looking project (presence of `Procfile` with
     `web:` process).
  3. Apex `@InvocableMethod` callout class whose Named Credential URL
     points at a `*.herokuapp.com` host — possible AppLink-instead-of-Apex
     candidate.
  4. README / docs that describe both Canvas Signed Request and OAuth
     Web Server Flow on the same app — possible double-auth confusion.

Stdlib only. Heuristic; signal tool not parser.

Usage:
    python3 check_heroku_salesforce_integration.py --src-root .
    python3 check_heroku_salesforce_integration.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Smell 1: app.json with heroku-connect add-on (review apps don't support this)
_HEROKU_CONNECT_ADDON_RE = re.compile(r'"heroku-connect"', re.IGNORECASE)

# Smell 2: deprecated demo-plan name (`hobby-dev`) — replaced by `mini` plan
# but old configs linger. Combined with a Procfile + `web:` we infer "looks
# like a production-ish app".
_HOBBY_DEV_RE = re.compile(r"hobby-dev|heroku-postgresql:hobby", re.IGNORECASE)
_WEB_PROCESS_RE = re.compile(r"^\s*web\s*:", re.IGNORECASE | re.MULTILINE)

# Smell 3: Apex @InvocableMethod with Heroku endpoint — AppLink candidate.
_INVOCABLE_RE = re.compile(r"@InvocableMethod\b", re.IGNORECASE)
_HEROKU_HOST_RE = re.compile(r"\b[\w-]+\.herokuapp\.com\b", re.IGNORECASE)

# Smell 4: doc/README mentions both Canvas auth flows
_SIGNED_REQUEST_RE = re.compile(r"\bsigned\s*request\b", re.IGNORECASE)
_OAUTH_WSF_RE = re.compile(r"\boauth\s*(?:2\.0)?\s*web\s*server\s*flow\b", re.IGNORECASE)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_app_json(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]
    if _HEROKU_CONNECT_ADDON_RE.search(text):
        findings.append(
            f"{path}: app.json declares `heroku-connect` add-on — Connect cannot be "
            "auto-attached to review apps; provision manually per app "
            "(references/gotchas.md § 7)"
        )
    return findings


def _scan_procfile_for_hobby_dev(root: Path) -> list[str]:
    """Look at Procfile + nearby config for the deprecated hobby-dev plan."""
    findings: list[str] = []
    procfile = root / "Procfile"
    if not procfile.exists():
        return findings
    try:
        proc_text = procfile.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    if not _WEB_PROCESS_RE.search(proc_text):
        return findings  # not a web app; skip
    for cfg in [root / "app.json", root / "README.md", root / "README"]:
        if not cfg.exists():
            continue
        try:
            text = cfg.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = _HOBBY_DEV_RE.search(text)
        if m:
            findings.append(
                f"{cfg}:{_line_no(text, m.start())}: references `hobby-dev` / hobby plan — "
                "demo plans (10K-row cap, 10-min polling) are POC-only; "
                "upgrade to Enterprise / Shield for production "
                "(references/gotchas.md § 1)"
            )
    return findings


def _scan_apex_for_heroku_callout(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    if not _INVOCABLE_RE.search(text):
        return findings
    for m in _HEROKU_HOST_RE.finditer(text):
        findings.append(
            f"{path}:{_line_no(text, m.start())}: @InvocableMethod with Heroku endpoint "
            f"`{m.group(0)}` — consider Heroku AppLink (no Apex wrapper needed) "
            "(references/llm-anti-patterns.md § 2)"
        )
    return findings


def _scan_doc_for_double_canvas_auth(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    if _SIGNED_REQUEST_RE.search(text) and _OAUTH_WSF_RE.search(text):
        findings.append(
            f"{path}: mentions both Canvas Signed Request and OAuth Web Server Flow — "
            "ensure the design picks one; mixing produces confused-deputy auth "
            "(references/gotchas.md § 6)"
        )
    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []

    app_json = root / "app.json"
    if app_json.exists():
        findings.extend(_scan_app_json(app_json))

    findings.extend(_scan_procfile_for_hobby_dev(root))

    for apex in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        findings.extend(_scan_apex_for_heroku_callout(apex))

    for doc in list(root.glob("*.md")) + list(root.glob("docs/**/*.md")):
        findings.extend(_scan_doc_for_double_canvas_auth(doc))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a Heroku ↔ Salesforce project for known anti-patterns "
            "(review-app Connect, demo-plan in production-shaped apps, "
            "AppLink-able Apex callouts, double Canvas auth)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the project (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Heroku-Salesforce integration anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
