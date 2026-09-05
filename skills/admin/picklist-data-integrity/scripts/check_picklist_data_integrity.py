#!/usr/bin/env python3
"""Lint picklist governance: field metadata + the value-change record.

Two independent surfaces, either or both:

`--manifest-dir` — a retrieved metadata tree (e.g. `force-app/main/default`).
  Checks, in severity order:

    WARN  1. A picklist `<valueSet>` with `<restricted>false</restricted>`.
             Unrestricted writes are not rejected; an unmatched value creates a
             new inactive picklist value in the definition, matched
             case-insensitively (object_reference.txt:2363-2367). Without a
             reconciliation job that drift is invisible.
             references/gotchas.md § 2, § 10
    WARN  2. Deactivated values (`<isActive>false</isActive>`) present in the
             file. Deactivation never removes the value from records
             (references/gotchas.md § 1) — this is a prompt to prove the
             migration ran, not a defect.
    WARN  3. A validation rule in the sibling `validationRules/` folder that
             tests `ISPICKVAL(<this field>, ...)` for every active value —
             duplicating the picklist's own membership enforcement.
             references/llm-anti-patterns.md § 2
    INFO  4. `restricted` false AND no `<valueSetName>` — a local, unrestricted
             value list. The riskiest shape there is: it is the only one whose
             retrieve is documented to omit inactive values
             (api_meta.txt:47521-47526), so the file is a partial snapshot.
    INFO  5. A `<value>` whose `<label>` differs from its `<fullName>` with no
             rename/retirement note in its `<description>`. Label and stored key
             have diverged and nothing in source control says why; report
             filters and integration mappings keyed on the label are exposed.
             references/gotchas.md § 14

`--governance-dir` / `--governance-file` — the YAML value-change records
  described in references/metadata-examples.md §6. Checks:

    ERROR required keys present: id, object, field, value, action, reason,
          affected_records, owner, date
    ERROR `action` is one of: add, deactivate, replace, rename-label
    ERROR `replacement_value` present and non-empty when action is `replace`
    ERROR `affected_records` is a non-negative integer
    ERROR `owner` is non-empty
    WARN  `audit_environment` missing or not `production` — a sandbox count is
          not the count
    WARN  `rollback` missing on a `deactivate` or `replace` record

Exit status: 1 if any ERROR or WARN was emitted, 0 otherwise. INFO never
fails the run on its own; pass `--fail-on-info` to make it.

Stdlib only. No network. Reads nothing outside the paths you name.

Usage:
    python3 check_picklist_data_integrity.py --manifest-dir force-app/main/default
    python3 check_picklist_data_integrity.py --governance-dir governance/picklists
    python3 check_picklist_data_integrity.py \\
        --manifest-dir force-app/main/default \\
        --governance-dir governance/picklists
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"

_PICKLIST_TYPES = {"Picklist", "MultiselectPicklist"}

_REQUIRED_GOVERNANCE_KEYS = (
    "id",
    "object",
    "field",
    "value",
    "action",
    "reason",
    "affected_records",
    "owner",
    "date",
)

_GOVERNANCE_ACTIONS = ("add", "deactivate", "replace", "rename-label")

# Words that, in a CustomValue <description>, count as an explanation for a
# label that no longer matches its stored key.
_RENAME_NOTE_WORDS = (
    "rename",
    "renamed",
    "relabel",
    "relabelled",
    "relabeled",
    "label",
    "retire",
    "retired",
    "legacy",
    "deprecat",
    "formerly",
    "was ",
    "superseded",
)


class Finding:
    """One lint result. Severity decides the exit code, not the caller."""

    __slots__ = ("severity", "path", "message")

    def __init__(self, severity: str, path: Path | str, message: str) -> None:
        self.severity = severity
        self.path = str(path)
        self.message = message

    def render(self) -> str:
        return f"{self.severity}: {self.path}: {self.message}"


# --------------------------------------------------------------------------
# XML helpers
#
# NEVER write `el.find(a) or el.find(b)` on ElementTree: an Element with no
# children is falsy even when it exists, so a present-but-empty element is
# silently skipped. Everything below goes through these helpers, which test
# `is not None`.
# --------------------------------------------------------------------------


def _strip_ns(tag: str) -> str:
    return tag[len(_NS_TAG):] if tag.startswith(_NS_TAG) else tag


def _child(parent: ET.Element | None, name: str) -> ET.Element | None:
    """First direct child named `name`, namespaced or not. None if absent."""
    if parent is None:
        return None
    found = parent.find(f"{_NS_TAG}{name}")
    if found is not None:
        return found
    return parent.find(name)


def _children(parent: ET.Element | None, name: str) -> list[ET.Element]:
    if parent is None:
        return []
    found = parent.findall(f"{_NS_TAG}{name}")
    if found:
        return found
    return parent.findall(name)


def _text(parent: ET.Element | None, name: str) -> str:
    el = _child(parent, name)
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _is_false(parent: ET.Element | None, name: str) -> bool:
    """True only when the element exists and says false."""
    el = _child(parent, name)
    if el is None or el.text is None:
        return False
    return el.text.strip().lower() == "false"


def _is_true(parent: ET.Element | None, name: str) -> bool:
    el = _child(parent, name)
    if el is None or el.text is None:
        return False
    return el.text.strip().lower() == "true"


# --------------------------------------------------------------------------
# Field metadata checks
# --------------------------------------------------------------------------


def _is_picklist_field(root: ET.Element) -> bool:
    if _strip_ns(root.tag) != "CustomField":
        return False
    return _text(root, "type") in _PICKLIST_TYPES


def _field_api_name(root: ET.Element, path: Path) -> str:
    name = _text(root, "fullName")
    if name:
        return name
    return path.name.replace(".field-meta.xml", "")


def _has_rename_note(value_el: ET.Element) -> bool:
    description = _text(value_el, "description").lower()
    if not description:
        return False
    return any(word in description for word in _RENAME_NOTE_WORDS)


def scan_field(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding(ERROR, path, f"not well-formed XML: {exc}")]
    except OSError as exc:
        return [Finding(ERROR, path, f"unreadable: {exc}")]

    if not _is_picklist_field(root):
        return findings

    field = _field_api_name(root, path)

    for value_set in _children(root, "valueSet"):
        unrestricted = _is_false(value_set, "restricted")
        value_set_name = _text(value_set, "valueSetName")

        # 1. Unrestricted.
        if unrestricted:
            findings.append(
                Finding(
                    WARN,
                    path,
                    f"picklist `{field}` is Unrestricted — the API does not "
                    "enforce the value list, and an unmatched write creates a "
                    "new inactive picklist value matched case-insensitively "
                    "(object_reference.txt:2363-2367). Pair it with the "
                    "stored-vs-defined audit in "
                    "references/metadata-examples.md §1 or make it restricted "
                    "(references/gotchas.md § 2, § 10)",
                )
            )

            # 4. Unrestricted AND local (no global value set behind it).
            if not value_set_name:
                findings.append(
                    Finding(
                        INFO,
                        path,
                        f"picklist `{field}` is a local, unrestricted value "
                        "list (restricted=false, no <valueSetName>) — the one "
                        "shape whose retrieve is documented to return active "
                        "values only (api_meta.txt:47521-47526). Treat this "
                        "file as a partial snapshot and reconcile it against "
                        "the org before deploying it anywhere",
                    )
                )

        definition = _child(value_set, "valueSetDefinition")
        values = _children(definition, "value")

        # 2. Deactivated values still in the file.
        deactivated = [v for v in values if _is_false(v, "isActive")]
        if deactivated:
            names = [_text(v, "fullName") or "?" for v in deactivated[:5]]
            more = "…" if len(deactivated) > 5 else ""
            findings.append(
                Finding(
                    WARN,
                    path,
                    f"picklist `{field}` has {len(deactivated)} deactivated "
                    f"value(s) ({', '.join(names)}{more}) — deactivation does "
                    "NOT remove the value from existing records. Confirm the "
                    "migration ran and the stored count is zero "
                    "(references/gotchas.md § 1; runbook in "
                    "references/metadata-examples.md §3)",
                )
            )

        # 5. Label / stored-key drift with no note.
        for value_el in values:
            full_name = _text(value_el, "fullName")
            label = _text(value_el, "label")
            if not full_name or not label or full_name == label:
                continue
            if _has_rename_note(value_el):
                continue
            findings.append(
                Finding(
                    INFO,
                    path,
                    f"picklist `{field}` value `{full_name}` displays as "
                    f"\"{label}\" and carries no note saying why. A label "
                    "that never matched the key is fine; a label that was "
                    "CHANGED is not, because report filters, list views and "
                    "hand-typed integration mappings are keyed on the label "
                    "and none of them are greppable "
                    "(references/gotchas.md § 14). One line in <description> "
                    "settles which case this is "
                    "(limit 255 chars, api_meta.txt:47517-47520)",
                )
            )

    return findings


def scan_validation_rules(path: Path) -> list[Finding]:
    """Flag a validation rule that re-enumerates the field's own value list."""
    findings: list[Finding] = []
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return findings  # already reported by scan_field

    if not _is_picklist_field(root):
        return findings

    field = _text(root, "fullName")
    if not field:
        return findings

    active_values: set[str] = set()
    for value_set in _children(root, "valueSet"):
        definition = _child(value_set, "valueSetDefinition")
        for value_el in _children(definition, "value"):
            full_name = _text(value_el, "fullName")
            if full_name and not _is_false(value_el, "isActive"):
                active_values.add(full_name)

    if not active_values:
        return findings

    # objects/<Object>/fields/<X>.field-meta.xml  ->  objects/<Object>/
    rules_dir = path.parent.parent / "validationRules"
    if not rules_dir.is_dir():
        return findings

    pattern = re.compile(
        r"ISPICKVAL\s*\(\s*[\w.]*"
        + re.escape(field)
        + r"\s*,\s*[\"']([^\"']+)[\"']\s*\)",
        re.IGNORECASE,
    )

    for rule_path in sorted(rules_dir.glob("*.validationRule-meta.xml")):
        try:
            text = rule_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        covered = set(pattern.findall(text)) & active_values
        if covered and covered >= active_values:
            findings.append(
                Finding(
                    WARN,
                    rule_path,
                    f"formula tests ISPICKVAL on `{field}` for every active "
                    "value — this duplicates the picklist's own membership "
                    "enforcement, and adding a value now means editing two "
                    "places. Use the restricted picklist alone for "
                    "membership; keep validation rules for cross-field rules "
                    "(references/llm-anti-patterns.md § 2)",
                )
            )

    return findings


