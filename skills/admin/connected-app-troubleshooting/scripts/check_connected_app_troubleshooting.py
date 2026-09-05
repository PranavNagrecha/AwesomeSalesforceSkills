#!/usr/bin/env python3
"""Static checks for Connected App OAuth troubleshooting artefacts.

Two modes, usable together.

``--manifest-dir <dir>``
    Parse a retrieved or source-format metadata tree with ElementTree and lint:

    Connected app policy combinations that produce the classic failures
    (``*.connectedApp-meta.xml``):

    * ERROR  ``isAdminApproved`` true with neither ``permissionSetName`` nor
             ``profileName`` — the app is pre-authorized for nobody, which is
             runbook row 2 (``references/metadata-examples.md`` § 1).
    * WARN   ``ipRelaxation`` ``ENFORCE`` with no ``ipRanges`` on the app —
             legitimate when the org's profile ranges do the work, and the
             single most common cause of runbook row 7 when they don't.
    * WARN   ``refreshTokenPolicy`` ``zero`` — "works once, then dies"
             (gotcha 1, runbook row 4).
    * WARN   ``isConsumerSecretOptional`` true with
             ``isSecretRequiredForRefreshToken`` not false — the first exchange
             needs no secret and every refresh does (gotcha 14, runbook row 5).

    Diagnosis records (``*diagnosis-record*.yaml`` / ``.yml``):

    * ERROR  a missing required field under ``diagnosis:``.
    * ERROR  a ``root-cause`` outside the documented category set.
    * ERROR  no ``evidence:`` entries, or an entry missing ``query`` or ``result``.
    * WARN   a ``verified-by`` or ``result`` left at the template placeholder.

``<paths...>`` (positional, unchanged)
    Text scan of arbitrary files for hardcoded credentials, ``grant_type=password``
    and Email-shaped JWT ``sub`` claims.

Exit status is 1 if any finding is emitted, 0 otherwise. Stdlib only.

Usage:
    python3 check_connected_app_troubleshooting.py --manifest-dir force-app/main/default
    python3 check_connected_app_troubleshooting.py --src-root .
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"

DIAGNOSIS_TOKEN = "diagnosis-record"

REQUIRED_DIAGNOSIS_FIELDS = (
    "symptom",
    "error",
    "app",
    "user-id",
    "first-failure",
    "root-cause",
    "fix-applied",
    "verified-by",
)

# The categories in references/metadata-examples.md § 1. Keep the two in sync.
ROOT_CAUSES = {
    "callback-url",
    "pre-authorization",
    "flow-not-enabled",
    "refresh-token-policy",
    "secret-required-asymmetry",
    "refresh-token-rotation",
    "ip-restriction",
    "policy-change",
    "user-state",
    "app-blocked",
    "post-auth-authorization",
}


def _strip_ns(tag: str) -> str:
    return tag[len(_NS_TAG):] if tag.startswith(_NS_TAG) else tag


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _child(parent, name: str):
    """Return the named child Element, or None.

    Never use ``a.find(x) or a.find(y)``: an Element with no children is falsy,
    so a present-but-empty element would be silently discarded.
    """
    if parent is None:
        return None
    found = parent.find(f"{_NS_TAG}{name}")
    if found is None:
        found = parent.find(name)
    return found


def _children(parent, name: str) -> list:
    if parent is None:
        return []
    found = parent.findall(f"{_NS_TAG}{name}")
    if not found:
        found = parent.findall(name)
    return found


def _text(parent, name: str) -> str | None:
    el = _child(parent, name)
    if el is None or el.text is None:
        return None
    return el.text.strip()


def _is_true(parent, name: str) -> bool:
    value = _text(parent, name)
    return value is not None and value.lower() == "true"


def _is_false(parent, name: str) -> bool:
    value = _text(parent, name)
    return value is not None and value.lower() == "false"


def _has_nonempty(parent, name: str) -> bool:
    for el in _children(parent, name):
        if el.text is not None and el.text.strip():
            return True
    return False


# --------------------------------------------------------------------------
# Connected app policy combinations
# --------------------------------------------------------------------------


def check_connected_app(path: Path) -> list[tuple[str, str]]:
    """Lint one connectedApp file for the combinations behind the classic failures."""
    issues: list[tuple[str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"{path}: not well-formed XML ({exc})")]
    except OSError as exc:
        return [("ERROR", f"{path}: unreadable ({exc})")]

    if _strip_ns(root.tag) != "ConnectedApp":
        return issues

    label = _text(root, "label") or _text(root, "fullName") or path.stem
    oauth = _child(root, "oauthConfig")
    policy = _child(root, "oauthPolicy")

    # 1. Admin-approved with no grantee. Runbook row 2.
    if oauth is not None and _is_true(oauth, "isAdminApproved"):
        has_permset = _has_nonempty(root, "permissionSetName")
        has_profile = _has_nonempty(root, "profileName")
        if not has_permset and not has_profile:
            issues.append((
                "ERROR",
                f"{path}: `{label}` sets isAdminApproved=true with no non-empty "
                "permissionSetName or profileName. The guide: 'only users with the "
                "appropriate profile or permission set can access the app' — so this "
                "app is pre-authorized for nobody and every user OAuth flow fails. "
                "Runbook row 2 (references/metadata-examples.md § 1).",
            ))

    # 2. ENFORCE with no ipRanges on the app. Runbook row 7.
    if policy is not None:
        relaxation = _text(policy, "ipRelaxation")
        if relaxation == "ENFORCE" and not _children(root, "ipRanges"):
            issues.append((
                "WARN",
                f"{path}: `{label}` has ipRelaxation=ENFORCE and no ipRanges on the "
                "app. ENFORCE 'enforces the IP restrictions configured for the org, "
                "such as the IP ranges assigned to a user profile' — which is correct "
                "when the profile ranges cover the caller, and is runbook row 7 when "
                "they do not. Note in the diagnosis record which layer is doing the "
                "work, and see gotcha 12 before trusting a SourceIp value.",
            ))

        # 3. refreshTokenPolicy zero. Runbook row 4 / gotcha 1.
        if _text(policy, "refreshTokenPolicy") == "zero":
            issues.append((
                "WARN",
                f"{path}: `{label}` has refreshTokenPolicy=zero — 'the refresh token "
                "is invalid immediately. The user can use the current session (access "
                "token) already issued, but can't obtain a new session when the access "
                "token expires.' This is the 'works once, then dies' configuration "
                "(gotcha 1, runbook row 4). Intentional only for a flow that never "
                "renews.",
            ))

    # 4. Secret-required asymmetry. Runbook row 5 / gotcha 14.
    if oauth is not None and _is_true(oauth, "isConsumerSecretOptional"):
        if not _is_false(oauth, "isSecretRequiredForRefreshToken"):
            issues.append((
                "WARN",
                f"{path}: `{label}` sets isConsumerSecretOptional=true while "
                "isSecretRequiredForRefreshToken is not explicitly false (it defaults "
                "to true). The initial token request needs no secret and every refresh "
                "request does, so a public client authenticates once and fails on "
                "renewal. Gotcha 14, runbook row 5.",
            ))

    return issues


# --------------------------------------------------------------------------
# Diagnosis record (narrow, shape-specific YAML reader — stdlib only)
# --------------------------------------------------------------------------

_PAIR_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z][\w-]*)\s*:\s*(?P<value>.*)$")
_ITEM_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<key>[A-Za-z][\w-]*)\s*:\s*(?P<value>.*)$")

_PLACEHOLDERS = (
    "row count",
    "what changed, in which org",
    "the post-fix evidence",
    "paste the response body verbatim",
    "one-line description of what the caller sees",
    "any row naming this app",
    "connected app label, exactly as it appears",
)


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return True
    return any(lowered.startswith(marker) for marker in _PLACEHOLDERS)


def _parse_diagnosis(lines: list[str]) -> tuple[dict[str, str], list[tuple[int, dict[str, str]]]]:
    """Read the documented record shape.

    Returns the scalar keys directly under ``diagnosis:`` and the list items under
    its ``evidence:`` key. Deliberately narrow: it reads this file's shape rather
    than pretending to be a YAML parser. Block scalars (``|``/``>``) are collapsed
    into the key's value so a filled-in field is not mistaken for an empty one.
    """
    fields: dict[str, str] = {}
    evidence: list[tuple[int, dict[str, str]]] = []

    in_diagnosis = False
    in_evidence = False
    diagnosis_indent = 0
    current: dict[str, str] | None = None
    current_line = 0
    item_indent = -1
    block_key: str | None = None
    block_indent = 0
    block_owner: dict[str, str] | None = None

    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if block_key is not None:
            # Inside a block scalar: any line indented past the key belongs to it.
            if stripped and not stripped.startswith("#") and indent > block_indent:
                if block_owner is not None:
                    block_owner[block_key] = (block_owner.get(block_key, "") + " " + stripped).strip()
                continue
            if not stripped:
                continue
            block_key = None
            block_owner = None

        if not stripped or stripped.startswith("#"):
            continue

        top = _PAIR_RE.match(line)
        if top is not None and indent == 0 and not stripped.startswith("-"):
            if top.group("key") == "diagnosis":
                in_diagnosis = True
                in_evidence = False
                diagnosis_indent = 0
                continue
            if in_diagnosis:
                break  # a new top-level key ends the record
            continue

        if not in_diagnosis:
            continue

        item = _ITEM_RE.match(line)
        if item is not None and in_evidence:
            if current is not None:
                evidence.append((current_line, current))
            current = {}
            current_line = number
            item_indent = len(item.group("indent"))
            key, value = item.group("key"), item.group("value").strip()
            if value in ("|", ">", "|-", ">-"):
                current[key] = ""
                block_key, block_indent, block_owner = key, item_indent + 2, current
            else:
                current[key] = value
            continue

        pair = _PAIR_RE.match(line)
        if pair is None:
            continue
        key, value = pair.group("key"), pair.group("value").strip()

        if in_evidence and current is not None and indent > item_indent:
            if value in ("|", ">", "|-", ">-"):
                current[key] = ""
                block_key, block_indent, block_owner = key, indent, current
            else:
                current[key] = value
            continue

        # A key directly under `diagnosis:`.
        if key == "evidence":
            if current is not None:
                evidence.append((current_line, current))
                current = None
            in_evidence = True
            continue

        if in_evidence and indent <= diagnosis_indent + 2:
            # A sibling key after the evidence list closes it.
            if current is not None:
                evidence.append((current_line, current))
                current = None
            in_evidence = False

        if value in ("|", ">", "|-", ">-"):
            fields[key] = ""
            block_key, block_indent, block_owner = key, indent, fields
        else:
            fields[key] = value

    if current is not None:
        evidence.append((current_line, current))
    return fields, evidence


def check_diagnosis_record(path: Path) -> list[tuple[str, str]]:
    """Lint one diagnosis-record YAML file."""
    issues: list[tuple[str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [("ERROR", f"{path}: unreadable ({exc})")]

    fields, evidence = _parse_diagnosis(lines)

    if not fields and not evidence:
        return [(
            "ERROR",
            f"{path}: no `diagnosis:` block found. Start from "
            "templates/connected-app-diagnosis-record.yaml.",
        )]

    for key in REQUIRED_DIAGNOSIS_FIELDS:
        if key not in fields or not fields[key].strip():
            issues.append((
                "ERROR",
                f"{path}: diagnosis record is missing a non-empty `{key}`. "
                f"Required: {', '.join(REQUIRED_DIAGNOSIS_FIELDS)}.",
            ))

    root_cause = fields.get("root-cause", "").strip()
    if root_cause and root_cause not in ROOT_CAUSES:
        issues.append((
            "ERROR",
            f"{path}: root-cause `{root_cause}` is not one of the documented "
            f"categories: {', '.join(sorted(ROOT_CAUSES))}. If the failure genuinely "
            "does not fit, add a row to references/metadata-examples.md § 1 first.",
        ))

    if not evidence:
        issues.append((
            "ERROR",
            f"{path}: no entries under `evidence:`. A diagnosis without recorded "
            "query results is a guess — run the three queries in "
            "references/metadata-examples.md § 2 and record each result, including "
            "zero-row results.",
        ))

    for line_number, entry in evidence:
        label = entry.get("step", "").strip() or f"line {line_number}"
        for key in ("query", "result"):
            if key not in entry or not entry[key].strip():
                issues.append((
                    "ERROR",
                    f"{path}:{line_number}: evidence entry `{label}` has no non-empty "
                    f"`{key}`. Every evidence row needs both the query that was run and "
                    "what it returned.",
                ))
        result = entry.get("result", "")
        if result.strip() and _is_placeholder(result):
            issues.append((
                "WARN",
                f"{path}:{line_number}: evidence entry `{label}` still holds the "
                "template placeholder in `result`.",
            ))

    for key in ("verified-by", "fix-applied", "symptom", "error", "app"):
        value = fields.get(key, "")
        if value.strip() and _is_placeholder(value):
            issues.append((
                "WARN",
                f"{path}: `{key}` still holds the template placeholder text.",
            ))

    return issues


# --------------------------------------------------------------------------
# Source scan (unchanged behaviour)
# --------------------------------------------------------------------------

# Salesforce Consumer Key shape: starts with `3MV`, 85 chars total.
_CONSUMER_KEY_RE = re.compile(r"\b3MV[A-Za-z0-9._]{80,90}\b")
# Refresh token shape: starts with `5A`, length varies.
_REFRESH_TOKEN_RE = re.compile(r"\b5A[a-zA-Z0-9._]{40,200}\b")
_GRANT_TYPE_PASSWORD_RE = re.compile(r"grant_type\s*[=:]\s*['\"]?password['\"]?", re.IGNORECASE)
_JWT_SUB_EMAIL_RE = re.compile(r"['\"]sub['\"]\s*:\s*['\"][^'\"@]+@[^'\"]+['\"]")


def _scan_source_for_secrets(path: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    for m in _CONSUMER_KEY_RE.finditer(text):
        findings.append((
            "ERROR",
            f"{path}:{_line_no(text, m.start())}: literal Salesforce Consumer Key in "
            "source — credentials in source control. Use environment variables, a "
            "secret store, or a Named Credential "
            "(references/llm-anti-patterns.md § 3).",
        ))

    for m in _REFRESH_TOKEN_RE.finditer(text):
        findings.append((
            "ERROR",
            f"{path}:{_line_no(text, m.start())}: literal-shaped refresh token in "
            "source — secret in source control. Move it to a secret store "
            "(references/llm-anti-patterns.md § 3).",
        ))

    for m in _GRANT_TYPE_PASSWORD_RE.finditer(text):
        findings.append((
            "WARN",
            f"{path}:{_line_no(text, m.start())}: `grant_type=password` "
            "(Username-Password OAuth flow) — deprecated for new integrations. Use "
            "JWT Bearer (server-to-server) or Web Server flow "
            "(references/llm-anti-patterns.md § 2).",
        ))

    for m in _JWT_SUB_EMAIL_RE.finditer(text):
        findings.append((
            "WARN",
            f"{path}:{_line_no(text, m.start())}: JWT `sub` claim looks like an Email "
            "(`user@domain`); JWT Bearer requires User.Username, which often differs "
            "(references/llm-anti-patterns.md § 5).",
        ))

    return findings


def scan_source_tree(root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for ext in ("*.py", "*.js", "*.ts", "*.cls", "*.trigger", "*.json",
                "*.yaml", "*.yml", "*.env", "*.sh"):
        for f in sorted(root.rglob(ext)):
            if DIAGNOSIS_TOKEN in f.name.lower():
                continue
            findings.extend(_scan_source_for_secrets(f))
    return findings


# --------------------------------------------------------------------------


def scan_manifest_dir(root: Path) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    apps = sorted(root.rglob("*.connectedApp-meta.xml")) + sorted(root.rglob("*.connectedApp"))
    for app in apps:
        issues.extend(check_connected_app(app))

    records: list[Path] = []
    for pattern in ("*.yaml", "*.yml"):
        for candidate in sorted(root.rglob(pattern)):
            if DIAGNOSIS_TOKEN in candidate.name.lower():
                records.append(candidate)
    for record in records:
        issues.extend(check_diagnosis_record(record))

    if not apps and not records:
        issues.append((
            "WARN",
            f"{root}: no *.connectedApp-meta.xml and no *{DIAGNOSIS_TOKEN}*.yaml found. "
            "Point --manifest-dir at the retrieved metadata tree, or at the folder "
            "holding the diagnosis record.",
        ))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Lint Connected App policy combinations behind the classic OAuth "
            "failures, the diagnosis record produced by this skill, and integration "
            "source for hardcoded credentials."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        help="Retrieved or source-format metadata tree, or the folder holding the "
             "diagnosis-record YAML.",
    )
    parser.add_argument(
        "--src-root",
        help="Root of the integration source to scan for hardcoded credentials.",
    )
    args = parser.parse_args()

    if not args.manifest_dir and not args.src_root:
        parser.error("provide --manifest-dir, --src-root, or both")

    issues: list[tuple[str, str]] = []

    for label, value, scanner in (
        ("--manifest-dir", args.manifest_dir, scan_manifest_dir),
        ("--src-root", args.src_root, scan_source_tree),
    ):
        if not value:
            continue
        path = Path(value)
        if not path.exists():
            issues.append(("ERROR", f"{label} does not exist: {path}"))
            continue
        if not path.is_dir():
            issues.append(("ERROR", f"{label} is not a directory: {path}"))
            continue
        issues.extend(scanner(path))

    if not issues:
        print("OK: no connected-app policy, diagnosis-record, or credential issues found.")
        return 0

    errors = 0
    for level, message in issues:
        if level == "ERROR":
            errors += 1
        print(f"{level}: {message}", file=sys.stderr)

    print(
        f"\n{len(issues)} finding(s), {errors} error(s).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
