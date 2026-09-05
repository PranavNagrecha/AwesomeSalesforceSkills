#!/usr/bin/env python3
"""Review approval-process metadata for routing, locking, and deploy-order risks.

Stdlib only. Reads ``approvalProcesses/*.approvalProcess-meta.xml`` from a DX
tree and reports findings as JSON on stdout.

Usage
-----
    python3 check_approval_design.py --manifest-dir force-app/main/default
    python3 check_approval_design.py path/to/approvalProcesses

Checks
------
CRITICAL  Two or more active processes on the same object with no entry
          criteria: both admit every record, so which one a submission enters
          is decided purely by the org's process order, which is not carried
          in the metadata.
HIGH      A step with no ``assignedApprover``.
HIGH      A step using approver type ``userHierarchyField`` while the process
          has no ``nextAutomatedApprover`` element.
HIGH      No ``approvalStep`` at all.
MEDIUM    ``emailTemplate`` with no matching ``*.email-meta.xml`` anywhere in
          the manifest tree (REVIEW instead when the tree holds no templates
          at all, since the reference then cannot be resolved either way).
MEDIUM    A referenced workflow action with no matching definition in
          ``workflows/<Object>.workflow-meta.xml``.
MEDIUM    Active process with no ``entryCriteria`` (admits every record).
LOW       ``finalApprovalRecordLock`` true together with
          ``recordEditability`` ``AdminOnly`` - the record is admin-only
          forever once approved.
REVIEW    Missing initial-submission / final-approval / final-rejection /
          recall action blocks, and a post-first step with no
          ``rejectBehavior`` (which cannot be set after activation).
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SUFFIX = ".approvalProcess-meta.xml"
WORKFLOW_SUFFIX = ".workflow-meta.xml"
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

# WorkflowActionType -> the Workflow child element holding its definitions.
ACTION_CONTAINER = {
    "Alert": "alerts",
    "FieldUpdate": "fieldUpdates",
    "Task": "tasks",
    "OutboundMessage": "outboundMessages",
    "FlowAction": "flowActions",
}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child(element: ET.Element | None, name: str) -> ET.Element | None:
    """First direct child named ``name``.

    A leaf ``Element`` is falsy, so every caller must compare against None.
    Never write ``el.find(a) or el.find(b)``.
    """
    if element is None:
        return None
    for candidate in element:
        if local_name(candidate.tag) == name:
            return candidate
    return None


def children(element: ET.Element | None, name: str) -> list[ET.Element]:
    if element is None:
        return []
    return [c for c in element if local_name(c.tag) == name]


def text_of(element: ET.Element | None, name: str) -> str:
    found = child(element, name)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def is_true(element: ET.Element | None, name: str) -> bool:
    return text_of(element, name).lower() == "true"


def has_child(element: ET.Element | None, name: str) -> bool:
    return child(element, name) is not None


def object_of(path: Path) -> str:
    """``Opportunity.Discount_Approval.approvalProcess-meta.xml`` -> Opportunity."""
    stem = path.name[: -len(SUFFIX)]
    return stem.split(".", 1)[0] if "." in stem else stem


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(c for c in path.rglob(f"*{SUFFIX}") if c.is_file())
        elif path.is_file() and path.name.endswith(SUFFIX):
            files.append(path)
    return sorted(set(files))


def load_workflow_actions(root_dir: Path | None) -> dict[str, set[str]]:
    """Map ``<Object>`` -> set of ``"<container>:<fullName>"`` defined for it."""
    defined: dict[str, set[str]] = {}
    if root_dir is None or not root_dir.exists():
        return defined
    for wf_file in sorted(root_dir.rglob(f"*{WORKFLOW_SUFFIX}")):
        obj = wf_file.name[: -len(WORKFLOW_SUFFIX)]
        names = defined.setdefault(obj, set())
        try:
            wf_root = ET.parse(wf_file).getroot()
        except ET.ParseError:
            continue
        for container in ACTION_CONTAINER.values():
            for entry in children(wf_root, container):
                full_name = text_of(entry, "fullName")
                if full_name:
                    names.add(f"{container}:{full_name}")
    return defined


def load_email_templates(root_dir: Path | None) -> set[str]:
    """Set of ``Folder/DeveloperName`` templates present in the tree."""
    found: set[str] = set()
    if root_dir is None or not root_dir.exists():
        return found
    for tmpl in sorted(root_dir.rglob("*.email-meta.xml")):
        name = tmpl.name[: -len(".email-meta.xml")]
        folder = tmpl.parent.name
        found.add(f"{folder}/{name}")
        found.add(name)
    return found


def iter_action_refs(root: ET.Element) -> list[tuple[str, str, str]]:
    """Every ``(block, action name, action type)`` referenced by the process."""
    refs: list[tuple[str, str, str]] = []
    process_blocks = [
        "initialSubmissionActions",
        "finalApprovalActions",
        "finalRejectionActions",
        "recallActions",
    ]
    containers: list[tuple[str, ET.Element]] = [
        (name, block) for name in process_blocks for block in children(root, name)
    ]
    for index, step in enumerate(children(root, "approvalStep"), start=1):
        label = text_of(step, "label") or text_of(step, "name") or f"step {index}"
        for name in ("approvalActions", "rejectionActions"):
            containers.extend((f"{label}/{name}", block) for block in children(step, name))

    for block_name, block in containers:
        for action in children(block, "action"):
            refs.append((block_name, text_of(action, "name"), text_of(action, "type")))
    return refs


def audit_file(
    path: Path,
    workflow_actions: dict[str, set[str]],
    email_templates: set[str],
    templates_known: bool,
    workflows_known: bool,
) -> list[str]:
    findings: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"CRITICAL {path}: not well-formed XML ({exc})"]

    obj = object_of(path)
    active = is_true(root, "active")
    steps = children(root, "approvalStep")

    # --- structure -------------------------------------------------------
    if not steps:
        findings.append(f"HIGH {path}: no approvalStep defined; the process cannot route anything")

    if active and not has_child(root, "entryCriteria"):
        findings.append(
            f"MEDIUM {path}: active process has no entryCriteria, so every {obj} record "
            "is admitted; which process a submission enters then depends on org process order"
        )

    if not has_child(root, "allowedSubmitters"):
        findings.append(
            f"HIGH {path}: allowedSubmitters is required; without it no submitter population is declared"
        )

    # --- approvers -------------------------------------------------------
    has_next_automated = has_child(root, "nextAutomatedApprover")
    for index, step in enumerate(steps, start=1):
        label = text_of(step, "label") or text_of(step, "name") or f"step {index}"
        assigned = child(step, "assignedApprover")
        approvers = children(assigned, "approver") if assigned is not None else []
        if assigned is None or not approvers:
            findings.append(
                f"HIGH {path}: step '{label}' has no assignedApprover; submissions reaching it cannot route"
            )
            continue
        for approver in approvers:
            approver_type = text_of(approver, "type")
            approver_name = text_of(approver, "name")
            if approver_type == "userHierarchyField" and not has_next_automated:
                findings.append(
                    f"HIGH {path}: step '{label}' uses approver type userHierarchyField but the "
                    "process declares no nextAutomatedApprover; no step may route by hierarchy field"
                )
            if approver_type in {"user", "queue", "relatedUserField"} and not approver_name:
                findings.append(
                    f"HIGH {path}: step '{label}' has approver type '{approver_type}' with no name"
                )
        if len(approvers) > 1 and not has_child(assigned, "whenMultipleApprovers"):
            findings.append(
                f"LOW {path}: step '{label}' has {len(approvers)} approvers with no "
                "whenMultipleApprovers; it defaults to Unanimous"
            )
        if index > 1 and not has_child(step, "rejectBehavior"):
            findings.append(
                f"REVIEW {path}: step '{label}' declares no rejectBehavior; set RejectRequest or "
                "BackToPrevious before activating - it cannot be changed afterwards"
            )

    # --- locking ---------------------------------------------------------
    editability = text_of(root, "recordEditability")
    if is_true(root, "finalApprovalRecordLock") and editability == "AdminOnly":
        findings.append(
            f"LOW {path}: finalApprovalRecordLock is true with recordEditability AdminOnly; "
            "approved records stay editable by administrators only, permanently"
        )
    if editability and editability not in {"AdminOnly", "AdminOrCurrentApprover"}:
        findings.append(
            f"HIGH {path}: recordEditability '{editability}' is not a valid RecordEditabilityType"
        )

    # --- references ------------------------------------------------------
    template = text_of(root, "emailTemplate")
    if template and templates_known and template not in email_templates:
        findings.append(
            f"MEDIUM {path}: emailTemplate '{template}' has no matching *.email-meta.xml in the "
            "tree; the deploy fails unless it already exists in the target org"
        )
    elif template and not templates_known:
        findings.append(
            f"REVIEW {path}: emailTemplate '{template}' could not be resolved because the tree "
            "contains no *.email-meta.xml files; confirm it exists in the target org before deploying"
        )

    known_actions = workflow_actions.get(obj, set())
    for block_name, action_name, action_type in iter_action_refs(root):
        if not action_name or not action_type:
            findings.append(f"HIGH {path}: {block_name} has an action missing name or type")
            continue
        if action_type not in ACTION_CONTAINER:
            findings.append(
                f"HIGH {path}: {block_name} action '{action_name}' has type '{action_type}', "
                "which is not a WorkflowActionType (Alert, FieldUpdate, Task, OutboundMessage, FlowAction)"
            )
            continue
        if action_type == "FlowAction":
            findings.append(
                f"MEDIUM {path}: {block_name} action '{action_name}' uses FlowAction, the closed "
                "flow-trigger pilot; fire a FieldUpdate and trigger a record-triggered Flow on it"
            )
        if workflows_known:
            key = f"{ACTION_CONTAINER[action_type]}:{action_name}"
            if known_actions and key not in known_actions:
                findings.append(
                    f"MEDIUM {path}: {block_name} references {action_type} '{action_name}' with no "
                    f"definition in workflows/{obj}.workflow-meta.xml"
                )

    # --- completeness ----------------------------------------------------
    for block, note in (
        ("initialSubmissionActions", "nothing stamps the record as submitted"),
        ("finalApprovalActions", "approval leaves no trace on the record"),
        ("finalRejectionActions", "rejection leaves no trace on the record"),
    ):
        if not has_child(root, block):
            findings.append(f"REVIEW {path}: no {block} configured; {note}")
    if is_true(root, "allowRecall") and not has_child(root, "recallActions"):
        findings.append(
            f"REVIEW {path}: allowRecall is true with no recallActions; a recalled record keeps "
            "whatever the submission actions set"
        )

    return findings


def audit_cross_file(files: list[Path]) -> list[str]:
    """Active processes on the same object that all admit every record."""
    findings: list[str] = []
    open_by_object: dict[str, list[Path]] = {}
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if is_true(root, "active") and not has_child(root, "entryCriteria"):
            open_by_object.setdefault(object_of(path), []).append(path)
    for obj, paths in sorted(open_by_object.items()):
        if len(paths) > 1:
            names = ", ".join(p.name for p in sorted(paths))
            findings.append(
                f"CRITICAL {obj}: {len(paths)} active processes with no entryCriteria ({names}); "
                "every record matches all of them and the winner is decided by org process order, "
                "which the metadata does not carry"
            )
    return findings


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan Salesforce approval-process metadata for routing, locking, and reference risks."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Approval-process files or directories (alternative to --manifest-dir)",
    )
    parser.add_argument(
        "--manifest-dir",
        help="DX metadata root, e.g. force-app/main/default; scans approvalProcesses/ under it "
        "and resolves workflow actions and email templates against the whole tree",
    )
    args = parser.parse_args()

    root_dir: Path | None = None
    targets: list[Path] = [Path(value) for value in args.paths]
    if args.manifest_dir:
        root_dir = Path(args.manifest_dir)
        if not root_dir.exists():
            return emit_result(
                [f"HIGH {root_dir}: --manifest-dir does not exist"],
                f"Scanned 0 approval-process metadata files; {root_dir} not found.",
            )
        targets.append(root_dir / "approvalProcesses")

    if not targets:
        parser.error("provide one or more paths, or --manifest-dir")

    files = iter_files(targets)
    if not files:
        return emit_result(
            ["HIGH no approval-process metadata files found"],
            "Scanned 0 approval-process metadata files; no files matched the provided paths.",
        )

    workflow_actions = load_workflow_actions(root_dir)
    email_templates = load_email_templates(root_dir)
    workflows_known = bool(workflow_actions)
    templates_known = bool(email_templates)

    findings: list[str] = []
    for path in files:
        findings.extend(
            audit_file(path, workflow_actions, email_templates, templates_known, workflows_known)
        )
    findings.extend(audit_cross_file(files))

    notes = []
    if root_dir is None:
        notes.append("workflow-action and email-template resolution skipped (no --manifest-dir)")
    else:
        if not workflows_known:
            notes.append("no workflow files found, so action references were not resolved")
        if not templates_known:
            notes.append("no email templates found, so emailTemplate references were not resolved")
    suffix = f" Note: {'; '.join(notes)}." if notes else ""

    summary = (
        f"Scanned {len(files)} approval-process metadata file(s); "
        f"{len(findings)} finding(s) detected.{suffix}"
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