def scan_manifest_dir(root: Path) -> list[Finding]:
    if not root.exists():
        return [Finding(ERROR, root, "--manifest-dir does not exist")]
    if not root.is_dir():
        return [Finding(ERROR, root, "--manifest-dir is not a directory")]

    findings: list[Finding] = []
    fields = sorted(root.rglob("*.field-meta.xml"))
    for field_path in fields:
        findings.extend(scan_field(field_path))
        findings.extend(scan_validation_rules(field_path))
    if not fields:
        findings.append(
            Finding(INFO, root, "no *.field-meta.xml found under --manifest-dir")
        )
    return findings


# --------------------------------------------------------------------------
# Governance record checks
#
# Deliberately a tiny top-level-key reader rather than PyYAML: skill-local
# checkers stay stdlib-only. It understands `key: scalar`, `key: >` / `key: |`
# folded blocks, and `key:` followed by an indented block (list or map), which
# is every shape used in references/metadata-examples.md §6.
# --------------------------------------------------------------------------

_TOP_LEVEL_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$")


def parse_governance_yaml(text: str) -> dict[str, str]:
    """Return {top-level key: scalar text}. Nested blocks map to "<block>"."""
    parsed: dict[str, str] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = _TOP_LEVEL_KEY.match(line)
        if match is None:
            continue
        key, raw = match.group(1), match.group(2).strip()
        if raw.startswith("#"):
            raw = ""
        if raw in (">", "|", ">-", "|-", ">+", "|+"):
            block: list[str] = []
            while index < len(lines):
                nxt = lines[index]
                if nxt.strip() and not nxt.startswith((" ", "\t")):
                    break
                block.append(nxt.strip())
                index += 1
            parsed[key] = " ".join(part for part in block if part).strip()
        elif raw == "":
            has_block = False
            while index < len(lines):
                nxt = lines[index]
                if not nxt.strip() or nxt.lstrip().startswith("#"):
                    index += 1
                    continue
                if not nxt.startswith((" ", "\t")):
                    break
                has_block = True
                index += 1
            parsed[key] = "<block>" if has_block else ""
        else:
            parsed[key] = raw.strip().strip('"').strip("'")
    return parsed


