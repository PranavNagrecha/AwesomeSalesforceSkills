#!/usr/bin/env python3
"""Linter for the CAB decision record this skill produces.

The artefact is a YAML file with a ``cab_decision:`` header, demonstrated end to
end in ``references/worked-examples.md`` section 3.  A CAB decision rots in
seven specific ways, and each is a check below:

1. ``classification`` / ``decision`` / vote values must come from the documented
   enums.  A free-text tier is a tier nobody can report on.
2. **Quorum** -- the number of members who actually voted must meet the charter's
   quorum for this classification, and every role the charter names as required
   must be among the voters.  Attendance is not quorum; a vote is.
3. **Risk fields** -- ``risk.level``, ``risk.rationale`` and a ``blast_radius``
   with a source and at least one metadata type.  A board that did not record
   blast radius did not assess one.
4. **Rollback** -- ``rollback.method`` and ``rollback.owner`` must be present,
   and a ``risk.level: high`` change must record ``rehearsed: true`` (or an
   explicit waiver note).
5. **Test evidence** -- every ``test_evidence[].artefact`` path must resolve to a
   real file under ``--manifest-dir``.  An approval citing a UAT pack nobody
   wrote is the most common CAB failure this checker exists to catch.
6. **Deploy window vs freeze** -- the approved window must not overlap any range
   in ``freezes``.  Salesforce's own guidance is to "avoid running deployments
   during the service upgrade" because a deployment interrupted by downtime is
   "retried from the beginning after the service is restored"
   (api_meta.txt L2115-2125).
7. **Emergency retrospective** -- an ``emergency`` record without a
   ``post_implementation_review.date`` is a permanent bypass wearing a
   temporary label.

Two further platform-grounded checks run when the record pins them:

* ``deploy_options`` -- ``testLevel`` must be one of the five values the guide
  documents; ``NoTestRun`` "applies only to deployments to development
  environments" so it is an error on a production window; ``RunSpecifiedTests``
  requires a non-empty ``runTests``; ``rollbackOnError`` "must be set to true if
  you're deploying to a production org"; ``ignoreWarnings`` should not be true
  for production.
* ``quick_deploy`` -- a validated component set qualifies for deployment without
  re-running tests only when it "has been validated successfully for the target
  environment within the last 10 days".  So the validation's target org must
  equal the window's target org, and its date must be within 10 days of the
  window opening.

Grounding for the platform facts asserted by these checks, into the extracted
text of the Metadata API Developer Guide (v62 / Summer '26),
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf :

* testLevel enum, NoTestRun scope,
  RunLocalTests default in production .... api_meta.txt L4280-4329
* runTests requires RunSpecifiedTests .... api_meta.txt L3132-3135
* rollbackOnError must be true for
  production ............................. api_meta.txt L4255-4260
* ignoreWarnings: don't set true for
  production ............................. api_meta.txt L7390-7392
* checkOnly is the validation ............ api_meta.txt L3095-3099
* quick deploy: validated for the target
  environment within the last 10 days .... api_meta.txt L4863-4869
* avoid deploying during a service
  upgrade; deploys are retried from the
  beginning after downtime ............... api_meta.txt L2115-2125

Stdlib only.  No PyYAML.

Usage:
    python3 check_change_advisory_board_process.py --file CAB-2026-014.yaml
    python3 check_change_advisory_board_process.py --manifest-dir artefacts
    python3 check_change_advisory_board_process.py --manifest-dir artefacts \\
        --charter artefacts/governance/cab-charter.yaml

Exit code 0 when clean, 1 when any ERROR is reported.  WARNs do not fail.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Enums the artefact and the ITSM form share (worked-examples.md section 2)
# ---------------------------------------------------------------------------
CLASSIFICATIONS = {"standard", "normal", "emergency"}
DECISIONS = {"approved", "approved-with-conditions", "deferred", "rejected"}
RISK_LEVELS = {"low", "medium", "high"}
VOTES = {"approve", "approve-with-conditions", "abstain", "reject", "veto"}
COUNTS_TOWARD_QUORUM = {"approve", "approve-with-conditions", "reject", "veto"}

# Metadata API DeployOptions.testLevel enum (api_meta.txt L4280-4329)
TEST_LEVELS = {
    "NoTestRun",
    "RunSpecifiedTests",
    "RunRelevantTests",
    "RunLocalTests",
    "RunAllTestsInOrg",
}

# Quick deploy validity window (api_meta.txt L4863-4869)
QUICK_DEPLOY_VALID_DAYS = 10

# Fallback quorum when no charter file is supplied. The charter is authoritative
# whenever it is found; these keep the checker useful without one.
DEFAULT_QUORUM = {"standard": 0, "normal": 3, "emergency": 2}
DEFAULT_REQUIRED_ROLES = {
    "normal": ["release-manager", "business-owner"],
    "emergency": ["release-manager"],
}

PLACEHOLDERS = {"", "todo", "tbd", "n/a", "na", "none", "xxx", "?", "-"}


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
        return ""
    text = re.split(r"\s+#", text, maxsplit=1)[0].strip()
    if text in ("null", "~", ""):
        return None
    if text in ("true", "false"):
        return text == "true"
    if text in ("yes", "no"):
        return text
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
    while idx < len(lines):
        line_indent, content, _number = lines[idx]
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
        idx += 1
        if rest and rest not in (">-", ">", "|", "|-"):
            mapping[key] = _scalar(rest)
        elif rest in (">-", ">", "|", "|-"):
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

def _mapping(document, key: str) -> dict:
    if not isinstance(document, dict):
        return {}
    value = document.get(key)
    return value if isinstance(value, dict) else {}


def _rows(document, key: str) -> list:
    if not isinstance(document, dict):
        return []
    value = document.get(key)
    if isinstance(value, list):
        return value
    return []


def _text(row, key: str) -> str:
    """Return a stripped string for row[key], or '' when absent or empty."""
    if not isinstance(row, dict):
        return ""
    value = row.get(key)
    if value is None or isinstance(value, bool):
        return ""
    return str(value).strip()


def _is_filled(value: str) -> bool:
    return value.strip().lower() not in PLACEHOLDERS


def _parse_date(value: str):
    """Return a date for an ISO date or datetime string, else None."""
    text = (value or "").strip()
    if not text:
        return None
    text = text.rstrip("Z")
    for cut in (10, 19, len(text)):
        try:
            return datetime.fromisoformat(text[:cut]).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_identity(record: dict, label: str) -> list[str]:
    """Ids, enums and the fields every record needs regardless of tier."""
    issues: list[str] = []

    if not _is_filled(_text(record, "id")):
        issues.append(f"ERROR [{label}] cab_decision has no 'id'. The record cannot be cited.")
    if not _is_filled(_text(record, "change_request")):
        issues.append(
            f"ERROR [{label}] no 'change_request'. The CR number is the only join between "
            "this decision and the deployment it approved."
        )

    classification = _text(record, "classification").lower()
    if classification not in CLASSIFICATIONS:
        issues.append(
            f"ERROR [{label}] classification '{classification or '(missing)'}' is not one of "
            f"{sorted(CLASSIFICATIONS)}."
        )

    decision = _text(record, "decision").lower()
    if decision not in DECISIONS:
        issues.append(
            f"ERROR [{label}] decision '{decision or '(missing)'}' is not one of "
            f"{sorted(DECISIONS)}."
        )

    if not _parse_date(_text(record, "meeting_date")):
        issues.append(
            f"ERROR [{label}] 'meeting_date' is missing or not an ISO date. "
            "An undated decision cannot be placed relative to the deploy window."
        )
    return issues


def check_quorum(record: dict, charter: dict, label: str) -> list[str]:
    """Votes cast must meet the charter's quorum and cover the required roles."""
    issues: list[str] = []
    classification = _text(record, "classification").lower()
    if classification == "standard":
        return issues  # pre-authorised; no board vote by design

    quorum_map = _mapping(charter, "quorum") or DEFAULT_QUORUM
    required_map = _mapping(charter, "required_roles") or DEFAULT_REQUIRED_ROLES

    raw_quorum = quorum_map.get(classification, DEFAULT_QUORUM.get(classification, 2))
    try:
        quorum = int(raw_quorum)
    except (TypeError, ValueError):
        issues.append(
            f"WARN [{label}] charter quorum for '{classification}' is not a number "
            f"({raw_quorum!r}); falling back to {DEFAULT_QUORUM.get(classification, 2)}."
        )
        quorum = DEFAULT_QUORUM.get(classification, 2)

    board = _rows(record, "board")
    if not board:
        issues.append(
            f"ERROR [{label}] no 'board:' list. Without recorded votes there is no evidence "
            "the board met at all."
        )
        return issues

    voters: list[str] = []
    seen_roles: set[str] = set()
    for index, member in enumerate(board, start=1):
        role = _text(member, "role")
        vote = _text(member, "vote").lower()
        if not _is_filled(role):
            issues.append(f"ERROR [{label}] board row {index} has no 'role'.")
            continue
        if role in seen_roles:
            issues.append(f"ERROR [{label}] board lists role '{role}' twice.")
        seen_roles.add(role)
        if vote not in VOTES:
            issues.append(
                f"ERROR [{label}] board role '{role}' has vote '{vote or '(missing)'}', "
                f"not one of {sorted(VOTES)}."
            )
            continue
        if vote in COUNTS_TOWARD_QUORUM:
            voters.append(role)
        if vote == "approve-with-conditions" and not _rows(record, "conditions"):
            issues.append(
                f"ERROR [{label}] role '{role}' voted approve-with-conditions but the record "
                "has no 'conditions:' list. An unrecorded condition is a dropped condition."
            )

    if len(voters) < quorum:
        issues.append(
            f"ERROR [{label}] quorum not met for a '{classification}' change: "
            f"{len(voters)} vote(s) cast ({', '.join(voters) or 'none'}), charter requires "
            f"{quorum}. Abstentions do not count toward quorum."
        )

    required = required_map.get(classification) or []
    if isinstance(required, str):
        required = [required]
    missing = [role for role in required if role not in voters]
    if missing:
        issues.append(
            f"ERROR [{label}] charter requires {sorted(required)} among the voters for a "
            f"'{classification}' change; missing: {sorted(missing)}."
        )

    vetoes = [
        _text(m, "role") for m in board if _text(m, "vote").lower() == "veto"
    ]
    if vetoes and _text(record, "decision").lower().startswith("approved"):
        issues.append(
            f"ERROR [{label}] decision is '{_text(record, 'decision')}' but {sorted(vetoes)} "
            "recorded a veto. Resolve or escalate the veto before approving."
        )
    return issues


