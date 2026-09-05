#!/usr/bin/env python3
"""Checker for the User Access Policies skill.

Parses ``UserAccessPolicy`` metadata in a local Salesforce project and reports
configuration problems that deploy cleanly but behave wrongly.

Grounding (Metadata API Developer Guide, ``UserAccessPolicy`` section, v62):

* ``booleanFilter`` is required and combines filter rows by their ``sortOrder``
  ("the booleanFilter can be 1 AND 2 or 1 OR 2") -- OR is supported.
* ``order`` is an int from 0 to 10,000 and "only the active policy with the
  lowest order value is applied" when a user matches several policies. It is
  required only when ``status`` is ``Active``.
* ``action`` is ``Grant``/``Revoke`` on a ``UserAccessPolicyAction`` child, so
  one policy may contain both. Action ``type`` and filter ``type`` are
  restricted enums.
* Deploying ``status`` ``Active`` results in ``Design`` in the target org.

Uses stdlib only -- no pip dependencies.

Usage::

    python3 check_user_access_policies.py --manifest-dir force-app/main/default
    python3 check_user_access_policies.py --manifest-dir force-app/main/default --json

Checks performed:
    1. booleanFilter is present, parseable, references only declared sortOrder
       values, and leaves no filter row unreferenced. sortOrder values unique.
    2. status and triggerType are valid enum values; a policy deployed Active is
       reported (it will land as Design).
    3. order is an integer 0-10,000, present when status is Active, and unique
       across active policies.
    4. Each action's type/action are valid enum values, and its target resolves
       to a component present in the manifest when that component type is
       deployable and any of that type is present.
    5. Filter row shape: type=User rows set target to "User" and populate
       columnName/value; other types leave those unused. Operations are valid.
    6. Two active policies that share a filter row (so they can match the same
       user) but carry different orders and conflicting action sets are warned
       about -- the lower order wins outright and the other never runs.

Exit code 0 when nothing is reported, 1 when any ERROR or WARN is emitted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

# --- Enumerations from the Metadata API Developer Guide --------------------

STATUS_VALUES = {
    "Active",
    "Completed",
    "Design",
    "Failed",
    "Migrate",
    "Testing",
    "Updating",
}
TRIGGER_TYPE_VALUES = {"Create", "CreateAndUpdate", "Update"}
ACTION_VALUES = {"Grant", "Revoke"}
ACTION_TARGET_TYPES = {
    "Group",
    "PackageLicense",
    "PermissionSet",
    "PermissionSetGroup",
    "PermissionSetLicense",
    "Queue",
}
FILTER_TARGET_TYPES = ACTION_TARGET_TYPES | {"Profile", "User", "UserRole"}
FILTER_OPERATIONS = {
    "equals",
    "equalsIgnoreCase",
    "in",
    "includes",
    "notEquals",
}

ORDER_MIN = 0
ORDER_MAX = 10000

# Action/filter target types that correspond to a deployable metadata folder.
# PermissionSetLicense and PackageLicense are org-provisioned, not deployable,
# so a target of those types can never be resolved from a manifest.
DEPLOYABLE_TARGETS: dict[str, tuple[str, str]] = {
    # type -> (folder, file suffix without the -meta.xml tail)
    "PermissionSet": ("permissionsets", ".permissionset"),
    "PermissionSetGroup": ("permissionsetgroups", ".permissionsetgroup"),
    "Group": ("groups", ".group"),
    "Queue": ("queues", ".queue"),
    "Profile": ("profiles", ".profile"),
    "UserRole": ("roles", ".role"),
}

NS_RE = re.compile(r"\{.*?\}")
BOOLEAN_TOKEN_RE = re.compile(r"\d+|AND|OR|NOT|\(|\)", re.IGNORECASE)


# --- XML helpers -----------------------------------------------------------
#
# A leaf ElementTree Element is falsy, so ``el.find(a) or el.find(b)`` silently
# discards a real match. Every lookup below tests ``is not None`` explicitly.


def _local(tag: str) -> str:
    return NS_RE.sub("", tag)


def _children(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in element if _local(child.tag) == name]


def _child_text(element: ElementTree.Element, name: str) -> str | None:
    """Return the stripped text of the first child called ``name``, else None."""
    for child in element:
        if _local(child.tag) == name:
            if child.text is None:
                return ""
            return child.text.strip()
    return None


def _parse_xml_root(path: Path) -> ElementTree.Element | None:
    try:
        return ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError):
        return None


# --- Discovery -------------------------------------------------------------


def find_policy_files(manifest_dir: Path) -> list[Path]:
    """Return every UserAccessPolicy file under manifest_dir, deduplicated."""
    found: list[Path] = []
    for pattern in (
        "*.useraccesspolicy",
        "*.useraccesspolicy-meta.xml",
        "useraccesspolicies/*.xml",
    ):
        found.extend(manifest_dir.rglob(pattern))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in sorted(found):
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def index_manifest_components(manifest_dir: Path) -> dict[str, set[str]]:
    """Map each deployable target type to the developer names present locally."""
    index: dict[str, set[str]] = {}
    for type_name, (folder, suffix) in DEPLOYABLE_TARGETS.items():
        names: set[str] = set()
        for path in manifest_dir.rglob(f"{folder}/*{suffix}*"):
            if not path.is_file():
                continue
            name = path.name
            for tail in (f"{suffix}-meta.xml", suffix):
                if name.endswith(tail):
                    name = name[: -len(tail)]
                    break
            names.add(name)
        index[type_name] = names
    return index


# --- Policy model ----------------------------------------------------------


class Policy:
    def __init__(self, path: Path, root: ElementTree.Element) -> None:
        self.path = path
        self.name = path.name
        self.label = _child_text(root, "masterLabel")
        self.boolean_filter = _child_text(root, "booleanFilter")
        self.status = _child_text(root, "status")
        self.trigger_type = _child_text(root, "triggerType")
        self.order_raw = _child_text(root, "order")
        self.filters = [
            {
                "sortOrder": _child_text(el, "sortOrder"),
                "type": _child_text(el, "type"),
                "operation": _child_text(el, "operation"),
                "target": _child_text(el, "target"),
                "columnName": _child_text(el, "columnName"),
                "value": _child_text(el, "value"),
            }
            for el in _children(root, "userAccessPolicyFilters")
        ]
        self.actions = [
            {
                "action": _child_text(el, "action"),
                "type": _child_text(el, "type"),
                "target": _child_text(el, "target"),
            }
            for el in _children(root, "userAccessPolicyActions")
        ]

    @property
    def is_active(self) -> bool:
        return self.status == "Active"

    @property
    def order(self) -> int | None:
        if self.order_raw is None or self.order_raw == "":
            return None
        try:
            return int(self.order_raw)
        except ValueError:
            return None

    def filter_signatures(self) -> set[tuple[str, ...]]:
        """Identity of each filter row, ignoring its sortOrder."""
        return {
            (
                row["type"] or "",
                row["operation"] or "",
                row["target"] or "",
                row["columnName"] or "",
                row["value"] or "",
            )
            for row in self.filters
        }

    def action_signatures(self) -> set[tuple[str, ...]]:
        return {
            (a["action"] or "", a["type"] or "", a["target"] or "")
            for a in self.actions
        }


# --- Individual checks -----------------------------------------------------


def check_boolean_filter(policy: Policy) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    declared: set[int] = set()
    seen_sort_orders: set[str] = set()

    for index, row in enumerate(policy.filters, start=1):
        raw = row["sortOrder"]
        if raw is None or raw == "":
            issues.append(
                ("ERROR", f"{policy.name}: filter row {index} has no sortOrder (required).")
            )
            continue
        if raw in seen_sort_orders:
            issues.append(
                ("ERROR", f"{policy.name}: sortOrder '{raw}' is used by more than one filter row.")
            )
        seen_sort_orders.add(raw)
        try:
            declared.add(int(raw))
        except ValueError:
            issues.append(
                ("ERROR", f"{policy.name}: sortOrder '{raw}' is not an integer.")
            )

    expression = policy.boolean_filter
    if expression is None:
        issues.append(
            (
                "ERROR",
                f"{policy.name}: booleanFilter is missing. It is required, even for a "
                "single filter row (where its value is '1').",
            )
        )
        return issues
    if expression == "":
        issues.append(("ERROR", f"{policy.name}: booleanFilter is empty."))
        return issues

    tokens = BOOLEAN_TOKEN_RE.findall(expression)
    if "".join(tokens).replace(" ", "") != re.sub(r"\s+", "", expression):
        issues.append(
            (
                "ERROR",
                f"{policy.name}: booleanFilter '{expression}' contains tokens that are "
                "neither an index, AND, OR, NOT, nor a parenthesis.",
            )
        )
    if expression.count("(") != expression.count(")"):
        issues.append(
            ("ERROR", f"{policy.name}: booleanFilter '{expression}' has unbalanced parentheses.")
        )

    referenced = {int(token) for token in tokens if token.isdigit()}
    dangling = sorted(referenced - declared)
    if dangling:
        issues.append(
            (
                "ERROR",
                f"{policy.name}: booleanFilter references index(es) "
                f"{', '.join(str(d) for d in dangling)} with no matching filter sortOrder.",
            )
        )
    unreferenced = sorted(declared - referenced)
    if unreferenced:
        issues.append(
            (
                "WARN",
                f"{policy.name}: filter sortOrder(s) "
                f"{', '.join(str(u) for u in unreferenced)} are never used by booleanFilter "
                f"'{expression}', so those rows do not affect who the policy matches.",
            )
        )
    if not referenced and policy.filters:
        issues.append(
            ("ERROR", f"{policy.name}: booleanFilter '{expression}' references no filter row.")
        )
    return issues


def check_enums_and_shape(policy: Policy) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []

    if policy.status is None:
        issues.append(("ERROR", f"{policy.name}: status is missing (required)."))
    elif policy.status not in STATUS_VALUES:
        issues.append(
            (
                "ERROR",
                f"{policy.name}: status '{policy.status}' is not a UserAccessPolicyStatus "
                f"value ({', '.join(sorted(STATUS_VALUES))}).",
            )
        )
    elif policy.is_active:
        issues.append(
            (
                "WARN",
                f"{policy.name}: deployed with status Active. The platform changes a "
                "deployed Active policy to Design; activation is a manual Setup step. "
                "Deploy Design and put activation on the release runbook.",
            )
        )

    if policy.trigger_type is not None and policy.trigger_type not in TRIGGER_TYPE_VALUES:
        issues.append(
            (
                "ERROR",
                f"{policy.name}: triggerType '{policy.trigger_type}' is not a "
                f"UserAccessPolicyTriggerType value ({', '.join(sorted(TRIGGER_TYPE_VALUES))}).",
            )
        )

    if policy.label is None or policy.label == "":
        issues.append(("ERROR", f"{policy.name}: masterLabel is missing (required)."))

    if not policy.actions:
        issues.append(
            ("WARN", f"{policy.name}: no userAccessPolicyActions -- the policy grants and revokes nothing.")
        )
    if not policy.filters:
        issues.append(
            ("WARN", f"{policy.name}: no userAccessPolicyFilters -- the policy defines no population.")
        )

    for index, row in enumerate(policy.filters, start=1):
        row_type = row["type"]
        if row_type is None:
            issues.append(("ERROR", f"{policy.name}: filter row {index} has no type (required)."))
        elif row_type not in FILTER_TARGET_TYPES:
            issues.append(
                (
                    "ERROR",
                    f"{policy.name}: filter row {index} type '{row_type}' is not a "
                    f"UserAccessPolicyFilterTargetType value.",
                )
            )
        operation = row["operation"]
        if operation is None:
            issues.append(("ERROR", f"{policy.name}: filter row {index} has no operation (required)."))
        elif operation not in FILTER_OPERATIONS:
            issues.append(
                (
                    "ERROR",
                    f"{policy.name}: filter row {index} operation '{operation}' is not a "
                    f"UserAccessPolicyFilterOperation value ({', '.join(sorted(FILTER_OPERATIONS))}).",
                )
            )
        if row["target"] is None or row["target"] == "":
            issues.append(("ERROR", f"{policy.name}: filter row {index} has no target (required)."))
        if row_type == "User":
            if row["target"] not in (None, "User"):
                issues.append(
                    (
                        "ERROR",
                        f"{policy.name}: filter row {index} has type User, so target must be "
                        f"the literal string 'User', not '{row['target']}'.",
                    )
                )
            if not row["columnName"]:
                issues.append(
                    (
                        "ERROR",
                        f"{policy.name}: filter row {index} has type User but no columnName -- "
                        "the user field being filtered is undefined.",
                    )
                )
            if row["value"] is None:
                issues.append(
                    (
                        "ERROR",
                        f"{policy.name}: filter row {index} has type User but no value to compare.",
                    )
                )
        elif row_type is not None:
            for unused in ("columnName", "value"):
                if row[unused]:
                    issues.append(
                        (
                            "WARN",
                            f"{policy.name}: filter row {index} sets {unused} but its type is "
                            f"'{row_type}'; {unused} is used only when type is User and is ignored here.",
                        )
                    )

    for index, action in enumerate(policy.actions, start=1):
        if action["action"] not in ACTION_VALUES:
            issues.append(
                (
                    "ERROR",
                    f"{policy.name}: action {index} has action '{action['action']}'; "
                    f"expected Grant or Revoke.",
                )
            )
        if action["type"] not in ACTION_TARGET_TYPES:
            issues.append(
                (
                    "ERROR",
                    f"{policy.name}: action {index} type '{action['type']}' is not a "
                    f"UserAccessPolicyActionTargetType value "
                    f"({', '.join(sorted(ACTION_TARGET_TYPES))}).",
                )
            )
        if not action["target"]:
            issues.append(("ERROR", f"{policy.name}: action {index} has no target (required)."))

    return issues


def check_order_field(policies: list[Policy]) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    by_order: dict[int, list[str]] = {}

    for policy in policies:
        raw = policy.order_raw
        if raw is not None and raw != "" and policy.order is None:
            issues.append(("ERROR", f"{policy.name}: order '{raw}' is not an integer."))
            continue
        if policy.order is not None and not (ORDER_MIN <= policy.order <= ORDER_MAX):
            issues.append(
                (
                    "ERROR",
                    f"{policy.name}: order {policy.order} is outside the documented range "
                    f"{ORDER_MIN}-{ORDER_MAX}.",
                )
            )
        if policy.is_active and policy.order is None:
            issues.append(
                (
                    "ERROR",
                    f"{policy.name}: status is Active but order is missing. order is required "
                    "when status is Active, and is the only tiebreak between matching policies.",
                )
            )
        if policy.is_active and policy.order is not None:
            by_order.setdefault(policy.order, []).append(policy.name)

    for order_value, names in sorted(by_order.items()):
        if len(names) > 1:
            issues.append(
                (
                    "ERROR",
                    f"Active policies share order {order_value}: {', '.join(sorted(names))}. "
                    "Only the lowest-order active policy applies, and no tiebreak between "
                    "equal orders is documented.",
                )
            )
    return issues


def check_action_targets(
    policies: list[Policy], component_index: dict[str, set[str]]
) -> list[tuple[str, str]]:
    """Warn when an action or filter target is absent from the local manifest.

    Only checked for a type whose folder has at least one component locally --
    otherwise the manifest simply does not carry that type and absence proves
    nothing. PermissionSetLicense and PackageLicense are never deployable, so
    they are reported as unverifiable rather than missing.
    """
    issues: list[tuple[str, str]] = []
    unverifiable: set[str] = set()

    for policy in policies:
        rows = [("action", a["type"], a["target"]) for a in policy.actions]
        rows += [
            ("filter", f["type"], f["target"])
            for f in policy.filters
            if f["type"] != "User"
        ]
        for kind, type_name, target in rows:
            if not type_name or not target:
                continue
            if type_name in ("PermissionSetLicense", "PackageLicense"):
                unverifiable.add(f"{policy.name}: {type_name} '{target}'")
                continue
            if type_name not in DEPLOYABLE_TARGETS:
                continue
            present = component_index.get(type_name, set())
            if not present:
                continue
            for name in [n.strip() for n in target.split(",") if n.strip()]:
                if name not in present:
                    issues.append(
                        (
                            "WARN",
                            f"{policy.name}: {kind} target '{name}' of type {type_name} is not "
                            f"in the manifest, though other {type_name} components are. "
                            "Deployment fails if it does not already exist in the target org.",
                        )
                    )

    for entry in sorted(unverifiable):
        issues.append(
            (
                "INFO",
                f"{entry} cannot be verified from a manifest -- licences are org-provisioned, "
                "not deployable metadata. Confirm it exists in the target org by hand.",
            )
        )
    return issues


def check_overlapping_policies(policies: list[Policy]) -> list[tuple[str, str]]:
    """Warn where two active policies can match the same user but differ."""
    issues: list[tuple[str, str]] = []
    active = [p for p in policies if p.is_active]

    for i, left in enumerate(active):
        for right in active[i + 1 :]:
            shared = left.filter_signatures() & right.filter_signatures()
            if not shared:
                continue
            if left.order is None or right.order is None or left.order == right.order:
                continue
            left_actions = left.action_signatures()
            right_actions = right.action_signatures()
            if left_actions == right_actions:
                continue
            winner, loser = (
                (left, right) if left.order < right.order else (right, left)
            )
            lost = loser.action_signatures() - winner.action_signatures()
            if not lost:
                continue
            lost_desc = ", ".join(
                f"{a[0]} {a[1]} {a[2]}" for a in sorted(lost)
            )
            issues.append(
                (
                    "WARN",
                    f"{winner.name} (order {winner.order}) and {loser.name} "
                    f"(order {loser.order}) share {len(shared)} filter row(s), so a user can "
                    f"match both. Only the lower order applies, so these action(s) from "
                    f"{loser.name} never run for that user: {lost_desc}. Repeat them in "
                    f"{winner.name} or merge the policies.",
                )
            )
    return issues


# --- Orchestrator ----------------------------------------------------------


def run_checks(manifest_dir: Path) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []

    if not manifest_dir.exists():
        return [("ERROR", f"Manifest directory not found: {manifest_dir}")]

    policy_files = find_policy_files(manifest_dir)
    if not policy_files:
        return [
            (
                "INFO",
                f"No UserAccessPolicy files (*.useraccesspolicy) found under {manifest_dir}. "
                "If policies are expected, retrieve them into the project first.",
            )
        ]

    policies: list[Policy] = []
    for path in policy_files:
        root = _parse_xml_root(path)
        if root is None:
            issues.append(("ERROR", f"{path.name}: not well-formed XML; skipped."))
            continue
        if _local(root.tag) != "UserAccessPolicy":
            issues.append(
                (
                    "ERROR",
                    f"{path.name}: root element is <{_local(root.tag)}>, expected "
                    "<UserAccessPolicy>.",
                )
            )
            continue
        policies.append(Policy(path, root))

    component_index = index_manifest_components(manifest_dir)

    for policy in policies:
        issues.extend(check_boolean_filter(policy))
        issues.extend(check_enums_and_shape(policy))

    issues.extend(check_order_field(policies))
    issues.extend(check_action_targets(policies, component_index))
    issues.extend(check_overlapping_policies(policies))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check UserAccessPolicy metadata for configuration problems: booleanFilter "
            "index integrity, enum validity, order range/uniqueness, unresolved action "
            "targets, and policies that suppress each other via order."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON instead of text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues = run_checks(Path(args.manifest_dir))

    if args.json:
        print(
            json.dumps(
                [{"severity": severity, "message": message} for severity, message in issues],
                indent=2,
            )
        )
    elif not issues:
        print("No User Access Policy issues found.")
    else:
        for severity, message in issues:
            print(f"{severity}: {message}")

    return 1 if any(severity in ("ERROR", "WARN") for severity, _ in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
