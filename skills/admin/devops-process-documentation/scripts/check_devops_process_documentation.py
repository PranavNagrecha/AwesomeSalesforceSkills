#!/usr/bin/env python3
"""Linter for the DevOps process document artefact this skill produces.

The artefact is a single YAML file (``devops-process.yaml``) whose shape is
demonstrated end to end in ``references/worked-examples.md`` section 1.  It
carries six things that rot in six specific ways, and each is a check below:

1. ``environments``   -- every row needs a purpose, a refresh cadence and an
                         owner.  A row with a purpose and no owner is why the
                         "who approves a refresh" question has no answer.
2. ``change_request`` -- every state in the state machine needs an
                         ``approver_role``.  Unapproved transitions are the
                         accountability gap this skill exists to close.
3. ``runbook``        -- a validate-only step must appear before the first
                         deploy step, and at least one rollback step must exist.
4. ``deploy_contract``-- every ``testLevel`` must be one of the five values the
                         Metadata API Developer Guide documents, and
                         ``RunSpecifiedTests`` requires a non-empty ``runTests``.
                         Production runs need ``rollbackOnError: true``.
5. ``deploy_order``   -- when package manifests are available, every metadata
                         type named in a ``package.xml`` must be claimed by some
                         deploy_order step.  An unclaimed type is a component
                         nobody decided where to put.
6. ``raci`` (optional) - rows without an accountable party are reported.

Grounding for the platform facts asserted by these checks, into the extracted
text of the Metadata API Developer Guide (v62 / Summer '26),
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf :

* testLevel enum ................ api_meta.txt L3140-3168
* runTests requires
  RunSpecifiedTests ............. api_meta.txt L3130-3135
* rollbackOnError "must be set to
  true if you're deploying to a
  production org" ............... api_meta.txt L3126-3129
* checkOnly is the validation ... api_meta.txt L3095-3099
* purgeOnDelete does not work
  in production orgs ............ api_meta.txt L3118-3120

Stdlib only.  No PyYAML, no lxml.

Usage:
    python3 check_devops_process_documentation.py --file devops-process.yaml
    python3 check_devops_process_documentation.py --file devops-process.yaml --manifest-dir manifest/
    python3 check_devops_process_documentation.py --manifest-dir .

Exit code 0 when clean, 1 when any ERROR is reported.  WARNs do not fail.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}

# ---------------------------------------------------------------------------
# Documented vocabularies
# ---------------------------------------------------------------------------

# TestLevel enumeration, api_meta.txt L3140-3168.  RunRelevantTests is marked
# beta in the guide; it is accepted here and flagged as a WARN, not an ERROR.
TEST_LEVELS = {
    "NoTestRun",
    "RunSpecifiedTests",
    "RunRelevantTests",
    "RunLocalTests",
    "RunAllTestsInOrg",
}
BETA_TEST_LEVELS = {"RunRelevantTests"}

# deployOptions parameters, api_meta.txt L3088-3160.  A key inside a
# deploy_contract block that is not one of these is almost always an invented
# option name, which is exactly the failure this linter exists to catch.
DEPLOY_OPTIONS = {
    "allowMissingFiles",
    "autoUpdatePackage",
    "checkOnly",
    "ignoreWarnings",
    "performRetrieve",
    "purgeOnDelete",
    "rollbackOnError",
    "runTests",
    "singlePackage",
    "testLevel",
}
# Non-option bookkeeping keys a run block may carry.
DEPLOY_CONTRACT_META = {"note", "target", "target_org", "label", "__lines__"}

ENVIRONMENT_REQUIRED = ("purpose", "refresh_cadence", "owner")

VALIDATE_ACTIONS = {"validate-only", "validate", "check-only", "checkonly", "dry-run"}
DEPLOY_ACTIONS = {"deploy", "quick-deploy", "promote"}
ROLLBACK_ACTIONS = {"rollback", "revert", "restore"}

ALLOWED_PROCESS_STATUS = {"draft", "active", "under-review", "superseded", "retired"}


# ---------------------------------------------------------------------------
# Minimal YAML-subset parser (block mappings, block lists, flow lists, scalars)
# ---------------------------------------------------------------------------

def _scalar(raw: str):
    """Convert a bare, quoted or flow-list YAML scalar to a Python value."""
    text = raw.strip()
    if text[:1] in ("'", '"'):
        closing = text.find(text[0], 1)
        if closing != -1:
            return text[1:closing]
        return text[1:]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in inner.split(",")]
    if text in (">-", ">", "|", "|-"):
        # Folded/literal block scalar; the body lines are indented deeper and
        # are consumed by the block parser as an opaque string.
        return ""
    text = re.split(r"\s+#", text, maxsplit=1)[0].strip()
    if text in ("null", "~", ""):
        return None
    if text in ("true", "false"):
        return text == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _significant_lines(text: str) -> list[tuple[int, str, int]]:
    """Return (indent, content, line_number) for non-blank, non-comment lines."""
    out: list[tuple[int, str, int]] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if "\t" in raw:
            raw = raw.replace("\t", "  ")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        out.append((indent, stripped, number))
    return out


def _parse_block(lines: list[tuple[int, str, int]], idx: int, indent: int):
    """Parse one block starting at lines[idx]; return (value, next_index)."""
    if idx >= len(lines):
        return None, idx

    if lines[idx][1].startswith("- ") or lines[idx][1] == "-":
        items: list = []
        while idx < len(lines):
            line_indent, content, _ = lines[idx]
            if line_indent != indent:
                break
            if not (content.startswith("- ") or content == "-"):
                break
            inner = content[2:].strip() if content.startswith("- ") else ""
            child_indent = indent + 2
            if inner == "":
                idx += 1
                if idx < len(lines) and lines[idx][0] > indent:
                    value, idx = _parse_block(lines, idx, lines[idx][0])
                else:
                    value = None
                items.append(value)
            elif ":" in inner and inner[0] not in ("'", '"', "["):
                sub: list[tuple[int, str, int]] = [(child_indent, inner, lines[idx][2])]
                idx += 1
                while idx < len(lines) and lines[idx][0] >= child_indent:
                    sub.append(lines[idx])
                    idx += 1
                value, _ = _parse_block(sub, 0, child_indent)
                items.append(value)
            else:
                items.append(_scalar(inner))
                idx += 1
        return items, idx

    mapping: dict = {}
    line_numbers: dict = {}
    while idx < len(lines):
        line_indent, content, number = lines[idx]
        if line_indent < indent:
            break
        if line_indent > indent:
            idx += 1
            continue
        if content.startswith("- ") or content == "-":
            break
        if ":" not in content:
            idx += 1
            continue
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        line_numbers[key] = number
        idx += 1
        if rest and rest not in (">-", ">", "|", "|-"):
            mapping[key] = _scalar(rest)
        elif rest in (">-", ">", "|", "|-"):
            # Folded scalar: swallow the deeper-indented body into one string.
            body: list[str] = []
            while idx < len(lines) and lines[idx][0] > line_indent:
                body.append(lines[idx][1])
                idx += 1
            mapping[key] = " ".join(body)
        elif idx < len(lines) and lines[idx][0] > line_indent:
            value, idx = _parse_block(lines, idx, lines[idx][0])
            mapping[key] = value
        else:
            mapping[key] = None
    mapping["__lines__"] = line_numbers
    return mapping, idx


def parse_yaml_subset(text: str) -> dict:
    lines = _significant_lines(text)
    if not lines:
        return {}
    value, _ = _parse_block(lines, 0, lines[0][0])
    return value if isinstance(value, dict) else {}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _text(row, key: str) -> str:
    """Return a stripped string for row[key], or '' when absent or empty."""
    if not isinstance(row, dict):
        return ""
    value = row.get(key)
    if value is None or isinstance(value, bool):
        return ""
    return str(value).strip()


def _mapping(document: dict, key: str) -> dict:
    value = document.get(key)
    return value if isinstance(value, dict) else {}


def _rows(container, key: str) -> list[dict]:
    if not isinstance(container, dict):
        return []
    value = container.get(key)
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _find(element, tag: str):
    """Namespace-tolerant single-child lookup.

    An ElementTree element with no children is falsy, so ``a.find(x) or
    a.find(y)`` silently discards a real leaf match.  Always test
    ``is not None`` instead.
    """
    if element is None:
        return None
    found = element.find(tag)
    if found is None:
        found = element.find(f"sf:{tag}", MD_NS)
    return found


def _find_all(element, tag: str) -> list:
    if element is None:
        return []
    found = element.findall(tag)
    if not found:
        found = element.findall(f"sf:{tag}", MD_NS)
    return found


def _looks_like_process_doc(text: str) -> bool:
    head = text[:4000]
    return "devops_process:" in head or ("environments:" in head and "runbook:" in text)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_header(document: dict, label: str) -> list[str]:
    issues: list[str] = []
    header = _mapping(document, "devops_process")
    if not header:
        issues.append(
            f"ERROR [{label}] No 'devops_process:' header block. The document needs an id, "
            "a title, an owner and a status so a reader can tell whose process this is and "
            "whether it is still in force."
        )
        return issues
    for field in ("id", "title", "owner", "status", "updated"):
        if not _text(header, field):
            issues.append(
                f"ERROR [{label}] devops_process is missing '{field}'. An undated, unowned "
                "process document is indistinguishable from a stale one."
            )
    status = _text(header, "status").lower()
    if status and status not in ALLOWED_PROCESS_STATUS:
        issues.append(
            f"ERROR [{label}] devops_process.status '{status}' is not one of "
            f"{sorted(ALLOWED_PROCESS_STATUS)}."
        )
    if not _text(header, "review_cadence"):
        issues.append(
            f"WARN [{label}] devops_process has no 'review_cadence'. Environment matrices "
            "decay silently; without a named forcing function this document will be wrong "
            "before anyone notices."
        )
    return issues


def check_environments(document: dict, label: str) -> list[str]:
    issues: list[str] = []
    environments = _rows(document, "environments")
    if not environments:
        issues.append(
            f"ERROR [{label}] No 'environments:' list. Every DevOps process document must "
            "state the environment ladder; runbooks that reference an environment with no "
            "row here are referencing something nobody has defined."
        )
        return issues

    seen: set[str] = set()
    for index, environment in enumerate(environments, start=1):
        name = _text(environment, "name") or f"<row {index}>"
        if not _text(environment, "name"):
            issues.append(f"ERROR [{label}] environments row {index} has no 'name'.")
        elif name in seen:
            issues.append(
                f"ERROR [{label}] environments has two rows named '{name}'. "
                "Environment names are the join key with the runbook; they must be unique."
            )
        else:
            seen.add(name)

        for field in ENVIRONMENT_REQUIRED:
            if not _text(environment, field):
                issues.append(
                    f"ERROR [{label}] environment '{name}' is missing '{field}'. "
                    "Purpose, refresh cadence and owner are the three columns that make the "
                    "row actionable; without the owner nobody can approve or block a refresh."
                )
        if not _text(environment, "data_policy"):
            issues.append(
                f"WARN [{label}] environment '{name}' has no 'data_policy'. State whether "
                "production data is present, anonymized, synthetic or prohibited — "
                "'no PII' is not a data policy."
            )
    return issues


def check_change_request(document: dict, label: str) -> list[str]:
    issues: list[str] = []
    change_request = _mapping(document, "change_request")
    if not change_request:
        issues.append(
            f"ERROR [{label}] No 'change_request:' block. The document must define the "
            "change-request record and its state machine, or approvals live in someone's inbox."
        )
        return issues

    states = _rows(change_request, "states")
    if not states:
        issues.append(
            f"ERROR [{label}] change_request has no 'states:' list. Without a state machine "
            "there is nothing for an approver to approve."
        )
    seen: set[str] = set()
    for index, state in enumerate(states, start=1):
        name = _text(state, "name") or f"<state {index}>"
        if not _text(state, "name"):
            issues.append(f"ERROR [{label}] change_request.states row {index} has no 'name'.")
        elif name in seen:
            issues.append(f"ERROR [{label}] change_request.states has two states named '{name}'.")
        else:
            seen.add(name)
        if not _text(state, "approver_role"):
            issues.append(
                f"ERROR [{label}] change-request state '{name}' has no 'approver_role'. "
                "Every state transition needs a role that owns it — a role, not a person, so "
                "the process survives a leaver."
            )
        if not _text(state, "exit_criteria"):
            issues.append(
                f"WARN [{label}] change-request state '{name}' has no 'exit_criteria'. "
                "A state with no exit criteria is a queue, not a gate."
            )

    emergency = change_request.get("emergency_path")
    if not isinstance(emergency, dict):
        issues.append(
            f"WARN [{label}] change_request has no 'emergency_path'. Emergencies happen "
            "whether or not the document admits it; an undocumented emergency path is an "
            "undocumented approval bypass."
        )
    else:
        if not _text(emergency, "approver_role"):
            issues.append(
                f"ERROR [{label}] change_request.emergency_path has no 'approver_role'. "
                "The path that skips the ladder is the one that most needs a named approver."
            )
        if not _text(emergency, "retro_requirement"):
            issues.append(
                f"WARN [{label}] change_request.emergency_path has no 'retro_requirement'. "
                "An emergency fix that is never replayed into the lower environments makes "
                "the ladder diverge permanently."
            )
    return issues


def check_deploy_contract(document: dict, label: str) -> list[str]:
    issues: list[str] = []
    contract = _mapping(document, "deploy_contract")
    if not contract:
        issues.append(
            f"WARN [{label}] No 'deploy_contract:' block. Recording the deploy options the "
            "release actually used is what makes a post-incident reconstruction possible."
        )
        return issues

    runs = {key: value for key, value in contract.items()
            if key != "__lines__" and isinstance(value, dict)}
    if not runs:
        issues.append(
            f"ERROR [{label}] deploy_contract has no run blocks. Expect at least a "
            "validation_run and a production_run."
        )
        return issues

    for run_name, run in runs.items():
        prefix = f"deploy_contract.{run_name}"

        for key in run:
            if key in DEPLOY_OPTIONS or key in DEPLOY_CONTRACT_META:
                continue
            issues.append(
                f"ERROR [{label}] {prefix}.{key} is not a documented deployOptions parameter. "
                f"Valid options: {', '.join(sorted(DEPLOY_OPTIONS))} "
                "(Metadata API Developer Guide, deployOptions Parameters)."
            )

        test_level = _text(run, "testLevel")
        if not test_level:
            issues.append(
                f"ERROR [{label}] {prefix} has no 'testLevel'. Leaving it unset is a decision, "
                "not a default: no tests run in a deployment to a non-production org, and "
                "production runs tests only when the package contains Apex. Say which you meant."
            )
        elif test_level not in TEST_LEVELS:
            issues.append(
                f"ERROR [{label}] {prefix}.testLevel '{test_level}' is not in the documented "
                f"TestLevel enumeration: {', '.join(sorted(TEST_LEVELS))}."
            )
        elif test_level in BETA_TEST_LEVELS:
            issues.append(
                f"WARN [{label}] {prefix}.testLevel '{test_level}' is documented as beta. "
                "Confirm it is enabled in the target org before the window."
            )

        run_tests = run.get("runTests")
        run_tests_list = run_tests if isinstance(run_tests, list) else []
        if test_level == "RunSpecifiedTests" and not run_tests_list:
            issues.append(
                f"ERROR [{label}] {prefix}.testLevel is RunSpecifiedTests but 'runTests' is "
                "empty. The guide requires the test classes to be named, and this level "
                "changes the coverage rule to 75% per class and trigger individually."
            )
        if test_level and test_level != "RunSpecifiedTests" and run_tests_list:
            issues.append(
                f"WARN [{label}] {prefix} names runTests but testLevel is '{test_level}'. "
                "runTests only applies when testLevel is RunSpecifiedTests; the list will be ignored."
            )

        target = (_text(run, "target") or _text(run, "target_org") or run_name).lower()
        is_production = "prod" in target
        if is_production:
            if run.get("rollbackOnError") is not True:
                issues.append(
                    f"ERROR [{label}] {prefix} targets production but rollbackOnError is not "
                    "true. It defaults to false, and the guide states it must be true when "
                    "deploying to a production org — otherwise a partial failure leaves a "
                    "half-landed org."
                )
            if run.get("purgeOnDelete") is True:
                issues.append(
                    f"ERROR [{label}] {prefix} targets production with purgeOnDelete true. "
                    "The option only works in Developer Edition and sandbox orgs; setting it "
                    "here documents a behaviour the org will not perform."
                )
        if run.get("checkOnly") is True and run.get("rollbackOnError") is False:
            issues.append(
                f"WARN [{label}] {prefix} is a validation with rollbackOnError false. "
                "Validations save nothing either way, but the flag should match the run it "
                "is rehearsing or the rehearsal is not one."
            )
    return issues


def check_runbook(document: dict, label: str) -> list[str]:
    issues: list[str] = []
    runbook = _mapping(document, "runbook")
    if not runbook:
        issues.append(
            f"ERROR [{label}] No 'runbook:' block. The process document must carry at least "
            "one worked runbook, or it documents a process nobody has executed."
        )
        return issues

    for field in ("release", "target_org", "window", "rollback_decision_owner"):
        if not _text(runbook, field):
            issues.append(
                f"ERROR [{label}] runbook is missing '{field}'. A runbook with no named "
                "rollback decision owner has a rollback section nobody can trigger."
            )

    steps = _rows(runbook, "steps")
    if not steps:
        issues.append(f"ERROR [{label}] runbook has no 'steps:' list.")
        return issues

    seen_ids: set[str] = set()
    validate_index: int | None = None
    deploy_index: int | None = None
    rollback_found = False

    for index, step in enumerate(steps):
        step_id = _text(step, "id") or f"<step {index + 1}>"
        if not _text(step, "id"):
            issues.append(f"ERROR [{label}] runbook step {index + 1} has no 'id'.")
        elif step_id in seen_ids:
            issues.append(f"ERROR [{label}] runbook has two steps with id '{step_id}'.")
        else:
            seen_ids.add(step_id)

        if not _text(step, "owner"):
            issues.append(
                f"ERROR [{label}] runbook step '{step_id}' has no 'owner'. A step without a "
                "single responsible role is a step that gets skipped during the window."
            )
        if not _text(step, "pass_criteria"):
            issues.append(
                f"ERROR [{label}] runbook step '{step_id}' has no 'pass_criteria'. "
                "Without a pass/fail outcome the step cannot gate anything."
            )

        action = _text(step, "action").lower()
        if action in VALIDATE_ACTIONS and validate_index is None:
            validate_index = index
        if action in DEPLOY_ACTIONS and deploy_index is None:
            deploy_index = index
        if action in ROLLBACK_ACTIONS:
            rollback_found = True

    if deploy_index is None:
        issues.append(
            f"ERROR [{label}] runbook has no step with action 'deploy'. "
            f"Recognised deploy actions: {', '.join(sorted(DEPLOY_ACTIONS))}."
        )
    if validate_index is None:
        issues.append(
            f"ERROR [{label}] runbook has no validate-only step. A validation "
            "(checkOnly = true) verifies the results of the tests a deploy would run without "
            "committing anything, and it is what licenses a quick deploy inside the window. "
            f"Recognised validate actions: {', '.join(sorted(VALIDATE_ACTIONS))}."
        )
    elif deploy_index is not None and validate_index > deploy_index:
        issues.append(
            f"ERROR [{label}] runbook step '{_text(steps[deploy_index], 'id')}' deploys before "
            f"step '{_text(steps[validate_index], 'id')}' validates. The validate-only run must "
            "precede the deploy; a validation after the fact rehearses nothing."
        )
    if not rollback_found:
        issues.append(
            f"ERROR [{label}] runbook has no rollback step. A runbook without a rollback "
            "step, an owner and a threshold is a one-way door."
        )
    return issues


def check_deploy_order(document: dict, manifest_types: dict[str, list[str]], label: str) -> list[str]:
    issues: list[str] = []
    order = _rows(document, "deploy_order")
    if not order:
        if manifest_types:
            issues.append(
                f"ERROR [{label}] Manifests were found but the document has no 'deploy_order:' "
                "list. Within one deployment the Metadata API resolves dependencies itself; "
                "the order matters when a release is split across submissions, because only "
                "one deployment runs at a time and queued deployments are not necessarily "
                "executed in submission order."
            )
        else:
            issues.append(f"WARN [{label}] No 'deploy_order:' list.")
        return issues

    covered: set[str] = set()
    for index, step in enumerate(order, start=1):
        types = step.get("metadata_types")
        if not isinstance(types, list) or not types:
            issues.append(
                f"ERROR [{label}] deploy_order step {index} has no 'metadata_types' list."
            )
            continue
        if not _text(step, "reason"):
            issues.append(
                f"WARN [{label}] deploy_order step {index} has no 'reason'. An order with no "
                "stated dependency is an order nobody can safely change."
            )
        for entry in types:
            if isinstance(entry, str) and entry.strip():
                covered.add(entry.strip())

    for metadata_type, sources in sorted(manifest_types.items()):
        if metadata_type not in covered:
            issues.append(
                f"ERROR [{label}] metadata type '{metadata_type}' appears in "
                f"{', '.join(sorted(sources))} but no deploy_order step claims it. Every type "
                "in the release needs a decided position in the submission sequence."
            )
    return issues


def check_raci(document: dict, label: str) -> list[str]:
    issues: list[str] = []
    raci = document.get("raci")
    if not isinstance(raci, list):
        return issues
    for index, row in enumerate(raci, start=1):
        if not isinstance(row, dict):
            continue
        activity = _text(row, "activity") or f"<raci row {index}>"
        if not _text(row, "accountable"):
            issues.append(
                f"ERROR [{label}] RACI row '{activity}' has no 'accountable' role. "
                "Responsible can be shared; accountable cannot."
            )
    return issues


# ---------------------------------------------------------------------------
# Manifest scanning
# ---------------------------------------------------------------------------

def collect_manifest_types(manifest_dir: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Return ({metadata type: [source file names]}, issues) for package manifests."""
    issues: list[str] = []
    found: dict[str, list[str]] = {}
    if not manifest_dir.exists():
        return found, [f"ERROR Directory not found: {manifest_dir}"]

    for xml_file in sorted(manifest_dir.rglob("*.xml")):
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError as error:
            issues.append(f"ERROR [{xml_file.name}] is not well-formed XML: {error}")
            continue
        if not root.tag.endswith("Package"):
            continue
        is_destructive = "destructive" in xml_file.name.lower()
        for types_node in _find_all(root, "types"):
            name_node = _find(types_node, "name")
            if name_node is None or not (name_node.text or "").strip():
                issues.append(
                    f"ERROR [{xml_file.name}] a <types> block has no <name>; the manifest "
                    "cannot be deployed as written."
                )
                continue
            metadata_type = name_node.text.strip()
            found.setdefault(metadata_type, []).append(xml_file.name)
        if not is_destructive and _find(root, "version") is None:
            issues.append(
                f"WARN [{xml_file.name}] has no <version>. The API version the deployment "
                "uses is the one specified in package.xml; leaving it out makes the "
                "deployment's behaviour depend on the client."
            )
    return found, issues


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def check_document(path: Path, manifest_types: dict[str, list[str]]) -> list[str]:
    label = path.name
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return [f"ERROR [{label}] cannot be read: {error}"]

    document = parse_yaml_subset(text)
    if not document:
        return [f"ERROR [{label}] parsed to an empty document. Expected a YAML mapping."]

    issues: list[str] = []
    issues.extend(check_header(document, label))
    issues.extend(check_environments(document, label))
    issues.extend(check_change_request(document, label))
    issues.extend(check_deploy_contract(document, label))
    issues.extend(check_runbook(document, label))
    issues.extend(check_deploy_order(document, manifest_types, label))
    issues.extend(check_raci(document, label))
    return issues


