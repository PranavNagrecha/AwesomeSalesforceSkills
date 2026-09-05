#!/usr/bin/env python3
"""Static checks for a sandbox post-refresh automation package.

Scans a Salesforce metadata directory and validates the five artefacts this
skill produces against the platform behaviours documented in
``references/gotchas.md``:

  1. SandboxPostCopy class  -- implements the interface, is ``global``, and has
     an explicit no-arg constructor (Apex Reference Guide L228955-228960: the
     copy process instantiates the class with the no-arg constructor, and
     constructors with arguments "won't be used by the sandbox copy process").
  2. Test class             -- calls ``Test.testSandboxPostCopyScript`` and uses
     the 5-arg ``RunAsAutoProcUser`` overload (L241180-241184).
  3. CronTrigger sweep      -- the abort query covers all six live ``State``
     values, not the usual three (Object Reference L86799-86811).
  4. Checklist JSON         -- ``*post-refresh-checklist*.json`` carries every
     required step, each with an ``owner`` and a ``verify``.
  5. EmailAdministration    -- the ``.settings`` file uses only elements that
     exist on the ``EmailAdministrationSettings`` metadata type
     (api_meta L114872-114994); in particular it has no deliverability
     access-level element, because no such element exists.

Stdlib only. Exit 0 when clean, 1 when there are findings.

Usage:
    python3 check_sandbox_post_refresh_automation.py --manifest-dir force-app/main/default
    python3 check_sandbox_post_refresh_automation.py --manifest-dir . --strict
    python3 check_sandbox_post_refresh_automation.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "http://soap.sforce.com/2006/04/metadata"

# --- Grounded constants -------------------------------------------------

# CronTrigger.State values that mean the job will still run.
# Object Reference L86799-86811. COMPLETE / ERROR / DELETED are terminal.
LIVE_CRON_STATES = frozenset(
    {"WAITING", "ACQUIRED", "EXECUTING", "PAUSED", "BLOCKED", "PAUSED_BLOCKED"}
)

# The complete EmailAdministrationSettings field list, api_meta L114872-114994.
# There is deliberately no access-level / deliverability element here: the type
# does not have one (references/gotchas.md section 5).
EMAIL_ADMIN_ELEMENTS = frozenset(
    {
        "enableComplianceBcc",
        "enableEmailConsentManagement",
        "enableEmailSenderIdCompliance",
        "enableEmailSpfCompliance",
        "enableEmailToSalesforce",
        "enableEmailWorkflowApproval",
        "enableEnhancedEmailEnabled",
        "enableHandleBouncedEmails",
        "enableHtmlEmail",
        "enableInternationalEmailAddresses",
        "enableListEmailLogActivities",
        "enableResendBouncedEmails",
        "enableRestrictTlsToDomains",
        "enableSendThroughGmailPref",
        "enableSendViaExchangePref",
        "enableSendViaGmailPref",
        "enableUseOrgFootersForExtTrans",
        "sendMassEmailNotification",
        "sendTextOnlySystemEmails",
    }
)

# One step per concern in SKILL.md's runApexClass body.
REQUIRED_CHECKLIST_STEPS = (
    "mask-user-email",
    "deactivate-users",
    "abort-scheduled-jobs",
    "scrub-integration-config",
    "reseed-reference-data",
    "apply-environment-config",
)
VALID_OWNERS = frozenset({"apex", "pipeline", "manual"})

# --- Patterns -----------------------------------------------------------

_IMPLEMENTS_RE = re.compile(
    r"\b(public|global|private|protected)\s+"
    r"(?:virtual\s+|abstract\s+|with\s+sharing\s+|without\s+sharing\s+|inherited\s+sharing\s+)*"
    r"class\s+(\w+)\s+implements\s+([^{]*?)\bSandboxPostCopy\b",
    re.IGNORECASE,
)
_RUN_APEX_RE = re.compile(
    r"\b(public|global|private|protected)\s+void\s+runApexClass\s*\(",
    re.IGNORECASE,
)
_TEST_CALL_RE = re.compile(
    r"(?:System\s*\.\s*)?Test\s*\.\s*testSandboxPostCopyScript\s*\(",
    re.IGNORECASE,
)
_ABORT_RE = re.compile(r"\bSystem\s*\.\s*abortJob\s*\(", re.IGNORECASE)
_CRON_QUERY_RE = re.compile(r"FROM\s+CronTrigger\b(.{0,400}?)\]", re.IGNORECASE | re.DOTALL)
_STATE_LITERAL_RE = re.compile(r"'([A-Z_]+)'")
_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)


def _strip_comments(text: str) -> str:
    return _COMMENT_RE.sub(" ", text)


def _find_child(element: ET.Element, tag: str) -> ET.Element | None:
    """Namespace-tolerant single-child lookup.

    Never rely on ``a.find(x) or a.find(y)``: an Element with no children is
    falsy, so a real match would be discarded. Always compare to None.
    """
    found = element.find(tag)
    if found is None:
        found = element.find(f"{{{MDAPI_NS}}}{tag}")
    return found


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _no_arg_constructor(text: str, class_name: str) -> bool:
    pattern = re.compile(
        r"\b(?:public|global|private|protected)\s+" + re.escape(class_name) + r"\s*\(\s*\)",
        re.IGNORECASE,
    )
    return pattern.search(text) is not None


def _balanced_args(call_text: str, start: int) -> list[str] | None:
    """Split the argument list of a call whose '(' is at index start-1."""
    depth = 0
    args: list[str] = []
    current: list[str] = []
    i = start
    while i < len(call_text):
        ch = call_text[i]
        if ch in "([":
            depth += 1
            current.append(ch)
        elif ch in ")]":
            if depth == 0:
                args.append("".join(current).strip())
                return [a for a in args if a != ""]
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    return None


# --- Check 1 + 2 + 3: Apex ---------------------------------------------


def check_apex(manifest_dir: Path) -> tuple[list[str], bool, bool]:
    """Returns (findings, saw_post_copy_class, saw_test_call)."""
    findings: list[str] = []
    saw_class = False
    saw_test = False

    for cls in sorted(manifest_dir.rglob("*.cls")):
        try:
            raw = cls.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            findings.append(f"{cls}: unreadable ({exc})")
            continue
        text = _strip_comments(raw)

        impl = _IMPLEMENTS_RE.search(text)
        if impl is not None:
            saw_class = True
            modifier, class_name = impl.group(1).lower(), impl.group(2)

            if modifier != "global":
                findings.append(
                    f"{cls}: class `{class_name}` implements SandboxPostCopy with "
                    f"`{modifier}` access. Every Salesforce sample uses `global` "
                    "(Apex Reference Guide L228952) — see references/gotchas.md section 1."
                )

            method = _RUN_APEX_RE.search(text)
            if method is None:
                findings.append(
                    f"{cls}: class `{class_name}` implements SandboxPostCopy but no "
                    "`runApexClass(...)` method was found."
                )
            elif method.group(1).lower() != "global":
                findings.append(
                    f"{cls}: `runApexClass` is declared `{method.group(1).lower()}`; "
                    "the interface implementation should be `global` "
                    "(Apex Reference Guide L228975)."
                )

            if not _no_arg_constructor(text, class_name):
                findings.append(
                    f"{cls}: `{class_name}` has no explicit no-arg constructor. "
                    "\"Implementations of SandboxPostCopy must have a no-arg constructor. "
                    "This constructor is used during the sandbox copy process\" "
                    "(Apex Reference Guide L228955-228956). A class whose only constructor "
                    "takes arguments cannot be instantiated by the copy."
                )

        # Check 2 — the test call and its overload.
        for m in _TEST_CALL_RE.finditer(text):
            saw_test = True
            args = _balanced_args(text, m.end())
            if args is None:
                findings.append(
                    f"{cls}: could not parse the argument list of "
                    "`Test.testSandboxPostCopyScript(...)`."
                )
            elif len(args) < 5:
                findings.append(
                    f"{cls}: `Test.testSandboxPostCopyScript` called with {len(args)} "
                    "arguments. Use the 5-arg overload with RunAsAutoProcUser = true — "
                    "the 4-arg form runs as the test initiator and cannot reproduce the "
                    "restricted Automated Process user (Apex Reference Guide "
                    "L241180-241184); see references/gotchas.md section 13."
                )
            elif args[4].strip().lower() != "true":
                findings.append(
                    f"{cls}: `Test.testSandboxPostCopyScript` passes "
                    f"RunAsAutoProcUser = `{args[4].strip()}`. Pass `true` so the script is "
                    "tested with the permissions the copy process actually uses "
                    "(Apex Reference Guide L241180-241184)."
                )

        # Check 3 — the CronTrigger sweep covers all six live states.
        if _ABORT_RE.search(text) or "CronTrigger" in text:
            for q in _CRON_QUERY_RE.finditer(text):
                clause = q.group(1)
                if "State" not in clause:
                    continue
                states = {s for s in _STATE_LITERAL_RE.findall(clause)}
                cron_states = states & (
                    LIVE_CRON_STATES | {"COMPLETE", "ERROR", "DELETED"}
                )
                if not cron_states:
                    continue
                missing = sorted(LIVE_CRON_STATES - cron_states)
                if missing:
                    findings.append(
                        f"{cls}: CronTrigger query filters on "
                        f"{sorted(cron_states)} and misses live state(s) "
                        f"{missing}. Six of the nine documented State values mean the job "
                        "will still run (Object Reference L86799-86811); only COMPLETE, "
                        "ERROR and DELETED are terminal. See references/gotchas.md "
                        "section 12."
                    )

    if saw_class and not saw_test:
        findings.append(
            f"{manifest_dir}: a SandboxPostCopy implementation exists but nothing in the "
            "tree calls `Test.testSandboxPostCopyScript`. The class needs a test to reach "
            "production at all, and only that harness exercises the post-copy path "
            "(references/gotchas.md section 8)."
        )

    return findings, saw_class, saw_test


# --- Check 4: checklist JSON -------------------------------------------


def check_checklist(manifest_dir: Path, search_root: Path) -> tuple[list[str], bool]:
    findings: list[str] = []
    candidates = sorted(
        set(search_root.rglob("*post-refresh-checklist*.json"))
        | set(manifest_dir.rglob("*post-refresh-checklist*.json"))
    )
    if not candidates:
        return [], False

    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"{path}: not valid JSON ({exc}).")
            continue

        if not isinstance(data, dict):
            findings.append(f"{path}: top level must be an object.")
            continue

        for key in ("sandboxName", "postCopyClass", "runAsAutoProcUser", "steps"):
            if key not in data:
                findings.append(f"{path}: missing required top-level key `{key}`.")

        if data.get("runAsAutoProcUser") is False:
            findings.append(
                f"{path}: `runAsAutoProcUser` is false. The tests then run as the test "
                "initiator rather than the identity the refresh uses "
                "(references/gotchas.md section 13)."
            )

        steps = data.get("steps")
        if not isinstance(steps, list):
            findings.append(f"{path}: `steps` must be a list.")
            continue

        seen: set[str] = set()
        for index, step in enumerate(steps):
            where = f"{path}: steps[{index}]"
            if not isinstance(step, dict):
                findings.append(f"{where}: must be an object.")
                continue
            step_id = step.get("id")
            if not step_id:
                findings.append(f"{where}: missing `id`.")
                continue
            seen.add(step_id)
            owner = step.get("owner")
            if owner not in VALID_OWNERS:
                findings.append(
                    f"{where} (`{step_id}`): `owner` is {owner!r}; expected one of "
                    f"{sorted(VALID_OWNERS)}. A step with no owner is the one that "
                    "silently stops happening."
                )
            if "idempotent" not in step:
                findings.append(f"{where} (`{step_id}`): missing `idempotent`.")
            elif step["idempotent"] is not True:
                findings.append(
                    f"{where} (`{step_id}`): `idempotent` is not true. The hook runs once "
                    "and the documented recovery is a manual re-run after activation "
                    "(Apex Reference Guide L228891)."
                )
            verify = step.get("verify")
            if not isinstance(verify, str) or not verify.strip():
                findings.append(
                    f"{where} (`{step_id}`): missing a non-empty `verify`. A checklist item "
                    "with no verification is a claim, not a control."
                )

        missing_steps = [s for s in REQUIRED_CHECKLIST_STEPS if s not in seen]
        if missing_steps:
            findings.append(
                f"{path}: checklist is missing required step(s) {missing_steps}. "
                "One step per concern in runApexClass (SKILL.md, Core Concepts)."
            )

    return findings, True


# --- Check 5: EmailAdministration settings ------------------------------


def check_email_settings(manifest_dir: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted(manifest_dir.rglob("*.settings*")):
        if "emailadmin" not in path.name.lower():
            continue
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            findings.append(f"{path}: not parseable XML ({exc}).")
            continue

        if _local(root.tag) != "EmailAdministrationSettings":
            continue

        for child in root:
            name = _local(child.tag)
            if name not in EMAIL_ADMIN_ELEMENTS:
                findings.append(
                    f"{path}: `<{name}>` is not a field of the "
                    "EmailAdministrationSettings metadata type (api_meta L114872-114994). "
                    "In particular the Deliverability Access Level has no metadata "
                    "surface — record it as a manual checklist step "
                    "(references/gotchas.md section 5)."
                )

        if root.tag.startswith("{") and _local(root.tag) == root.tag:
            pass
        elif not root.tag.startswith("{"):
            findings.append(
                f"{path}: root element is missing the "
                f"xmlns=\"{MDAPI_NS}\" namespace; the deploy will reject it."
            )

        if path.name.lower().startswith("emailadministration"):
            findings.append(
                f"{path}: the guide spells the file `EmailAdminstration.settings` "
                "(api_meta L114854) — no second `i`. Rename before deploying, or expect "
                "an unhelpful deploy error."
            )
    return findings


# --- Driver -------------------------------------------------------------


def check_all(manifest_dir: Path, search_root: Path, strict: bool) -> list[str]:
    if not manifest_dir.exists():
        return [f"--manifest-dir does not exist: {manifest_dir}"]
    if not manifest_dir.is_dir():
        return [f"--manifest-dir is not a directory: {manifest_dir}"]

    findings, saw_class, _ = check_apex(manifest_dir)

    checklist_findings, saw_checklist = check_checklist(manifest_dir, search_root)
    findings.extend(checklist_findings)
    if strict and saw_class and not saw_checklist:
        findings.append(
            f"{search_root}: no `*post-refresh-checklist*.json` found. Workflow step 2 "
            "writes it before the Apex, so the steps that cannot be automated get an "
            "owner (references/metadata-examples.md section 7)."
        )

    findings.extend(check_email_settings(manifest_dir))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check a sandbox post-refresh automation package: SandboxPostCopy class "
            "shape and no-arg constructor, the testSandboxPostCopyScript overload, the "
            "CronTrigger live-state coverage, checklist JSON completeness, and "
            "EmailAdministrationSettings element validity."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata tree (default: current directory).",
    )
    parser.add_argument(
        "--checklist-root",
        default=None,
        help=(
            "Where to look for *post-refresh-checklist*.json, if it lives outside the "
            "metadata tree (default: the parent of --manifest-dir)."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail when a post-copy class exists but no checklist JSON was found.",
    )
    args = parser.parse_args()

    manifest_dir = Path(args.manifest_dir)
    search_root = (
        Path(args.checklist_root)
        if args.checklist_root
        else (manifest_dir.parent if manifest_dir.parent != Path("") else manifest_dir)
    )

    findings = check_all(manifest_dir, search_root, args.strict)

    if not findings:
        print("OK: no sandbox post-refresh automation issues found.")
        return 0

    for finding in findings:
        print(f"WARN: {finding}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
