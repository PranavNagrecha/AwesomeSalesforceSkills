#!/usr/bin/env python3
"""check_scoping_rules.py — Scoping rule (RestrictionRule) metadata checker.

Scans a Salesforce metadata directory for scoping rules and validates the
shape errors that actually break them in production:

  * a fabricated ``ScopingRule`` metadata type, folder or package.xml entry
    (there is no such type — a scoping rule is ``RestrictionRule`` with
    ``enforcementType`` set to ``Scoping``)
  * missing required fields, including ``description``, which RestrictionRule
    documents as required and which most generators silently omit
  * a ``targetEntity`` outside the scoping-supported object list
  * SOQL-operator criteria with no ``USING SCOPE EVERYTHING`` at all, using a
    scope other than EVERYTHING, using a ``$User`` variable other than
    ``$User.Id``, or querying an object barred from the SOQL operator
  * ``AND`` / ``OR`` in criteria, which are unsupported outside the SOQL
    operator ("scoping rules support only the EQUALS operator")
  * untyped polymorphic owner references (``Owner.`` instead of ``Owner:User.``)
  * unsupported ``IsPersonAccount`` fields in criteria
  * more active scoping rules on one object than the edition cap allows
  * active scoping rules with no list view wired to ``filterScope ScopingRule``
    — the single most common "my rule does nothing" cause
  * org-specific hardcoded IDs that must be remapped before promotion

Uses stdlib only — no pip dependencies. Python 3.8+.

Usage:
    python3 check_scoping_rules.py --manifest-dir path/to/metadata
    python3 check_scoping_rules.py --manifest-dir . --strict
    python3 check_scoping_rules.py --help

Exit codes:
    0  no ERROR findings (WARN/INFO may still be printed)
    1  at least one ERROR finding, or the manifest directory is unusable
       (with --strict, also exits 1 on WARN)
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce Metadata API namespace.
SF_NS = "http://soap.sforce.com/2006/04/metadata"
NS = {"sf": SF_NS}

# Objects on which a scoping rule (enforcementType Scoping) is supported.
# Source: Scoping Rules Developer Guide — "custom objects and the account,
# case, contact, event, lead, opportunity, and task standard objects."
# Custom objects are matched separately by the __c / __x suffix.
SCOPING_STANDARD_OBJECTS = {
    "Account",
    "Case",
    "Contact",
    "Event",
    "Lead",
    "Opportunity",
    "Task",
}

# Objects that support restriction rules but NOT scoping rules. Naming one of
# these in a Scoping rule is the classic cross-contamination between the two
# features that share the RestrictionRule metadata type.
RESTRICTION_ONLY_OBJECTS = {
    "Contract",
    "Quote",
    "TimeSheet",
    "TimeSheetEntry",
}

# RestrictionRule fields that must be present. `active` is deliberately absent:
# it is optional and defaults to false, which is reported separately.
REQUIRED_RULE_FIELDS = (
    "description",
    "enforcementType",
    "masterLabel",
    "recordFilter",
    "targetEntity",
    "userCriteria",
    "version",
)

# Person-account fields are not supported in scoping rule criteria. Standard
# person-account fields are PascalCase with no __c suffix (PersonDepartment,
# PersonLeadSource); a custom field called Person<Something>__c is a different
# thing and must not be flagged, hence the negative lookahead.
PERSON_ACCOUNT_FIELD_RE = re.compile(r"\bPerson[A-Z][A-Za-z0-9]*\b(?!__[crx])")

# A SOQL operator inside recordFilter: SOQL(<left operand>, <SELECT ...>)
SOQL_OPERATOR_RE = re.compile(r"SOQL\s*\(", re.IGNORECASE)
SELECT_RE = re.compile(r"\bSELECT\b", re.IGNORECASE)
USING_SCOPE_EVERYTHING_RE = re.compile(r"\bUSING\s+SCOPE\s+EVERYTHING\b", re.IGNORECASE)
USING_SCOPE_ANY_RE = re.compile(r"\bUSING\s+SCOPE\s+([A-Za-z_]+)", re.IGNORECASE)
USER_VAR_RE = re.compile(r"\$User\.([A-Za-z0-9_]+)")

# Objects that can't be queried inside a SOQL operator, even when the rule's
# targetEntity is otherwise scopeable. Source: Considerations for Scoping Rules
# — "These objects aren't supported in the SOQL operator". Event and Task are on
# BOTH the scoping-supported list and this one.
SOQL_OPERATOR_BARRED_OBJECTS = {
    "activityhistory",
    "attachment",
    "attachments",
    "event",
    "eventattendee",
    "note",
    "openactivity",
    "task",
}
FROM_OBJECT_RE = re.compile(r"\bFROM\s+([A-Za-z0-9_]+)", re.IGNORECASE)

# Outside the SOQL operator the criteria language has one operator. Source:
# Considerations for Scoping Rules — "Unless you use SOQL, scoping rules support
# only the EQUALS operator. The AND and OR operators aren't supported."
BOOLEAN_OPERATOR_RE = re.compile(r"(?<=\s)(AND|OR)(?=\s)")
QUOTED_LITERAL_RE = re.compile(r"'[^']*'|\"[^\"]*\"")

# `Owner` is polymorphic and must be typed. Queues aren't supported in scoping
# rules, so the only correct typing here is Owner:User.
UNTYPED_OWNER_RE = re.compile(r"(?<![:\w])Owner\.")

# Org-specific key prefixes that do not survive a promotion unchanged.
ORG_SPECIFIC_ID_RE = re.compile(r"\b(00E|00e|012|005)[A-Za-z0-9]{12}([A-Za-z0-9]{3})?\b")
ID_PREFIX_MEANING = {
    "00E": "UserRole",
    "00e": "Profile",
    "012": "RecordType",
    "005": "User",
}

# Edition caps on ACTIVE scoping rules per object. Source: Considerations for
# Scoping Rules — two per object in Developer editions, five per object in
# Performance and Unlimited editions.
CAP_DEVELOPER = 2
CAP_PERFORMANCE_UNLIMITED = 5

# Where rule metadata lives, in both MDAPI and SFDX source layouts.
RULE_DIR_NAMES = ("restrictionRules",)
FABRICATED_RULE_DIR_NAMES = ("scopingRules", "scopingrules")

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"


class Finding:
    """One check result, attributed to a file."""

    def __init__(self, level: str, path: str, message: str) -> None:
        self.level = level
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.level}: {self.path}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Salesforce scoping rules (RestrictionRule with "
            "enforcementType Scoping) in a metadata directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--edition",
        choices=("developer", "performance", "unlimited"),
        default="developer",
        help=(
            "Org edition, used to pick the active-rules-per-object cap "
            "(developer: 2, performance/unlimited: 5). Default: developer."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN findings as well as ERROR findings.",
    )
    return parser.parse_args()


def _text(element, tag: str) -> str:
    """Child text by tag name, namespace-tolerant, '' when absent."""
    found = element.find(f"sf:{tag}", NS)
    if found is None:
        found = element.find(tag)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def check_fabricated_type(root: Path) -> list:
    """A `ScopingRule` type, folder or package.xml entry does not exist."""
    findings = []

    # Case-insensitive filesystems return the same directory for more than one
    # spelling, so dedupe on the resolved path before reporting.
    seen = set()
    for name in FABRICATED_RULE_DIR_NAMES:
        for directory in root.rglob(name):
            if not directory.is_dir():
                continue
            try:
                stat = directory.stat()
                key = (stat.st_dev, stat.st_ino)
            except OSError:
                key = (0, str(directory.resolve()))
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                Finding(
                    ERROR,
                    _rel(directory, root),
                    "there is no scopingRules metadata directory. A scoping rule is a "
                    "RestrictionRule with enforcementType Scoping and belongs in "
                    "restrictionRules/ with a .rule suffix.",
                )
            )

    for manifest in root.rglob("package.xml"):
        try:
            content = manifest.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(WARN, _rel(manifest, root), f"unreadable: {exc}"))
            continue
        if re.search(r"<name>\s*ScopingRule\s*</name>", content):
            findings.append(
                Finding(
                    ERROR,
                    _rel(manifest, root),
                    "package.xml names the type ScopingRule, which does not exist. "
                    "Use <name>RestrictionRule</name>.",
                )
            )

    return findings


def find_rule_files(root: Path) -> list:
    """Every .rule file under a restrictionRules/ directory, plus strays."""
    candidates = set()
    for name in RULE_DIR_NAMES:
        for directory in root.rglob(name):
            if directory.is_dir():
                candidates.update(p for p in directory.glob("*.rule*") if p.is_file())
    # Files named *.rule-meta.xml or *.rule anywhere else still get parsed, so a
    # misplaced rule is checked rather than silently skipped.
    for pattern in ("*.rule", "*.rule-meta.xml"):
        candidates.update(p for p in root.rglob(pattern) if p.is_file())
    return sorted(candidates)


def check_soql_operator(criteria: str, rel_path: Path, root: Path) -> list:
    """Constraints that apply only inside a SOQL(...) record filter."""
    findings = []
    where = _rel(rel_path, root)

    if not SOQL_OPERATOR_RE.search(criteria):
        return findings

    selects = len(SELECT_RE.findall(criteria))
    everythings = len(USING_SCOPE_EVERYTHING_RE.findall(criteria))
    if selects and everythings == 0:
        findings.append(
            Finding(
                ERROR,
                where,
                f"recordFilter has {selects} SELECT statement(s) and no USING SCOPE "
                "EVERYTHING. The SELECT statement must include it.",
            )
        )
    elif selects and everythings < selects:
        # Deliberately WARN, not ERROR: Salesforce's own published nested example
        # (BranchRuleOnAccount / BranchRuleOnLead) has two SELECTs and one USING
        # SCOPE EVERYTHING, contradicting the prose rule on the same page. Failing
        # that metadata would fail the platform's canonical sample. See
        # references/gotchas.md Gotcha 5 and the well-architected Contradiction Log.
        findings.append(
            Finding(
                WARN,
                where,
                f"recordFilter has {selects} SELECT statement(s) but only {everythings} "
                "USING SCOPE EVERYTHING. The documented rule says every nested SELECT "
                "must carry it; Salesforce's own nested example carries it only on the "
                "outer query. Write the compliant superset and verify in a sandbox.",
            )
        )

    for obj in FROM_OBJECT_RE.findall(criteria):
        lowered = obj.lower()
        if lowered in SOQL_OPERATOR_BARRED_OBJECTS or lowered.endswith("tag"):
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"recordFilter queries {obj} inside a SOQL operator. "
                    "ActivityHistory, Attachments, Event, EventAttendee, Note, "
                    "OpenActivity, Task and tag objects aren't supported there — "
                    "Event and Task are scopeable target entities and still barred "
                    "from the subquery.",
                )
            )

    for scope in USING_SCOPE_ANY_RE.findall(criteria):
        if scope.upper() != "EVERYTHING":
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"recordFilter uses USING SCOPE {scope}. EVERYTHING is the only "
                    "valid scope clause syntax for scoping rules.",
                )
            )

    for variable in USER_VAR_RE.findall(criteria):
        if variable != "Id":
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"recordFilter uses $User.{variable} inside a SOQL operator. Only "
                    "$User.Id is supported there (other $User fields are fine in a "
                    "plain comparison filter).",
                )
            )

    return findings


def check_criteria(rule_path: Path, root: Path, record_filter: str, user_criteria: str) -> list:
    """Criteria-language constraints that apply to both criteria fields."""
    findings = []
    where = _rel(rule_path, root)

    findings.extend(check_soql_operator(record_filter, rule_path, root))

    for label, criteria in (("recordFilter", record_filter), ("userCriteria", user_criteria)):
        if not criteria:
            continue

        if UNTYPED_OWNER_RE.search(criteria):
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"{label} contains an untyped 'Owner.' reference. Owner is "
                    "polymorphic and must be typed; queues aren't supported in "
                    "scoping rules, so write Owner:User.",
                )
            )

        # AND / OR are unsupported outside the SOQL operator. Quoted literals are
        # stripped first so a value like 'Smith AND Sons' isn't misread as syntax.
        if not SOQL_OPERATOR_RE.search(criteria):
            bare = QUOTED_LITERAL_RE.sub(" ", criteria)
            for operator in set(BOOLEAN_OPERATOR_RE.findall(bare)):
                findings.append(
                    Finding(
                        ERROR,
                        where,
                        f"{label} uses the {operator} operator. Unless you use the "
                        "SOQL operator, scoping rules support only EQUALS — AND and "
                        "OR aren't supported. Precompute the combination into one "
                        "field, or move to the API-only SOQL operator.",
                    )
                )

        for field in PERSON_ACCOUNT_FIELD_RE.findall(criteria):
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"{label} references {field}. IsPersonAccount fields on the "
                    "account object are not supported in scoping rule criteria.",
                )
            )

        for match in ORG_SPECIFIC_ID_RE.finditer(criteria):
            prefix = match.group(1)
            findings.append(
                Finding(
                    WARN,
                    where,
                    f"{label} hardcodes {match.group(0)} "
                    f"({ID_PREFIX_MEANING.get(prefix, 'org-specific')} ID). This value "
                    "differs per org and must be remapped before promotion — a stale "
                    "ID matches nobody and reports no error.",
                )
            )

    return findings


def check_rule_file(rule_path: Path, root: Path) -> tuple:
    """Validate one .rule file. Returns (findings, target_entity_or_'', is_active)."""
    findings = []
    where = _rel(rule_path, root)

    try:
        tree = ET.parse(rule_path)
    except ET.ParseError as exc:
        return [Finding(ERROR, where, f"not parseable as XML: {exc}")], "", False
    except OSError as exc:
        return [Finding(ERROR, where, f"unreadable: {exc}")], "", False

    element = tree.getroot()
    root_tag = _local_name(element.tag)
    if root_tag == "ScopingRule":
        findings.append(
            Finding(
                ERROR,
                where,
                "root element is <ScopingRule>, which is not a metadata type. Use "
                "<RestrictionRule> with <enforcementType>Scoping</enforcementType>.",
            )
        )
    elif root_tag != "RestrictionRule":
        return findings, "", False

    enforcement = _text(element, "enforcementType")
    if enforcement != "Scoping":
        # A Restrict / FieldRestrict rule is a different feature; only report the
        # per-object-per-user interaction, which is this skill's concern.
        target = _text(element, "targetEntity")
        if target:
            findings.append(
                Finding(
                    INFO,
                    where,
                    f"enforcementType is '{enforcement or '(missing)'}' on "
                    f"{target}. Confirm its userCriteria cannot match a user who is "
                    "also matched by a scoping rule on the same object — only one "
                    "scoping or restriction rule per object per user is supported.",
                )
            )
        return findings, "", False

    for field in REQUIRED_RULE_FIELDS:
        if not _text(element, field):
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"required RestrictionRule field <{field}> is missing or empty."
                    + (
                        " description is documented as required on RestrictionRule, "
                        "unlike on most metadata types."
                        if field == "description"
                        else ""
                    ),
                )
            )

    target = _text(element, "targetEntity")
    if target:
        is_custom = target.endswith("__c") or target.endswith("__x")
        if not is_custom and target not in SCOPING_STANDARD_OBJECTS:
            if target in RESTRICTION_ONLY_OBJECTS:
                findings.append(
                    Finding(
                        ERROR,
                        where,
                        f"targetEntity {target} supports restriction rules but not "
                        "scoping rules. Scoping supports custom objects plus Account, "
                        "Case, Contact, Event, Lead, Opportunity, Task.",
                    )
                )
            else:
                findings.append(
                    Finding(
                        ERROR,
                        where,
                        f"targetEntity {target} is not on the scoping-supported object "
                        "list: custom objects plus Account, Case, Contact, Event, "
                        "Lead, Opportunity, Task.",
                    )
                )

    record_filter = _text(element, "recordFilter")
    user_criteria = _text(element, "userCriteria")
    findings.extend(check_criteria(rule_path, root, record_filter, user_criteria))

    if target == "Event" and "IsGroupEvent" in (record_filter + user_criteria):
        findings.append(
            Finding(
                ERROR,
                where,
                "criteria reference Event.IsGroupEvent. Salesforce states not to "
                "create rules on that field.",
            )
        )

    active_raw = _text(element, "active").lower()
    is_active = active_raw == "true"
    if not active_raw:
        findings.append(
            Finding(
                WARN,
                where,
                "<active> is absent and defaults to false. A deployed-but-inactive "
                "rule is the most common 'my scoping rule does nothing' cause — set "
                "it explicitly.",
            )
        )

    return findings, target, is_active


def check_edition_caps(active_by_entity: dict, cap: int, edition: str) -> list:
    findings = []
    for entity, paths in sorted(active_by_entity.items()):
        if len(paths) > cap:
            findings.append(
                Finding(
                    ERROR,
                    ", ".join(sorted(paths)),
                    f"{len(paths)} active scoping rules on {entity}, above the "
                    f"{edition}-edition cap of {cap} per object.",
                )
            )
        elif len(paths) > 1:
            findings.append(
                Finding(
                    INFO,
                    ", ".join(sorted(paths)),
                    f"{len(paths)} active scoping rules on {entity}. Confirm their "
                    "userCriteria are disjoint — only one scoping or restriction rule "
                    "per object per user is supported, and overlap produces "
                    "unpredictable behaviour rather than an error.",
                )
            )
    return findings


def check_listview_wiring(root: Path, scoped_entities: set) -> list:
    """An active scoping rule with no list view wired to it is invisible."""
    findings = []
    if not scoped_entities:
        return findings

    wired = set()
    for listview in root.rglob("*.listView-meta.xml"):
        try:
            content = listview.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(r"<filterScope>\s*ScopingRule\s*</filterScope>", content):
            # force-app/main/default/objects/<Object>/listViews/<Name>.listView-meta.xml
            parts = listview.parts
            if "listViews" in parts:
                index = parts.index("listViews")
                if index >= 1:
                    wired.add(parts[index - 1])

    for entity in sorted(scoped_entities):
        if entity not in wired:
            findings.append(
                Finding(
                    WARN,
                    f"objects/{entity}/listViews/",
                    "an active scoping rule targets this object but no list view in "
                    "this metadata sets <filterScope>ScopingRule</filterScope>. List "
                    "views apply a scoping rule only when Filter by scope is selected, "
                    "so the rule is live and invisible to users.",
                )
            )
    return findings


def check_scoping_rules(manifest_dir: Path, edition: str) -> list:
    findings = []

    if not manifest_dir.exists():
        return [Finding(ERROR, str(manifest_dir), "manifest directory not found.")]
    if not manifest_dir.is_dir():
        return [Finding(ERROR, str(manifest_dir), "manifest path is not a directory.")]

    findings.extend(check_fabricated_type(manifest_dir))

    rule_files = find_rule_files(manifest_dir)
    if not rule_files:
        findings.append(
            Finding(
                INFO,
                str(manifest_dir),
                "no .rule files found. Scoping rules built in Object Manager and never "
                "retrieved into source are invisible to this check — retrieve the "
                "RestrictionRule type before trusting a clean result.",
            )
        )
        return findings

    active_by_entity: dict = {}
    scoped_entities = set()

    for rule_path in rule_files:
        file_findings, target, is_active = check_rule_file(rule_path, manifest_dir)
        findings.extend(file_findings)
        if target and is_active:
            active_by_entity.setdefault(target, []).append(_rel(rule_path, manifest_dir))
            scoped_entities.add(target)

    cap = CAP_DEVELOPER if edition == "developer" else CAP_PERFORMANCE_UNLIMITED
    findings.extend(check_edition_caps(active_by_entity, cap, edition))
    findings.extend(check_listview_wiring(manifest_dir, scoped_entities))

    return findings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    findings = check_scoping_rules(manifest_dir, args.edition)

    errors = [f for f in findings if f.level == ERROR]
    warnings = [f for f in findings if f.level == WARN]
    notes = [f for f in findings if f.level == INFO]

    for finding in errors + warnings:
        print(str(finding), file=sys.stderr)
    for finding in notes:
        print(str(finding))

    print(
        f"\n{len(errors)} error(s), {len(warnings)} warning(s), {len(notes)} note(s).",
        file=sys.stderr,
    )

    if errors:
        print(
            "Fix the ERROR findings above. See "
            "skills/admin/scoping-rules/references/gotchas.md for the mechanism "
            "behind each one.",
            file=sys.stderr,
        )
        return 1
    if warnings and args.strict:
        print("--strict: failing on WARN findings.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