def scan_governance_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [Finding(ERROR, path, f"unreadable: {exc}")]

    record = parse_governance_yaml(text)
    if not record:
        return [
            Finding(
                ERROR,
                path,
                "no top-level keys parsed — is this a governance record? "
                "Shape: references/metadata-examples.md §6",
            )
        ]

    missing = [
        key
        for key in _REQUIRED_GOVERNANCE_KEYS
        if key not in record or record[key] == ""
    ]
    if missing:
        findings.append(
            Finding(
                ERROR,
                path,
                "missing or empty required key(s): "
                + ", ".join(missing)
                + " (required set: "
                + ", ".join(_REQUIRED_GOVERNANCE_KEYS)
                + ")",
            )
        )

    action = record.get("action", "")
    if action and action not in _GOVERNANCE_ACTIONS:
        findings.append(
            Finding(
                ERROR,
                path,
                f"action `{action}` is not one of: "
                + ", ".join(_GOVERNANCE_ACTIONS),
            )
        )

    if action == "replace" and not record.get("replacement_value", ""):
        findings.append(
            Finding(
                ERROR,
                path,
                "action is `replace` but `replacement_value` is missing or "
                "empty — a replacement with no target is a deactivation that "
                "orphans records",
            )
        )

    affected = record.get("affected_records", "")
    if affected and affected != "<block>":
        cleaned = affected.replace(",", "").replace("_", "")
        if not cleaned.isdigit():
            findings.append(
                Finding(
                    ERROR,
                    path,
                    f"`affected_records` is `{affected}` — it must be a "
                    "non-negative integer measured by the stored-vs-defined "
                    "audit (references/metadata-examples.md §1), not an "
                    "estimate or a range",
                )
            )

    owner = record.get("owner", "")
    if owner == "<block>":
        findings.append(
            Finding(
                ERROR,
                path,
                "`owner` must be a single named person, not a list or a team",
            )
        )

    environment = record.get("audit_environment", "")
    if environment.lower() != "production":
        findings.append(
            Finding(
                WARN,
                path,
                f"`audit_environment` is `{environment or 'absent'}` — the "
                "record count that matters is the production one; a sandbox "
                "has lost the integration traffic that creates phantom values",
            )
        )

    if action in ("deactivate", "replace") and not record.get("rollback", ""):
        findings.append(
            Finding(
                WARN,
                path,
                f"action is `{action}` with no `rollback` — record the "
                "pre-image CSV path and the re-activation step before "
                "deploying (references/metadata-examples.md §4 step 0)",
            )
        )

    return findings