def check_risk(record: dict, label: str) -> list[str]:
    """Risk level, rationale and an imported blast radius."""
    issues: list[str] = []
    risk = _mapping(record, "risk")
    if not risk:
        issues.append(f"ERROR [{label}] no 'risk:' block.")
        return issues

    level = _text(risk, "level").lower()
    if level not in RISK_LEVELS:
        issues.append(
            f"ERROR [{label}] risk.level '{level or '(missing)'}' is not one of "
            f"{sorted(RISK_LEVELS)}."
        )
    if not _is_filled(_text(risk, "rationale")):
        issues.append(
            f"ERROR [{label}] risk.rationale is empty. A level with no rationale cannot be "
            "challenged in the meeting or reviewed afterwards."
        )

    blast = _mapping(record, "blast_radius")
    if not blast:
        issues.append(
            f"ERROR [{label}] no 'blast_radius:' block. The board must record what the change "
            "reaches, not estimate it in the room."
        )
        return issues
    if not _is_filled(_text(blast, "source")):
        issues.append(
            f"ERROR [{label}] blast_radius.source is empty. Name the analysis this came from "
            "(for example a /analyze-field-impact run) so it can be re-run."
        )
    if not _rows(blast, "metadata_types"):
        issues.append(
            f"ERROR [{label}] blast_radius.metadata_types is empty. The metadata types in the "
            "package are what the classification matrix is applied to."
        )
    return issues


