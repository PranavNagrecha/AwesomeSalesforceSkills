#!/usr/bin/env python3
"""Lint a partner-portal design artefact (and any retrieved partner metadata beside it).

Two modes, both stdlib-only:

1. **Design YAML** (``--file`` or any ``*.yaml`` / ``*.yml`` under ``--manifest-dir``).
   The artefact authored by ``references/worked-examples.md``. Checks:
     - every partner tier carries a licence from the documented set and a role depth
       that fits the fixed ``UserRole.PortalRole`` picklist;
     - every exposed object carries a sharing mechanism from the documented set, and
       no object is handed to a mechanism that cannot carry it (sharing sets cannot
       target Lead);
     - the deal-registration flow has an acceptance step and a duplicate check;
     - offboarding covers both user deactivation and record reassignment;
     - ids are unique and every row has an owner.

2. **Retrieved metadata** (``--manifest-dir``). Parses ``networks/*.network-meta.xml``
   and ``sharingSets/*.sharingSet-meta.xml`` and checks them against the Metadata API
   Developer Guide field tables (``Network`` and ``SharingSet``).

Grounding for every enum in this file is cited beside the constant.

Usage::

    python3 check_partner_community_requirements.py --file design.yaml
    python3 check_partner_community_requirements.py --manifest-dir force-app/main/default
    python3 check_partner_community_requirements.py --manifest-dir . --file design.yaml

Exit status: 0 when no errors, 1 when any error is reported.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Documented vocabularies
# ---------------------------------------------------------------------------

# object_reference.txt L299583-L299585 (UserLicense.LicenseDefinitionKey:
# PID_Partner_Community, PID_Partner_Community_Login) plus "Partner Community Plus"
# as named in the Apex Reference Guide L4398-L4399.
ALLOWED_LICENCES = {
    "Partner Community",
    "Partner Community Login",
    "Partner Community Plus",
}

# object_reference.txt L303483-L303489 - UserRole.PortalRole is a restricted picklist
# with exactly Executive, Manager, User, PersonAccount. A partner account therefore
# has at most three stacked roles (PersonAccount is not a hierarchy level).
PORTAL_ROLE_LADDER = ("User", "Manager", "Executive")
MAX_ROLE_DEPTH = len(PORTAL_ROLE_LADDER)

# Mechanisms this skill will name in a design. Each maps to a documented type.
SHARING_MECHANISMS = {
    # api_meta.txt L130365-L130520 (SharingSet / AccessMapping)
    "sharing-set",
    # object_reference.txt L303469-L303489 (UserRole.PortalAccountId / PortalRole)
    "partner-account-role-hierarchy",
    # object_reference.txt L17416-L17570 (AccountRelationshipShareRule)
    "account-relationship-share-rule",
    # api_meta.txt L129082-L129090 (SharedTo.portalRole / portalRoleandSubordinates)
    "sharing-rule-portal-role",
    # api_meta.txt L74776-L74782 (FolderShare sharedToType AllPrmUsers / PortalRole)
    "folder-share",
    # Ownership by the partner user; no sharing metadata at all.
    "record-ownership",
    # Apex managed sharing - the escape hatch, and the one that needs a code owner.
    "apex-managed-sharing",
    # Explicitly modelled as "external OWD keeps this closed".
    "not-exposed",
}

# api_meta.txt L130443-L130452 - SharingSet AccessMapping.object valid values.
# Lead is deliberately absent from the guide's list.
SHARING_SET_OBJECTS = {
    "Account",
    "Campaign",
    "Contact",
    "Case",
    "Opportunity",
    "Order",
    "ServiceContract",
    "User",
    "WorkOrder",
}

# api_meta.txt L130455-L130466 - SharingSet AccessMapping.userField valid values.
SHARING_SET_USER_FIELDS = {
    "Account",
    "Contact",
    "Contact.RelatedAccount",
    "Manager.Account",
    "Manager.Contact",
}

# api_meta.txt L130436-L130440 - AccessMapping.accessLevel valid values.
SHARING_SET_ACCESS_LEVELS = {"Read", "Edit"}

# api_meta.txt L90782-L91045 - Network fields marked "Required." in the field table.
NETWORK_REQUIRED_FIELDS = (
    "emailSenderAddress",
    "emailSenderName",
    "forgotPasswordTemplate",
    "site",
    "status",
    "tabs",
)

# api_meta.txt L91020-L91035 - Network.status NetworkStatus valid values.
NETWORK_STATUS_VALUES = {"Live", "DownForMaintenance", "UnderConstruction"}

DEAL_REG_REQUIRED_STEP_TYPES = {"acceptance", "duplicate_check"}
OFFBOARDING_REQUIRED_ACTIONS = {"deactivate_user", "reassign_records"}

ALLOWED_STEP_TYPES = {
    "submission",
    "duplicate_check",
    "approval",
    "acceptance",
    "conversion",
    "rejection",
    "expiry",
}

ALLOWED_OFFBOARDING_ACTIONS = {
    "reassign_records",
    "deactivate_user",
    "remove_group_membership",
    "revoke_permission_set",
    "archive_content",
    "clear_partner_flag",
}


# ---------------------------------------------------------------------------
# Minimal YAML subset reader (nested maps + lists of maps, scalar leaves)
# ---------------------------------------------------------------------------


def _strip_scalar(raw: str) -> str:
    """Strip quotes and a trailing inline comment from a scalar value."""
    value = raw.strip()
    if value.startswith(("'", '"')):
        quote = value[0]
        end = value.find(quote, 1)
        if end != -1:
            return value[1:end]
        return value[1:]
    hash_at = value.find(" #")
    if hash_at != -1:
        value = value[:hash_at]
    return value.strip()


ITEM = "\x00ITEM"
SCALARS = "\x00SCALARS"


def _tokenize(text: str) -> tuple[list[tuple[int, str]], list[str]]:
    """Flatten the document into (indent, text) tokens.

    A list item ``- rest`` becomes an ITEM marker at the dash's indent followed by
    ``rest`` at ``indent + 2``, so every key of a list item aligns the same way.
    Block scalars (``>`` / ``|``) are folded into their key's token.
    """
    issues: list[str] = []
    tokens: list[tuple[int, str]] = []
    lines = text.splitlines()
    index = 0

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        index += 1

        if not stripped or stripped.startswith("#") or stripped.startswith("---"):
            continue

        indent = len(raw) - len(raw.lstrip())

        if stripped.startswith("- ") or stripped == "-":
            tokens.append((indent, ITEM))
            rest = stripped[1:].strip()
            if not rest:
                continue
            indent += 2
            stripped = rest

        if stripped.startswith("[") or stripped.startswith("{"):
            issues.append(
                f"line {index}: flow collections are outside the supported subset. "
                f"Write one scalar per line."
            )
            continue

        key, sep, value = stripped.partition(":")
        if sep and value.strip() in (">", "|", ">-", "|-", ">+", "|+"):
            folded: list[str] = []
            while index < len(lines):
                nxt = lines[index]
                if not nxt.strip():
                    index += 1
                    continue
                nxt_indent = len(nxt) - len(nxt.lstrip())
                if nxt_indent <= indent:
                    break
                folded.append(nxt.strip())
                index += 1
            tokens.append((indent, f"{key.strip()}: {' '.join(folded)}"))
            continue

        tokens.append((indent, stripped))

    return tokens, issues


def _parse_block(tokens: list[tuple[int, str]], pos: int, indent: int):
    """Parse every token at *indent* into a list (ITEM markers) or a mapping."""
    if pos < len(tokens) and tokens[pos][0] == indent and tokens[pos][1] == ITEM:
        items: list = []
        while pos < len(tokens) and tokens[pos][0] == indent and tokens[pos][1] == ITEM:
            pos += 1
            if pos < len(tokens) and tokens[pos][0] > indent:
                value, pos = _parse_block(tokens, pos, tokens[pos][0])
                items.append(_unwrap(value))
            else:
                items.append({})
        return items, pos

    mapping: dict = {}
    while pos < len(tokens) and tokens[pos][0] == indent and tokens[pos][1] != ITEM:
        text = tokens[pos][1]
        pos += 1

        if ":" not in text:
            mapping.setdefault(SCALARS, []).append(_strip_scalar(text))
            continue

        key, _, raw_value = text.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()

        if raw_value:
            mapping[key] = _strip_scalar(raw_value)
            continue

        if pos < len(tokens) and tokens[pos][0] > indent:
            value, pos = _parse_block(tokens, pos, tokens[pos][0])
            mapping[key] = _unwrap(value)
        elif pos < len(tokens) and tokens[pos][0] == indent and tokens[pos][1] == ITEM:
            value, pos = _parse_block(tokens, pos, indent)
            mapping[key] = _unwrap(value)
        else:
            mapping[key] = ""

    return mapping, pos


def _unwrap(value):  # noqa: ANN001
    """A block that held only bare scalars becomes a list (or a lone scalar)."""
    if isinstance(value, dict) and set(value) == {SCALARS}:
        scalars = value[SCALARS]
        return scalars[0] if len(scalars) == 1 else scalars
    return value


def parse_yaml_subset(text: str) -> tuple[dict, list[str]]:
    """Parse the indentation-based YAML subset used by this skill's design artefact.

    Supported: nested mappings, lists of mappings, lists of scalars, and block
    scalars. Flow collections are rejected so a design file never silently lints
    as empty.
    """
    tokens, issues = _tokenize(text)
    if not tokens:
        return {}, issues
    root, _ = _parse_block(tokens, 0, tokens[0][0])
    if not isinstance(root, dict):
        return {}, issues + ["document root is a list; expected a mapping"]
    root.pop(SCALARS, None)
    return root, issues


# ---------------------------------------------------------------------------
# XML helpers -- a leaf Element is falsy, so never rely on truthiness
# ---------------------------------------------------------------------------


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(element, tag: str) -> list:  # noqa: ANN001
    return [child for child in list(element) if _local(child.tag) == tag]


def _first(element, tag: str):  # noqa: ANN001
    """Return the first direct child named *tag*, or None. Never truthiness-test."""
    for child in list(element):
        if _local(child.tag) == tag:
            return child
    return None


def _text(element, tag: str) -> str | None:
    child = _first(element, tag)
    if child is None:
        return None
    return (child.text or "").strip()


def _has(element, tag: str) -> bool:
    return _first(element, tag) is not None


# ---------------------------------------------------------------------------
# Design-artefact checks
# ---------------------------------------------------------------------------


def _as_rows(value) -> list[dict]:  # noqa: ANN001
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    return []


def check_tiers(design: dict) -> list[str]:
    errors: list[str] = []
    tiers = _as_rows(design.get("tiers"))
    if not tiers:
        return ["tiers: no partner tiers found. A partner-portal design needs at least one tier."]

    seen: set[str] = set()
    for index, tier in enumerate(tiers, start=1):
        tier_id = (tier.get("id") or "").strip()
        label = tier_id or f"tiers[{index}]"
        if not tier_id:
            errors.append(f"{label}: missing 'id'.")
        elif tier_id in seen:
            errors.append(f"{label}: duplicate tier id.")
        else:
            seen.add(tier_id)

        licence = (tier.get("licence") or tier.get("license") or "").strip()
        if not licence:
            errors.append(
                f"{label}: missing 'licence'. Every tier must name the partner licence it "
                f"consumes. Allowed: {', '.join(sorted(ALLOWED_LICENCES))}."
            )
        elif licence not in ALLOWED_LICENCES:
            errors.append(
                f"{label}: licence '{licence}' is not a documented partner licence. "
                f"Allowed: {', '.join(sorted(ALLOWED_LICENCES))}."
            )

        depth_raw = str(tier.get("role_depth", "")).strip()
        if not depth_raw:
            errors.append(
                f"{label}: missing 'role_depth'. State how many of "
                f"{'/'.join(PORTAL_ROLE_LADDER)} this tier's partner accounts get."
            )
        else:
            try:
                depth = int(depth_raw)
            except ValueError:
                errors.append(f"{label}: role_depth '{depth_raw}' is not an integer.")
            else:
                if depth < 1 or depth > MAX_ROLE_DEPTH:
                    errors.append(
                        f"{label}: role_depth {depth} is outside 1-{MAX_ROLE_DEPTH}. "
                        f"UserRole.PortalRole is a restricted picklist "
                        f"({'/'.join(PORTAL_ROLE_LADDER)}), so a partner account "
                        f"cannot stack more than {MAX_ROLE_DEPTH} roles."
                    )

        if not (tier.get("owner") or "").strip():
            errors.append(f"{label}: missing 'owner'.")
    return errors


def check_exposed_objects(design: dict) -> list[str]:
    errors: list[str] = []
    rows = _as_rows(design.get("exposed_objects"))
    if not rows:
        return [
            "exposed_objects: no rows found. Every object a partner user can reach needs "
            "an explicit sharing mechanism, including the ones set to 'not-exposed'."
        ]

    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        obj = (row.get("object") or "").strip()
        label = obj or f"exposed_objects[{index}]"
        if not obj:
            errors.append(f"{label}: missing 'object'.")
        elif obj in seen:
            errors.append(f"{label}: duplicate object row.")
        else:
            seen.add(obj)

        mechanism = (row.get("sharing_mechanism") or "").strip()
        if not mechanism:
            errors.append(
                f"{label}: missing 'sharing_mechanism'. Allowed: "
                f"{', '.join(sorted(SHARING_MECHANISMS))}."
            )
        elif mechanism not in SHARING_MECHANISMS:
            errors.append(
                f"{label}: sharing_mechanism '{mechanism}' is not in the documented set. "
                f"Allowed: {', '.join(sorted(SHARING_MECHANISMS))}."
            )
        elif mechanism == "sharing-set" and obj and obj not in SHARING_SET_OBJECTS:
            errors.append(
                f"{label}: sharing-set cannot target '{obj}'. The Metadata API Guide's "
                f"SharingSet AccessMapping.object list is "
                f"{', '.join(sorted(SHARING_SET_OBJECTS))} plus custom objects "
                f"(api_meta.txt L130443-L130452). Lead in particular is not on it."
            )

        if not (row.get("owner") or "").strip():
            errors.append(f"{label}: missing 'owner'.")
    return errors


def check_deal_registration(design: dict) -> list[str]:
    errors: list[str] = []
    block = design.get("deal_registration")
    if not isinstance(block, dict):
        return ["deal_registration: block missing."]

    steps = _as_rows(block.get("steps"))
    if not steps:
        return ["deal_registration.steps: no steps found."]

    seen: set[str] = set()
    present_types: set[str] = set()
    for index, step in enumerate(steps, start=1):
        step_id = (step.get("id") or "").strip()
        label = step_id or f"deal_registration.steps[{index}]"
        if not step_id:
            errors.append(f"{label}: missing 'id'.")
        elif step_id in seen:
            errors.append(f"{label}: duplicate step id.")
        else:
            seen.add(step_id)

        step_type = (step.get("type") or "").strip()
        if not step_type:
            errors.append(
                f"{label}: missing 'type'. Allowed: {', '.join(sorted(ALLOWED_STEP_TYPES))}."
            )
        elif step_type not in ALLOWED_STEP_TYPES:
            errors.append(
                f"{label}: type '{step_type}' is not allowed. "
                f"Allowed: {', '.join(sorted(ALLOWED_STEP_TYPES))}."
            )
        else:
            present_types.add(step_type)

        if not (step.get("owner") or "").strip():
            errors.append(f"{label}: missing 'owner'.")

    for required in sorted(DEAL_REG_REQUIRED_STEP_TYPES - present_types):
        if required == "acceptance":
            errors.append(
                "deal_registration.steps: no step with type 'acceptance'. A registration "
                "that is approved but never accepted by a named partner leaves no record "
                "of who owns the deal."
            )
        else:
            errors.append(
                "deal_registration.steps: no step with type 'duplicate_check'. Without one, "
                "two partners can register the same prospect and the conflict surfaces after "
                "conversion."
            )
    return errors


def check_offboarding(design: dict) -> list[str]:
    errors: list[str] = []
    block = design.get("offboarding")
    if not isinstance(block, dict):
        return ["offboarding: block missing."]

    steps = _as_rows(block.get("steps"))
    if not steps:
        return ["offboarding.steps: no steps found."]

    seen: set[str] = set()
    present: set[str] = set()
    for index, step in enumerate(steps, start=1):
        step_id = (step.get("id") or "").strip()
        label = step_id or f"offboarding.steps[{index}]"
        if not step_id:
            errors.append(f"{label}: missing 'id'.")
        elif step_id in seen:
            errors.append(f"{label}: duplicate step id.")
        else:
            seen.add(step_id)

        action = (step.get("action") or "").strip()
        if not action:
            errors.append(
                f"{label}: missing 'action'. Allowed: "
                f"{', '.join(sorted(ALLOWED_OFFBOARDING_ACTIONS))}."
            )
        elif action not in ALLOWED_OFFBOARDING_ACTIONS:
            errors.append(
                f"{label}: action '{action}' is not allowed. Allowed: "
                f"{', '.join(sorted(ALLOWED_OFFBOARDING_ACTIONS))}."
            )
        else:
            present.add(action)

        if not (step.get("owner") or "").strip():
            errors.append(f"{label}: missing 'owner'.")

    missing = OFFBOARDING_REQUIRED_ACTIONS - present
    if "deactivate_user" in missing:
        errors.append(
            "offboarding.steps: no 'deactivate_user' step. User.IsActive is the only switch "
            "that stops a login; clearing Account.IsPartner does not deactivate anyone."
        )
    if "reassign_records" in missing:
        errors.append(
            "offboarding.steps: no 'reassign_records' step. Leads and Opportunities owned by "
            "a deactivated partner user keep that owner, and PartnerAccountId is derived from "
            "the owner, so reassignment must happen before deactivation."
        )
    return errors


def check_design(design: dict) -> list[str]:
    errors: list[str] = []
    errors.extend(check_tiers(design))
    errors.extend(check_exposed_objects(design))
    errors.extend(check_deal_registration(design))
    errors.extend(check_offboarding(design))
    return errors


def looks_like_design(design: dict) -> bool:
    return any(key in design for key in ("tiers", "exposed_objects", "deal_registration"))


# ---------------------------------------------------------------------------
# Metadata XML checks
# ---------------------------------------------------------------------------


def check_network_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path.name}: not well-formed XML ({exc})."]

    if _local(root.tag) != "Network":
        errors.append(f"{path.name}: root element is <{_local(root.tag)}>, expected <Network>.")
        return errors

    for field in NETWORK_REQUIRED_FIELDS:
        if not _has(root, field):
            errors.append(
                f"{path.name}: missing required Network field <{field}> "
                f"(Metadata API Guide, Network field table)."
            )

    status = _text(root, "status")
    if status is not None and status not in NETWORK_STATUS_VALUES:
        errors.append(
            f"{path.name}: <status>{status}</status> is not a NetworkStatus value. "
            f"Allowed: {', '.join(sorted(NETWORK_STATUS_VALUES))}."
        )

    if _has(root, "template") or _has(root, "networkTemplate"):
        errors.append(
            f"{path.name}: <template> is not a Network field. The Experience Cloud template "
            f"is not carried by the Network component; do not assert the site template from "
            f"this file."
        )

    groups = _first(root, "networkMemberGroups")
    if groups is None:
        errors.append(
            f"{path.name}: no <networkMemberGroups>. No profile or permission set is a member "
            f"of this site, so no partner user can reach it."
        )
    elif not _children(groups, "profile") and not _children(groups, "permissionSet"):
        errors.append(
            f"{path.name}: <networkMemberGroups> contains neither <profile> nor <permissionSet>."
        )

    roles = _first(root, "communityRoles")
    if roles is not None and not _has(roles, "partnerUserRole"):
        errors.append(
            f"{path.name}: <communityRoles> is present but has no <partnerUserRole> label. "
            f"A partner site that labels only customer or employee roles reads wrong in the UI."
        )
    return errors


def check_sharing_set_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path.name}: not well-formed XML ({exc})."]

    if _local(root.tag) != "SharingSet":
        errors.append(f"{path.name}: root element is <{_local(root.tag)}>, expected <SharingSet>.")
        return errors

    name = _text(root, "name")
    if not name:
        errors.append(f"{path.name}: missing required <name>.")

    description = _text(root, "description")
    if description is not None and len(description) > 255:
        errors.append(
            f"{path.name}: <description> is {len(description)} characters; the documented "
            f"limit is 255."
        )

    mappings = _children(root, "accessMappings")
    if not mappings:
        errors.append(f"{path.name}: no <accessMappings>. A sharing set with no mapping grants nothing.")

    for index, mapping in enumerate(mappings, start=1):
        label = f"{path.name} accessMappings[{index}]"
        level = _text(mapping, "accessLevel")
        if level is None:
            errors.append(f"{label}: missing required <accessLevel>.")
        elif level not in SHARING_SET_ACCESS_LEVELS:
            errors.append(
                f"{label}: accessLevel '{level}' is not Read or Edit."
            )

        obj = _text(mapping, "object")
        if obj is None:
            errors.append(f"{label}: missing required <object>.")
        elif not obj.endswith("__c") and obj not in SHARING_SET_OBJECTS:
            errors.append(
                f"{label}: object '{obj}' is not a documented sharing-set target. "
                f"Allowed: {', '.join(sorted(SHARING_SET_OBJECTS))} or a custom object."
            )

        if _text(mapping, "objectField") is None:
            errors.append(f"{label}: missing required <objectField>.")

        user_field = _text(mapping, "userField")
        if user_field is None:
            errors.append(f"{label}: missing required <userField>.")
        else:
            base = user_field.split(".")[0]
            if user_field not in SHARING_SET_USER_FIELDS and base not in {"Account", "Contact", "Manager"}:
                errors.append(
                    f"{label}: userField '{user_field}' is not derived from Account, Contact "
                    f"or Manager. Allowed: {', '.join(sorted(SHARING_SET_USER_FIELDS))} "
                    f"or Account.Field / Contact.Field."
                )
    return errors


def check_manifest_dir(manifest_dir: Path) -> tuple[list[str], int]:
    """Return (errors, files_examined) for the metadata under *manifest_dir*."""
    errors: list[str] = []
    examined = 0

    for path in sorted(manifest_dir.rglob("*.network-meta.xml")) + sorted(
        manifest_dir.rglob("*.network")
    ):
        examined += 1
        errors.extend(check_network_file(path))

    for path in sorted(manifest_dir.rglob("*.sharingSet-meta.xml")) + sorted(
        manifest_dir.rglob("*.sharingSet")
    ):
        examined += 1
        errors.extend(check_sharing_set_file(path))

    return errors, examined


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def lint_design_file(path: Path) -> tuple[list[str], bool]:
    """Return (errors, was_a_design_file)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: cannot read ({exc})."], True

    design, parse_issues = parse_yaml_subset(text)
    if not looks_like_design(design):
        return [f"{path}: no 'tiers' / 'exposed_objects' / 'deal_registration' keys."], False

    errors = [f"{path.name}: {issue}" for issue in parse_issues]
    errors.extend(f"{path.name}: {issue}" for issue in check_design(design))
    return errors, True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a partner-portal design YAML and any retrieved Network / SharingSet "
            "metadata beside it."
        ),
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Path to a partner-portal design YAML. See references/worked-examples.md.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help=(
            "Directory to scan. Design YAML files (*.yaml / *.yml) are linted as designs; "
            "networks/*.network-meta.xml and sharingSets/*.sharingSet-meta.xml are parsed "
            "against the Metadata API field tables."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.file is None and args.manifest_dir is None:
        print(
            "Nothing to check. Pass --file <design.yaml> or --manifest-dir <path>.",
            file=sys.stderr,
        )
        return 1

    errors: list[str] = []
    designs_seen = 0
    metadata_seen = 0

    seen_paths: set[Path] = set()

    if args.file is not None:
        path = Path(args.file)
        if not path.exists():
            errors.append(f"{path}: file not found.")
        else:
            seen_paths.add(path.resolve())
            file_errors, was_design = lint_design_file(path)
            errors.extend(file_errors)
            if was_design:
                designs_seen += 1

    if args.manifest_dir is not None:
        manifest_dir = Path(args.manifest_dir)
        if not manifest_dir.exists():
            errors.append(f"{manifest_dir}: manifest directory not found.")
        else:
            for candidate in sorted(manifest_dir.rglob("*.yaml")) + sorted(
                manifest_dir.rglob("*.yml")
            ):
                if candidate.resolve() in seen_paths:
                    continue
                file_errors, was_design = lint_design_file(candidate)
                if was_design:
                    designs_seen += 1
                    errors.extend(file_errors)
            meta_errors, metadata_seen = check_manifest_dir(manifest_dir)
            errors.extend(meta_errors)

    if designs_seen == 0 and metadata_seen == 0:
        print(
            "No partner-portal design YAML and no Network / SharingSet metadata found. "
            "Nothing was checked.",
            file=sys.stderr,
        )
        return 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"\n{len(errors)} error(s) across {designs_seen} design file(s) and "
            f"{metadata_seen} metadata file(s).",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: {designs_seen} design file(s) and {metadata_seen} metadata file(s) passed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
