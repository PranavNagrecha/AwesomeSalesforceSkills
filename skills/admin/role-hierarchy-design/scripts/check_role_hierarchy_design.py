#!/usr/bin/env python3
"""Static checks on a directory of Salesforce Role metadata files.

Parses ``*.role-meta.xml`` (or ``*.role``) files and reports the defects that
make a role deployment fail, or that make a hierarchy expensive to maintain:

  ERROR  parentRole names a role that is not in the directory and was not
         declared present in the target org (deployment fails on the
         unresolved reference)
  ERROR  a parent chain that loops back on itself
  ERROR  caseAccessLevel / contactAccessLevel / opportunityAccessLevel set to
         something other than Read, Edit or None
         (RoleOrTerritory metadata type: "Valid values are Read, Edit, None")
  ERROR  a role file with no <name>
         (RoleOrTerritory metadata type: name is Required)
  ERROR  role count above the org ceiling
         (Spring '21 Release Notes, "Create More Roles": 5,000 for orgs
         created in Spring '21 or later, 500 for older orgs)
  WARN   an access level left unset, which hands the value to a platform
         default rather than a deliberate choice (RoleOrTerritory: "If no
         value is set for this field, this field value uses the default
         access level that is specified in the Manage Territory page in
         Setup")
  WARN   depth beyond --max-depth, when that flag is supplied

Depth is reported, never failed by default. Salesforce documents a ceiling on
the NUMBER of roles, not on the number of levels; --max-depth exists so a team
can enforce its own convention, not because a platform limit is being checked.

Stdlib only. Exit 0 when no ERROR was found, 1 otherwise.

Usage:
    python3 check_role_hierarchy_design.py --roles-dir force-app/main/default/roles
    python3 check_role_hierarchy_design.py --roles-dir <dir> --role-limit 5000
    python3 check_role_hierarchy_design.py --roles-dir <dir> --max-depth 8
    python3 check_role_hierarchy_design.py --roles-dir <dir> --known-role Executive
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

ACCESS_FIELDS = ("caseAccessLevel", "contactAccessLevel", "opportunityAccessLevel")
VALID_ACCESS = ("Read", "Edit", "None")

# Spring '21 Release Notes, "Create More Roles". 500 is the default for orgs
# created before Spring '21, so it is the safe default for a check.
DEFAULT_ROLE_LIMIT = 500


class Role:
    """One parsed .role-meta.xml file."""

    def __init__(self, api_name: str, path: Path) -> None:
        self.api_name = api_name
        self.path = path
        self.label: str | None = None
        self.parent: str | None = None
        self.access: dict[str, str | None] = {f: None for f in ACCESS_FIELDS}


def _text(elem: ET.Element, tag: str) -> str | None:
    node = elem.find(f"{MD_NS}{tag}")
    if node is None:
        node = elem.find(tag)  # tolerate namespace-stripped fixtures
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value or None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce Role metadata for deploy-breaking and "
        "maintenance-cost defects.",
    )
    parser.add_argument(
        "--roles-dir",
        default="force-app/main/default/roles",
        help="Directory holding .role-meta.xml files "
        "(default: force-app/main/default/roles).",
    )
    parser.add_argument(
        "--role-limit",
        type=int,
        default=DEFAULT_ROLE_LIMIT,
        help=f"Org role ceiling to check the file count against "
        f"(default: {DEFAULT_ROLE_LIMIT}; pass 5000 for orgs created in "
        f"Spring '21 or later).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Warn when a role sits deeper than this many levels. Local "
        "convention only — Salesforce documents no maximum level count.",
    )
    parser.add_argument(
        "--known-role",
        action="append",
        default=[],
        metavar="API_NAME",
        help="A role fullName that already exists in the target org, so a "
        "parentRole pointing at it is not an unresolved reference. Repeatable.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARN findings as failures too.",
    )
    return parser.parse_args()


def load_roles(roles_dir: Path) -> tuple[dict[str, Role], list[str]]:
    """Parse every role file under roles_dir. Returns (roles, errors)."""
    errors: list[str] = []
    roles: dict[str, Role] = {}

    paths = sorted(
        p
        for p in roles_dir.iterdir()
        if p.is_file() and (p.name.endswith(".role-meta.xml") or p.suffix == ".role")
    )

    for path in paths:
        api_name = path.name.split(".")[0]
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            errors.append(f"{path}: not parseable as XML ({exc})")
            continue

        role = Role(api_name, path)
        role.label = _text(root, "name")
        role.parent = _text(root, "parentRole")
        for field in ACCESS_FIELDS:
            role.access[field] = _text(root, field)

        if role.label is None:
            errors.append(
                f"{path}: missing required <name> element "
                f"(RoleOrTerritory metadata: name is Required)"
            )

        for field, value in role.access.items():
            if value is not None and value not in VALID_ACCESS:
                errors.append(
                    f"{path}: <{field}> is '{value}'; valid values are "
                    f"{', '.join(VALID_ACCESS)}"
                )

        if api_name in roles:
            errors.append(f"{path}: duplicate role fullName '{api_name}'")
        roles[api_name] = role

    return roles, errors


def check_parents(roles: dict[str, Role], known: set[str]) -> list[str]:
    """Unresolved parentRole references."""
    errors: list[str] = []
    for role in roles.values():
        if role.parent and role.parent not in roles and role.parent not in known:
            errors.append(
                f"{role.path}: <parentRole>{role.parent}</parentRole> is not in "
                f"the roles directory and was not passed via --known-role; the "
                f"deployment will fail on the unresolved reference"
            )
    return errors


def check_cycles(roles: dict[str, Role]) -> list[str]:
    """A role that is its own ancestor."""
    errors: list[str] = []
    reported: set[str] = set()
    for start in sorted(roles):
        seen: list[str] = []
        node: str | None = start
        while node is not None and node in roles:
            if node in seen:
                cycle = seen[seen.index(node):] + [node]
                key = ">".join(sorted(set(cycle)))
                if key not in reported:
                    reported.add(key)
                    errors.append(
                        "parentRole cycle: " + " -> ".join(cycle)
                    )
                break
            seen.append(node)
            node = roles[node].parent
    return errors


def compute_depths(roles: dict[str, Role]) -> dict[str, int]:
    """Depth of each role; 1 for a root. Roles inside a cycle are skipped."""
    depths: dict[str, int] = {}

    def depth_of(name: str, guard: set[str]) -> int | None:
        if name in depths:
            return depths[name]
        if name in guard or name not in roles:
            return None
        parent = roles[name].parent
        if parent is None or parent not in roles:
            depths[name] = 1
            return 1
        parent_depth = depth_of(parent, guard | {name})
        if parent_depth is None:
            return None
        depths[name] = parent_depth + 1
        return depths[name]

    for name in roles:
        depth_of(name, set())
    return depths


def main() -> int:
    args = parse_args()
    roles_dir = Path(args.roles_dir)

    if not roles_dir.is_dir():
        print(f"ERROR: roles directory not found: {roles_dir}", file=sys.stderr)
        return 1

    roles, errors = load_roles(roles_dir)

    if not roles:
        print(
            f"ERROR: no .role-meta.xml files found in {roles_dir}. Point "
            f"--roles-dir at the directory holding the Role metadata.",
            file=sys.stderr,
        )
        return 1

    errors += check_parents(roles, set(args.known_role))
    errors += check_cycles(roles)

    if len(roles) > args.role_limit:
        errors.append(
            f"{len(roles)} roles in {roles_dir} exceeds the --role-limit of "
            f"{args.role_limit}. Orgs created in Spring '21 or later allow up "
            f"to 5,000 roles; older orgs default to 500 and need Salesforce "
            f"Customer Support to raise it."
        )

    warnings: list[str] = []
    for name in sorted(roles):
        role = roles[name]
        unset = [f for f, v in role.access.items() if v is None]
        if unset:
            warnings.append(
                f"{role.path}: {', '.join(unset)} unset — the value falls back "
                f"to a platform default (RoleOrTerritory: the default access "
                f"level specified on the Manage Territory page in Setup), which "
                f"no source diff shows. Set it explicitly, or omit it "
                f"deliberately because that object's sharing model is Public "
                f"Read/Write."
            )

    depths = compute_depths(roles)
    if depths:
        deepest = max(depths.values())
        roots = sorted(n for n, d in depths.items() if d == 1)
        print(f"Parsed {len(roles)} role(s) from {roles_dir}")
        print(f"  root roles: {len(roots)} ({', '.join(roots[:5])}"
              f"{', …' if len(roots) > 5 else ''})")
        print(f"  deepest chain: {deepest} level(s)")
        histogram = {}
        for depth in depths.values():
            histogram[depth] = histogram.get(depth, 0) + 1
        for depth in sorted(histogram):
            print(f"    level {depth}: {histogram[depth]} role(s)")
        if args.max_depth is not None:
            for name in sorted(depths):
                if depths[name] > args.max_depth:
                    warnings.append(
                        f"{roles[name].path}: depth {depths[name]} exceeds "
                        f"--max-depth {args.max_depth}. Salesforce documents no "
                        f"maximum level count; this is your own convention. "
                        f"Each level adds indirect membership rows and widens "
                        f"the cost of every future reparent."
                    )

    for warning in warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(
            f"\n{len(errors)} error(s), {len(warnings)} warning(s). "
            f"Fix the errors before deploying.",
            file=sys.stderr,
        )
        return 1

    if warnings and args.strict:
        print(
            f"\n{len(warnings)} warning(s) and --strict was set.",
            file=sys.stderr,
        )
        return 1

    print(f"\nNo errors. {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