def check_rollback(record: dict, label: str) -> list[str]:
    """A rollback plan with an owner, rehearsed when the risk is high."""
    issues: list[str] = []
    rollback = _mapping(record, "rollback")
    if not rollback:
        issues.append(
            f"ERROR [{label}] no 'rollback:' block. Approving without one converts a "
            "recoverable deploy into an open-ended outage."
        )
        return issues

    if not _is_filled(_text(rollback, "method")):
        issues.append(f"ERROR [{label}] rollback.method is empty.")
    if not _is_filled(_text(rollback, "owner")):
        issues.append(
            f"ERROR [{label}] rollback.owner is empty. A rollback with no named owner is not "
            "a plan, it is a hope."
        )

    level = _text(_mapping(record, "risk"), "level").lower()
    rehearsed = rollback.get("rehearsed")
    if level == "high" and rehearsed is not True:
        if _is_filled(_text(rollback, "rehearsed_note")):
            issues.append(
                f"WARN [{label}] risk.level is high and rollback.rehearsed is not true; a "
                "waiver note is recorded. Confirm the waiver was approved by the escalation role."
            )
        else:
            issues.append(
                f"ERROR [{label}] risk.level is high but rollback.rehearsed is not true and no "
                "'rehearsed_note' waiver is recorded."
            )
    return issues