def find_process_documents(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for suffix in ("*.yaml", "*.yml"):
        for path in sorted(root.rglob(suffix)):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if _looks_like_process_doc(text):
                candidates.append(path)
    return candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a Salesforce DevOps process document (environment ladder, change-request "
            "state machine, deploy contract, deploy order, runbook, RACI) and, when package "
            "manifests are present, check that the deploy order covers every metadata type "
            "in the release."
        ),
    )
    parser.add_argument(
        "--file",
        help="The devops-process YAML document to lint.",
    )
    parser.add_argument(
        "--manifest-dir",
        help=(
            "Directory holding package.xml / destructiveChanges*.xml manifests. Scanned for "
            "metadata types so deploy_order coverage can be checked. When --file is omitted, "
            "this directory is also searched for the process document itself."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    manifest_types: dict[str, list[str]] = {}
    issues: list[str] = []

    if args.manifest_dir:
        manifest_types, manifest_issues = collect_manifest_types(Path(args.manifest_dir))
        issues.extend(manifest_issues)

    documents: list[Path] = []
    if args.file:
        candidate = Path(args.file)
        if not candidate.exists():
            issues.append(f"ERROR File not found: {candidate}")
        else:
            documents.append(candidate)
    elif args.manifest_dir:
        documents = find_process_documents(Path(args.manifest_dir))
        if not documents:
            issues.append(
                f"ERROR No DevOps process document found under {args.manifest_dir}. Expected a "
                "YAML file containing a 'devops_process:' header. Pass --file to name it "
                "explicitly."
            )
    else:
        documents = find_process_documents(Path("."))
        if not documents:
            issues.append(
                "ERROR No DevOps process document found in the current directory. "
                "Pass --file devops-process.yaml or --manifest-dir <dir>."
            )

    for document in documents:
        issues.extend(check_document(document, manifest_types))

    errors = [issue for issue in issues if issue.startswith("ERROR")]
    warnings = [issue for issue in issues if issue.startswith("WARN")]

    for issue in warnings:
        print(issue, file=sys.stderr)
    for issue in errors:
        print(issue, file=sys.stderr)

    if not issues:
        print("No issues found.")
        return 0

    print(
        f"\n{len(errors)} error(s), {len(warnings)} warning(s) "
        f"across {len(documents)} document(s).",
        file=sys.stderr,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
