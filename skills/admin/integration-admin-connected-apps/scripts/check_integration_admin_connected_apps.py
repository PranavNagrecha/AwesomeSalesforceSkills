#!/usr/bin/env python3
"""Checker for the integration-admin-connected-apps skill.

Lints the two artefacts this skill produces:

1. ConnectedApp metadata (``*.connectedApp`` / ``*.connectedApp-meta.xml``) for the
   OAuth policy shapes that break a running integration:

   * ERROR - ``oauthPolicy/ipRelaxation`` is ``BYPASS``. The Metadata API Developer
     Guide describes ``BYPASS`` as "Allows a user to run this app without org IP
     restrictions", which removes the org's network control entirely.
   * ERROR - ``oauthConfig/isAdminApproved`` is ``true`` with no ``permissionSetName``
     and no ``profileName``. Both grantee fields carry "To use this field, the
     isAdminApproved field on the ConnectedAppOauthConfig subtype must be set to
     true"; without one, the app is pre-authorized for nobody.
   * WARN  - ``oauthPolicy/refreshTokenPolicy`` is ``infinite`` (the guide's default)
     on an admin-approved app: "the refresh token is used indefinitely, unless
     revoked by the user or Salesforce admin."
   * WARN  - ``oauthConfig/scopes`` includes ``Full``.
   * WARN  - ``oauthConfig/oauthClientCredentialUser`` is set (must be a dedicated
     API-only integration user).

2. The periodic review checklist YAML (a file whose name contains
   ``connected-app-review``). Every entry under ``apps:`` must carry ``owner``,
   ``last-reviewed`` and ``token-count-query-run``.

stdlib only - no pip dependencies, no YAML library.

Usage:
    python3 check_integration_admin_connected_apps.py --manifest-dir force-app/main/default
    python3 check_integration_admin_connected_apps.py --manifest-dir templates

Exit codes: 0 = clean or warnings only, 1 = at least one ERROR (or a bad --manifest-dir).
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

APP_SUFFIXES = ("*.connectedApp", "*.connectedApp-meta.xml")
CHECKLIST_TOKEN = "connected-app-review"
CHECKLIST_SUFFIXES = ("*.yaml", "*.yml")
REQUIRED_APP_KEYS = ("owner", "last-reviewed", "token-count-query-run")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint ConnectedApp OAuth policy metadata and the periodic review "
            "checklist produced by the integration-admin-connected-apps skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    return parser.parse_args()


# --------------------------------------------------------------------------
# XML helpers
# --------------------------------------------------------------------------

def _namespace(root: ET.Element) -> str:
    """Return the '{uri}' prefix for this document, or '' when unqualified."""
    if root.tag.startswith("{"):
        return root.tag.split("}")[0] + "}"
    return ""


def _child(parent, ns: str, name: str):
    """Find one child element by local name.

    A leaf Element is falsy in ElementTree, so ``parent.find(a) or parent.find(b)``
    silently discards a real match. Always compare against None.
    """
    if parent is None:
        return None
    found = parent.find(f"{ns}{name}")
    if found is not None:
        return found
    return None


def _text(parent, ns: str, name: str) -> str:
    """Return the stripped text of a child element, or '' when absent/empty."""
    node = _child(parent, ns, name)
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _texts(parent, ns: str, name: str) -> list[str]:
    """Return the stripped text of every matching child element."""
    if parent is None:
        return []
    out: list[str] = []
    for node in parent.findall(f"{ns}{name}"):
        if node.text is not None and node.text.strip():
            out.append(node.text.strip())
    return out


# --------------------------------------------------------------------------
# ConnectedApp checks
# --------------------------------------------------------------------------

def check_connected_app(app_file: Path) -> list[tuple[str, str]]:
    """Return (level, message) tuples for one ConnectedApp metadata file."""
    issues: list[tuple[str, str]] = []

    try:
        root = ET.parse(app_file).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"{app_file}: not well-formed XML ({exc})")]

    ns = _namespace(root)
    name = app_file.name.split(".")[0]

    oauth_config = _child(root, ns, "oauthConfig")
    oauth_policy = _child(root, ns, "oauthPolicy")

    if oauth_config is None and oauth_policy is None:
        # Not an OAuth-enabled connected app - nothing this skill governs.
        return issues

    # --- ipRelaxation -----------------------------------------------------
    ip_relaxation = _text(oauth_policy, ns, "ipRelaxation")
    if ip_relaxation == "BYPASS":
        issues.append((
            "ERROR",
            f"'{name}': oauthPolicy/ipRelaxation is BYPASS, which lets the app run "
            "without the org's IP restrictions. Use ENFORCE with the caller's egress "
            "ranges on the org trusted-IP list, or document the exception.",
        ))
    elif oauth_policy is not None and not ip_relaxation:
        issues.append((
            "WARN",
            f"'{name}': oauthPolicy has no ipRelaxation value. The field is Required "
            "and defaults to ENFORCE - set it explicitly so the policy is reviewable.",
        ))

    # --- isAdminApproved without a grantee --------------------------------
    is_admin_approved = _text(oauth_config, ns, "isAdminApproved").lower() == "true"
    permission_sets = [v for v in _texts(root, ns, "permissionSetName") if v]
    profiles = [v for v in _texts(root, ns, "profileName") if v]

    if is_admin_approved and not permission_sets and not profiles:
        issues.append((
            "ERROR",
            f"'{name}': isAdminApproved is true but the file carries no non-empty "
            "permissionSetName or profileName. The app deploys cleanly and "
            "pre-authorizes nobody - every OAuth attempt, including the admin's, fails.",
        ))

    # --- refreshTokenPolicy ----------------------------------------------
    refresh_policy = _text(oauth_policy, ns, "refreshTokenPolicy")
    if is_admin_approved and refresh_policy == "infinite":
        issues.append((
            "WARN",
            f"'{name}': refreshTokenPolicy is 'infinite' on an admin-approved app, so "
            "its refresh token never expires on its own. Set specific_lifetime:n:UNIT "
            "or specific_inactivity:n:UNIT, or record why indefinite is acceptable.",
        ))
    elif oauth_policy is not None and not refresh_policy:
        issues.append((
            "WARN",
            f"'{name}': oauthPolicy has no refreshTokenPolicy value. The field is "
            "Required and defaults to 'infinite'.",
        ))

    # --- scope and principal hygiene --------------------------------------
    scopes = _texts(oauth_config, ns, "scopes")
    if any(s.lower() == "full" for s in scopes):
        issues.append((
            "WARN",
            f"'{name}': OAuth scope 'Full' is granted, which carries every permission "
            "the running user holds. Narrow to the scopes the integration uses.",
        ))

    cc_user = _text(oauth_config, ns, "oauthClientCredentialUser")
    if cc_user:
        issues.append((
            "WARN",
            f"'{name}': client-credentials run-as user is '{cc_user}'. Confirm this is "
            "a dedicated API-only integration user, not a person or an admin.",
        ))

    return issues


# --------------------------------------------------------------------------
# Review checklist checks (minimal, shape-specific YAML reader)
# --------------------------------------------------------------------------

_ITEM_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<key>[A-Za-z][\w-]*)\s*:\s*(?P<value>.*)$")
_PAIR_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z][\w-]*)\s*:\s*(?P<value>.*)$")


def _parse_app_entries(lines: list[str]) -> list[tuple[int, dict[str, str]]]:
    """Extract the list items under a top-level `apps:` key.

    Returns (line number, {key: value}) pairs. Deliberately narrow: it reads the
    documented checklist shape rather than pretending to be a YAML parser.
    """
    entries: list[tuple[int, dict[str, str]]] = []
    in_apps = False
    current: dict[str, str] | None = None
    current_line = 0
    item_indent = -1

    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        top_level = _PAIR_RE.match(line)
        if top_level is not None and not top_level.group("indent") and not line.lstrip().startswith("-"):
            if top_level.group("key") == "apps":
                in_apps = True
                continue
            if in_apps:
                break  # a new top-level key ends the apps block
            continue

        if not in_apps:
            continue

        item = _ITEM_RE.match(line)
        if item is not None:
            if current is not None:
                entries.append((current_line, current))
            current = {item.group("key"): item.group("value").strip()}
            current_line = number
            item_indent = len(item.group("indent"))
            continue

        pair = _PAIR_RE.match(line)
        if pair is not None and current is not None and len(pair.group("indent")) > item_indent:
            current[pair.group("key")] = pair.group("value").strip()

    if current is not None:
        entries.append((current_line, current))
    return entries


def check_review_checklist(path: Path) -> list[tuple[str, str]]:
    """Return (level, message) tuples for one review-checklist YAML file."""
    issues: list[tuple[str, str]] = []

    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError as exc:
        return [("ERROR", f"{path}: unreadable ({exc})")]

    entries = _parse_app_entries(lines)
    if not entries:
        issues.append((
            "ERROR",
            f"{path}: no entries found under a top-level 'apps:' key. The review "
            "checklist needs one row per connected app.",
        ))
        return issues

    for line_number, entry in entries:
        label = entry.get("name") or entry.get("app") or f"entry at line {line_number}"
        missing = [key for key in REQUIRED_APP_KEYS if not entry.get(key)]
        if missing:
            issues.append((
                "ERROR",
                f"{path}:{line_number}: review entry '{label}' is missing "
                f"{', '.join(missing)}. Each app row needs an owner, the date it was "
                "last reviewed, and the date the OauthToken count query was actually run.",
            ))
        if entry.get("token-count-query-run") and not entry.get("token-count"):
            issues.append((
                "WARN",
                f"{path}:{line_number}: review entry '{label}' records when the token "
                "count query ran but not the count it returned. Record the number - "
                "OauthToken stops returning rows at 2,500, so the count is the only "
                "way a later reviewer can tell a real zero from a truncated result.",
            ))

    return issues


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def collect_issues(manifest_dir: Path) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []

    if not manifest_dir.exists() or not manifest_dir.is_dir():
        return [("ERROR", f"Manifest directory not found: {manifest_dir}")]

    seen: set[Path] = set()
    for pattern in APP_SUFFIXES:
        for app_file in sorted(manifest_dir.rglob(pattern)):
            resolved = app_file.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            issues.extend(check_connected_app(app_file))

    for pattern in CHECKLIST_SUFFIXES:
        for yaml_file in sorted(manifest_dir.rglob(pattern)):
            if CHECKLIST_TOKEN not in yaml_file.name.lower():
                continue
            resolved = yaml_file.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            issues.extend(check_review_checklist(yaml_file))

    if not seen:
        issues.append((
            "WARN",
            f"No .connectedApp metadata and no *{CHECKLIST_TOKEN}*.yaml checklist found "
            f"under {manifest_dir} - nothing was checked.",
        ))

    return issues


def main() -> int:
    args = parse_args()
    issues = collect_issues(Path(args.manifest_dir))

    errors = [msg for level, msg in issues if level == "ERROR"]
    warnings = [msg for level, msg in issues if level == "WARN"]

    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in warnings:
        print(f"WARN: {message}", file=sys.stderr)

    if not issues:
        print("No connected-app policy or review-checklist issues found.")
        return 0

    print(
        f"{len(errors)} error(s), {len(warnings)} warning(s).",
        file=sys.stderr,
    )
    if errors:
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