def check_evidence(record: dict, root: Path, label: str) -> list[str]:
    """Every cited evidence artefact must resolve to a real file."""
    issues: list[str] = []
    evidence = _rows(record, "test_evidence")
    if not evidence:
        issues.append(
            f"ERROR [{label}] no 'test_evidence:' list. An approval with no evidence is a "
            "signature on an empty page."
        )
        return issues

    for index, item in enumerate(evidence, start=1):
        kind = _text(item, "kind") or f"row {index}"
        artefact = _text(item, "artefact")
        if not _is_filled(artefact):
            issues.append(f"ERROR [{label}] test_evidence '{kind}' has no 'artefact' path.")
            continue
        candidates = [root / artefact, Path(artefact)]
        # also try the path relative to each parent of the manifest root, so a
        # record committed inside artefacts/ can cite artefacts/... or ...
        stripped = artefact.split("/", 1)[1] if "/" in artefact else artefact
        candidates.append(root / stripped)
        if not any(path.exists() for path in candidates):
            issues.append(
                f"ERROR [{label}] test_evidence '{kind}' cites '{artefact}', which does not "
                f"exist under {root}. Approvals must not reference artefacts nobody wrote."
            )
    return issues


def check_window(record: dict, label: str) -> list[str]:
    """The approved window must not sit inside a declared freeze."""
    issues: list[str] = []
    window = _mapping(record, "deploy_window")
    if not window:
        issues.append(f"ERROR [{label}] no 'deploy_window:' block.")
        return issues

    target = _text(window, "target_org")
    if not _is_filled(target):
        issues.append(f"ERROR [{label}] deploy_window.target_org is empty.")
    if not _is_filled(_text(window, "approved_by")):
        issues.append(f"ERROR [{label}] deploy_window.approved_by is empty.")

    start = _parse_date(_text(window, "start"))
    end = _parse_date(_text(window, "end"))
    if start is None or end is None:
        issues.append(
            f"ERROR [{label}] deploy_window.start / .end must be ISO dates or datetimes."
        )
        return issues
    if end < start:
        issues.append(f"ERROR [{label}] deploy_window.end is before deploy_window.start.")

    for index, freeze in enumerate(_rows(record, "freezes"), start=1):
        name = _text(freeze, "name") or f"freeze {index}"
        f_start = _parse_date(_text(freeze, "start"))
        f_end = _parse_date(_text(freeze, "end"))
        if f_start is None or f_end is None:
            issues.append(
                f"ERROR [{label}] freeze '{name}' has an unparseable start or end date."
            )
            continue
        if start <= f_end and f_start <= end:
            issues.append(
                f"ERROR [{label}] deploy window {start}..{end} overlaps freeze '{name}' "
                f"({f_start}..{f_end}). Salesforce advises avoiding deployments during a "
                "service upgrade: a deploy interrupted by downtime is retried from the "
                "beginning. Reschedule, or record a freeze exception from "
                f"'{_text(freeze, 'exception_approver') or 'the escalation role'}'."
            )
    return issues