def scan_governance_dir(root: Path) -> list[Finding]:
    if not root.exists():
        return [Finding(ERROR, root, "--governance-dir does not exist")]
    if not root.is_dir():
        return [Finding(ERROR, root, "--governance-dir is not a directory")]

    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in (".yml", ".yaml")
    )
    if not files:
        return [
            Finding(INFO, root, "no *.yml / *.yaml governance records found")
        ]

    findings: list[Finding] = []
    for path in files:
        findings.extend(scan_governance_file(path))
    return findings


# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Lint picklist governance: field metadata (unrestricted value "
            "lists, deactivated values, label/key drift, validation rules "
            "duplicating picklist membership) and the YAML value-change "
            "records described in references/metadata-examples.md §6."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        dest="manifest_dir",
        default=None,
        help="Root of a retrieved metadata tree, e.g. force-app/main/default.",
    )
    parser.add_argument(
        "--src-root",
        dest="manifest_dir",
        default=argparse.SUPPRESS,
        help="Deprecated alias for --manifest-dir.",
    )
    parser.add_argument(
        "--governance-dir",
        default=None,
        help="Directory of *.yml value-change records to lint.",
    )
    parser.add_argument(
        "--governance-file",
        default=None,
        help="A single value-change record to lint.",
    )
    parser.add_argument(
        "--fail-on-info",
        action="store_true",
        help="Exit 1 on INFO findings too (default: INFO does not fail).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    manifest_dir = getattr(args, "manifest_dir", None)
    if not manifest_dir and not args.governance_dir and not args.governance_file:
        parser.print_usage(sys.stderr)
        print(
            "ERROR: give at least one of --manifest-dir, --governance-dir, "
            "--governance-file.",
            file=sys.stderr,
        )
        return 1

    findings: list[Finding] = []
    if manifest_dir:
        findings.extend(scan_manifest_dir(Path(manifest_dir)))
    if args.governance_dir:
        findings.extend(scan_governance_dir(Path(args.governance_dir)))
    if args.governance_file:
        path = Path(args.governance_file)
        if not path.is_file():
            findings.append(
                Finding(ERROR, path, "--governance-file is not a file")
            )
        else:
            findings.extend(scan_governance_file(path))

    blocking = [f for f in findings if f.severity in (ERROR, WARN)]
    informational = [f for f in findings if f.severity == INFO]

    for finding in findings:
        stream = sys.stdout if finding.severity == INFO else sys.stderr
        print(finding.render(), file=stream)

    if not findings:
        print("OK: no picklist governance findings.")
        return 0

    print(
        f"\n{len(blocking)} blocking finding(s), "
        f"{len(informational)} informational.",
        file=sys.stderr,
    )

    if blocking:
        return 1
    if informational and args.fail_on_info:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        sys.exit(1)  # findings present — explicit failure path for CI and the repo validator
    sys.exit(0)