def check_deploy_options(record: dict, label: str) -> list[str]:
    """DeployOptions the board pinned must be values the Metadata API accepts."""
    issues: list[str] = []
    window = _mapping(record, "deploy_window")
    options = _mapping(window, "deploy_options")
    if not options:
        issues.append(
            f"WARN [{label}] deploy_window has no 'deploy_options'. The same package deployed "
            "with different options is a different change; pin checkOnly, testLevel, "
            "rollbackOnError and ignoreWarnings."
        )
        return issues

    is_production = bool(record.get("production", True))

    test_level = _text(options, "testLevel")
    if test_level and test_level not in TEST_LEVELS:
        issues.append(
            f"ERROR [{label}] deploy_options.testLevel '{test_level}' is not one of "
            f"{sorted(TEST_LEVELS)}."
        )
    if test_level == "NoTestRun" and is_production:
        issues.append(
            f"ERROR [{label}] deploy_options.testLevel NoTestRun applies only to deployments "
            "to development environments (sandbox, Developer Edition, trial)."
        )
    if test_level == "RunSpecifiedTests" and not _rows(options, "runTests"):
        issues.append(
            f"ERROR [{label}] testLevel RunSpecifiedTests requires a non-empty 'runTests' list."
        )

    if options.get("rollbackOnError") is False and is_production:
        issues.append(
            f"ERROR [{label}] deploy_options.rollbackOnError is false. It must be true when "
            "deploying to a production org; false can land the deploy as SucceededPartial."
        )
    if options.get("ignoreWarnings") is True and is_production:
        issues.append(
            f"WARN [{label}] deploy_options.ignoreWarnings is true. The guide states not to "
            "set this for production deployments; warnings are then reported as successes."
        )
    if options.get("checkOnly") is True:
        issues.append(
            f"WARN [{label}] deploy_options.checkOnly is true — this record approves a "
            "validation, not a deployment. Confirm that is intended."
        )
    return issues


def check_quick_deploy(record: dict, label: str) -> list[str]:
    """A quick deploy is only valid for the org it was validated against, for 10 days."""
    issues: list[str] = []
    window = _mapping(record, "deploy_window")
    quick = _mapping(window, "quick_deploy")
    if not quick or quick.get("enabled") is not True:
        return issues

    if not _is_filled(_text(quick, "validation_id")):
        issues.append(
            f"ERROR [{label}] quick_deploy.enabled is true but no 'validation_id' is recorded."
        )

    target = _text(window, "target_org")
    validation_target = _text(quick, "validation_target_org")
    if validation_target and target and validation_target != target:
        issues.append(
            f"ERROR [{label}] quick_deploy was validated against '{validation_target}' but the "
            f"window targets '{target}'. A validation qualifies for quick deploy only for the "
            "target environment it ran against."
        )
    elif not _is_filled(validation_target):
        issues.append(
            f"ERROR [{label}] quick_deploy has no 'validation_target_org'. Quick deploy is "
            "scoped to the environment the validation ran against."
        )

    validated = _parse_date(_text(quick, "validation_date"))
    start = _parse_date(_text(window, "start"))
    if validated is None:
        issues.append(f"ERROR [{label}] quick_deploy has no parseable 'validation_date'.")
    elif start is not None:
        if validated > start:
            issues.append(
                f"ERROR [{label}] quick_deploy.validation_date {validated} is after the window "
                f"opens ({start})."
            )
        elif validated + timedelta(days=QUICK_DEPLOY_VALID_DAYS) < start:
            issues.append(
                f"ERROR [{label}] quick_deploy validation of {validated} expires before the "
                f"window opens on {start}: a validation qualifies for deployment without "
                f"rerunning tests only within {QUICK_DEPLOY_VALID_DAYS} days."
            )
    return issues


def check_emergency(record: dict, label: str) -> list[str]:
    """Emergency records need a dated retrospective; normal ones are warned."""
    issues: list[str] = []
    classification = _text(record, "classification").lower()
    pir = _mapping(record, "post_implementation_review")
    pir_date = _parse_date(_text(pir, "date"))

    if classification == "emergency":
        if pir_date is None:
            issues.append(
                f"ERROR [{label}] an emergency change has no "
                "post_implementation_review.date. An emergency path with no retrospective is "
                "a permanent bypass wearing a temporary label."
            )
        if not _is_filled(_text(pir, "owner")):
            issues.append(
                f"ERROR [{label}] post_implementation_review has no 'owner'."
            )
        if not _is_filled(_text(record, "trigger")):
            issues.append(
                f"ERROR [{label}] an emergency change has no 'trigger'. Record what made this "
                "unable to wait for the standing meeting."
            )
        meeting = _parse_date(_text(record, "meeting_date"))
        if pir_date and meeting and pir_date < meeting:
            issues.append(
                f"ERROR [{label}] post_implementation_review.date {pir_date} is before the "
                f"decision date {meeting}."
            )
    elif classification == "normal" and pir_date is None:
        issues.append(
            f"WARN [{label}] a normal change with no post_implementation_review date. "
            "Confirm the charter exempts normal changes from a review."
        )
    return issues


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _yaml_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for suffix in ("*.yaml", "*.yml"):
        for path in sorted(root.rglob(suffix)):
            if any(part.startswith(".") for part in path.parts):
                continue
            out.append(path)
    return out


def find_decision_records(root: Path) -> list[Path]:
    return [p for p in _yaml_files(root) if "cab_decision:" in _read(p)]


def find_charter(root: Path, explicit: str | None) -> tuple[dict, str]:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            return {}, f"ERROR Charter file not found: {path}"
        return _mapping(parse_yaml_subset(_read(path)), "cab_charter"), ""
    for path in _yaml_files(root):
        text = _read(path)
        if "cab_charter:" in text:
            return _mapping(parse_yaml_subset(text), "cab_charter"), ""
    return {}, (
        "WARN No cab-charter.yaml found under the manifest directory; quorum is being "
        f"checked against the built-in defaults {DEFAULT_QUORUM}. Supply --charter to "
        "check against the board's real charter."
    )


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def check_record_file(path: Path, charter: dict, root: Path) -> list[str]:
    label = path.name
    document = parse_yaml_subset(_read(path))
    record = _mapping(document, "cab_decision")
    if not record:
        return [
            f"ERROR [{label}] no 'cab_decision:' block found. See "
            "references/worked-examples.md section 3 for the shape."
        ]
    issues: list[str] = []
    issues.extend(check_identity(record, label))
    issues.extend(check_quorum(record, charter, label))
    issues.extend(check_risk(record, label))
    issues.extend(check_rollback(record, label))
    issues.extend(check_evidence(record, root, label))
    issues.extend(check_window(record, label))
    issues.extend(check_deploy_options(record, label))
    issues.extend(check_quick_deploy(record, label))
    issues.extend(check_emergency(record, label))
    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a CAB decision record (YAML) against its charter: classification and "
            "decision enums, quorum and required roles, risk and blast radius, rollback "
            "plan, evidence paths that resolve, a deploy window clear of declared freezes, "
            "Metadata API deploy options, quick-deploy validity, and the emergency "
            "retrospective."
        ),
    )
    parser.add_argument("file", nargs="?", help="Path to one CAB decision record.")
    parser.add_argument("--file", dest="file_flag", help="Alternate way to pass the file path.")
    parser.add_argument(
        "--manifest-dir",
        help=(
            "Directory to scan recursively for CAB decision records and the charter. "
            "Evidence paths are resolved relative to this directory."
        ),
    )
    parser.add_argument(
        "--charter",
        help="Path to cab-charter.yaml (otherwise discovered under --manifest-dir).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    root = Path(args.manifest_dir) if args.manifest_dir else Path(".")
    if args.manifest_dir and not root.exists():
        print(f"ERROR Manifest directory not found: {root}", file=sys.stderr)
        return 1

    charter, charter_note = find_charter(root, args.charter)
    if charter_note:
        issues.append(charter_note)

    records: list[Path] = []
    named = args.file_flag or args.file
    if named:
        candidate = Path(named)
        if not candidate.exists():
            issues.append(f"ERROR File not found: {candidate}")
        else:
            records.append(candidate)
    else:
        records = find_decision_records(root)
        if not records:
            issues.append(
                f"ERROR No CAB decision record found under {root}. Expected a YAML file "
                "containing a 'cab_decision:' header. Pass --file to name it explicitly."
            )

    for record in records:
        issues.extend(check_record_file(record, charter, root))

    errors = [i for i in issues if i.startswith("ERROR")]
    warnings = [i for i in issues if i.startswith("WARN")]

    for issue in warnings:
        print(issue, file=sys.stderr)
    for issue in errors:
        print(issue, file=sys.stderr)

    if not issues:
        print(f"No issues found across {len(records)} CAB decision record(s).")
        return 0

    print(
        f"\n{len(errors)} error(s), {len(warnings)} warning(s) across "
        f"{len(records)} record(s).",
        file=sys.stderr,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
