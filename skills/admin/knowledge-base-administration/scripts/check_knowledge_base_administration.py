#!/usr/bin/env python3
"""Checker script for the Knowledge Base Administration skill.

Lints a retrieved Salesforce metadata directory for the Lightning Knowledge
configuration mistakes that deploy cleanly and then show nobody any articles:

- KnowledgeSettings with enableKnowledge true but enableLightningKnowledge false
  (the org is on Knowledge in Salesforce Classic, not Lightning Knowledge)
- DataCategoryGroup with active=false
- DataCategoryGroup with no objectUsage/object, so no article can be classified by it
- DataCategoryGroup hierarchy deeper than the heuristic depth (default 3 of the
  5 levels the Metadata API guide allows), and category counts near the 100 cap
- Profile categoryGroupVisibilities naming a group, or a category, that is not in
  the retrieved datacategorygroups tree
- Permission sets carrying Knowledge__kav object permissions but no profile in the
  package grants category visibility (permission sets cannot carry it)
- Knowledge__kav with no record types, no layouts, and approval processes without
  a Validation Status field

Grounding: Metadata API Developer Guide (KnowledgeSettings, DataCategoryGroup,
ObjectUsage, ProfileCategoryGroupVisibility, PermissionSet) and the Object
Reference (Knowledge__kav). See ../references/metadata-examples.md.

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_knowledge_base_administration.py --help
    python3 check_knowledge_base_administration.py --manifest-dir force-app/main/default
    python3 check_knowledge_base_administration.py --manifest-dir . --knowledge-object Article__kav
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://soap.sforce.com/2006/04/metadata"

# The Metadata API guide caps a data category group at 5 hierarchy levels and 100
# categories. This checker INFOs earlier than that: past three levels a taxonomy is
# usually better split, and the count warning gives room to react before the cap.
HEURISTIC_MAX_DEPTH = 3
GUIDE_MAX_DEPTH = 5
GUIDE_MAX_CATEGORIES = 100


class Finding:
    """One issue, with a severity the caller renders and the exit code ignores."""

    def __init__(self, severity: str, message: str) -> None:
        self.severity = severity
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a retrieved Salesforce metadata directory for Lightning Knowledge "
            "configuration issues that deploy cleanly and hide articles."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the retrieved Salesforce metadata, e.g. force-app/main/default (default: .).",
    )
    parser.add_argument(
        "--knowledge-object",
        default="Knowledge__kav",
        help=(
            "API name of the knowledge object. Knowledge__kav is only the default; "
            "the prefix can be renamed in Object Manager (default: Knowledge__kav)."
        ),
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=HEURISTIC_MAX_DEPTH,
        help=(
            f"Data category hierarchy depth above which to emit an INFO. The platform "
            f"allows {GUIDE_MAX_DEPTH} levels (default: {HEURISTIC_MAX_DEPTH})."
        ),
    )
    return parser.parse_args()


# --------------------------------------------------------------------------- #
# ElementTree helpers.
#
# A leaf Element is falsy, so `node.find(a) or node.find(b)` silently discards a
# real match. Every lookup below goes through these helpers, which test `is not
# None` explicitly and try the namespaced form before the bare one.
# --------------------------------------------------------------------------- #


def _find(node: ET.Element, tag: str) -> ET.Element | None:
    found = node.find(f"{{{NS}}}{tag}")
    if found is not None:
        return found
    return node.find(tag)


def _findall(node: ET.Element, tag: str) -> list[ET.Element]:
    found = node.findall(f"{{{NS}}}{tag}")
    if found:
        return found
    return node.findall(tag)


def _text(node: ET.Element, tag: str) -> str:
    child = _find(node, tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _parse(path: Path, findings: list[Finding]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(Finding("ERROR", f"Could not parse '{path}': {exc}"))
        return None


# --------------------------------------------------------------------------- #
# Data category groups
# --------------------------------------------------------------------------- #


def _walk_categories(
    node: ET.Element, depth: int, names: set[str], deepest: list[int]
) -> None:
    """Collect every category developer name and track the deepest level reached."""
    for child in _findall(node, "dataCategory"):
        name = _text(child, "name")
        if name:
            names.add(name)
        deepest[0] = max(deepest[0], depth)
        _walk_categories(child, depth + 1, names, deepest)


def read_data_category_groups(
    manifest_dir: Path, findings: list[Finding], max_depth: int
) -> dict[str, set[str]]:
    """Check every DataCategoryGroup file; return {group name: {category names}}."""
    groups: dict[str, set[str]] = {}
    dcg_dir = manifest_dir / "datacategorygroups"
    if not dcg_dir.exists():
        return groups

    # The guide gives the suffix as .datacategorygroup; DX source format appends
    # -meta.xml. Accept both so this runs on either project shape.
    files = sorted(
        set(dcg_dir.glob("*.datacategorygroup-meta.xml")) | set(dcg_dir.glob("*.datacategorygroup"))
    )
    for dcg_file in files:
        root = _parse(dcg_file, findings)
        if root is None:
            continue

        group_name = _text(root, "fullName") or dcg_file.name.split(".")[0]
        names: set[str] = set()
        deepest = [0]
        _walk_categories(root, 1, names, deepest)
        groups[group_name] = names

        # Check 1: inactive group. Deployable, but classifies nothing.
        if _text(root, "active").lower() != "true":
            findings.append(
                Finding(
                    "INFO",
                    f"Data category group '{group_name}' has active != true. It deploys, but no "
                    f"article can be classified against it and articles already tagged with its "
                    f"categories behave as unclassified. Set <active>true</active> when the "
                    f"taxonomy goes live ({dcg_file}).",
                )
            )

        # Check 2: no objectUsage. The single most common silent Knowledge failure.
        usage_objects = [
            _text(usage_el, "object")
            for usage in _findall(root, "objectUsage")
            for usage_el in [usage]
        ]
        usage_objects = [obj for obj in usage_objects if obj]
        if not usage_objects:
            findings.append(
                Finding(
                    "WARN",
                    f"Data category group '{group_name}' has no <objectUsage><object>. It is not "
                    f"associated with any object, so it never appears when classifying an article. "
                    f"Add <object>KnowledgeArticleVersion</object>. Note that a later deploy "
                    f"omitting this element permanently removes an assignment made in Setup "
                    f"({dcg_file}).",
                )
            )
        elif not any("Knowledge" in obj for obj in usage_objects):
            findings.append(
                Finding(
                    "WARN",
                    f"Data category group '{group_name}' declares objectUsage "
                    f"{sorted(usage_objects)} but not KnowledgeArticleVersion, so it classifies "
                    f"something other than Knowledge articles ({dcg_file}).",
                )
            )

        # Check 3: hierarchy depth and category count against the guide's caps.
        if deepest[0] > GUIDE_MAX_DEPTH:
            findings.append(
                Finding(
                    "WARN",
                    f"Data category group '{group_name}' nests {deepest[0]} levels deep. The "
                    f"Metadata API guide allows {GUIDE_MAX_DEPTH} levels in a data category group "
                    f"hierarchy; this will not deploy ({dcg_file}).",
                )
            )
        elif deepest[0] > max_depth:
            findings.append(
                Finding(
                    "INFO",
                    f"Data category group '{group_name}' nests {deepest[0]} levels deep, past the "
                    f"heuristic depth of {max_depth} used here (the platform cap is "
                    f"{GUIDE_MAX_DEPTH}). Deep trees are slower to browse and expensive to "
                    f"restructure, because a category developer name cannot be renamed and moving "
                    f"a category costs visibility for anyone who cannot see its new parent. See "
                    f"architect/knowledge-taxonomy-design ({dcg_file}).",
                )
            )
        if len(names) > GUIDE_MAX_CATEGORIES:
            findings.append(
                Finding(
                    "WARN",
                    f"Data category group '{group_name}' defines {len(names)} categories. The "
                    f"Metadata API guide allows up to {GUIDE_MAX_CATEGORIES} per group "
                    f"({dcg_file}).",
                )
            )

    return groups


# --------------------------------------------------------------------------- #
# Knowledge settings
# --------------------------------------------------------------------------- #


def check_knowledge_settings(manifest_dir: Path, findings: list[Finding]) -> None:
    """Check settings/Knowledge.settings for the Classic-vs-Lightning fork."""
    candidates = [
        manifest_dir / "settings" / "Knowledge.settings-meta.xml",
        manifest_dir / "settings" / "Knowledge.settings",
    ]
    settings_file = next((path for path in candidates if path.exists()), None)
    if settings_file is None:
        return

    root = _parse(settings_file, findings)
    if root is None:
        return

    knowledge_on = _text(root, "enableKnowledge").lower() == "true"
    lightning_on = _text(root, "enableLightningKnowledge").lower() == "true"

    # Check 4: Knowledge on, Lightning Knowledge off -> the org is on Classic.
    if knowledge_on and not lightning_on:
        findings.append(
            Finding(
                "WARN",
                "Knowledge settings set enableKnowledge=true with enableLightningKnowledge not "
                "true. That is Knowledge in Salesforce Classic: articles live on per-type "
                "<ArticleType>__kav objects, not one Knowledge__kav with record types, and this "
                "skill's record type and Knowledge__kav guidance does not apply. Use "
                f"admin/knowledge-classic-to-lightning ({settings_file}).",
            )
        )

    if knowledge_on and not _text(root, "defaultLanguage"):
        findings.append(
            Finding(
                "WARN",
                "Knowledge settings have no <defaultLanguage>. The Metadata API guide marks it "
                f"required; it takes the locale form, for example en_US ({settings_file}).",
            )
        )

    # <language><name> takes the bare language code ("English is en"), while
    # defaultLanguage takes the locale form. Mixing them fails the deploy.
    languages = _find(root, "languages")
    if languages is not None:
        for language in _findall(languages, "language"):
            name = _text(language, "name")
            if "_" in name:
                findings.append(
                    Finding(
                        "WARN",
                        f"Knowledge settings declare a language <name>{name}</name>. Per the "
                        f"Metadata API guide, KnowledgeLanguage.name takes the bare language code "
                        f"(English is 'en'); only defaultLanguage takes the locale form "
                        f"({settings_file}).",
                    )
                )
            assignee_type = _text(language, "defaultAssigneeType")
            if assignee_type and assignee_type not in {"User", "Queue"}:
                findings.append(
                    Finding(
                        "WARN",
                        f"Language '{name}' has defaultAssigneeType '{assignee_type}'. Valid "
                        f"values are User and Queue ({settings_file}).",
                    )
                )

    if knowledge_on and lightning_on and _text(root, "showValidationStatusField").lower() != "true":
        findings.append(
            Finding(
                "INFO",
                "showValidationStatusField is not true, so Knowledge__kav.ValidationStatus is not "
                "surfaced. That is fine if the publishing workflow uses native statuses only; it "
                "breaks any approval design that hands off through Validation Status "
                f"({settings_file}).",
            )
        )


# --------------------------------------------------------------------------- #
# Profiles and permission sets
# --------------------------------------------------------------------------- #


def check_profile_category_visibility(
    manifest_dir: Path, findings: list[Finding], groups: dict[str, set[str]]
) -> int:
    """Check profile categoryGroupVisibilities against the retrieved category tree.

    Returns the number of profiles that grant any category visibility.
    """
    profiles_dir = manifest_dir / "profiles"
    if not profiles_dir.exists():
        return 0

    granting_profiles = 0
    files = sorted(
        set(profiles_dir.glob("*.profile-meta.xml")) | set(profiles_dir.glob("*.profile"))
    )
    for profile_file in files:
        root = _parse(profile_file, findings)
        if root is None:
            continue

        visibilities = _findall(root, "categoryGroupVisibilities")
        if visibilities:
            granting_profiles += 1

        for visibility in visibilities:
            group_name = _text(visibility, "dataCategoryGroup")
            level = _text(visibility, "visibility")

            # Check 5: visibility pointing at a group not present in the package.
            if group_name and groups and group_name not in groups:
                findings.append(
                    Finding(
                        "WARN",
                        f"Profile '{profile_file.name}' grants visibility to data category group "
                        f"'{group_name}', which is not among the retrieved groups "
                        f"({', '.join(sorted(groups)) or 'none'}). Either the group is missing "
                        f"from the package - deploy the profile and the visibility silently does "
                        f"not apply - or the group name is misspelled.",
                    )
                )
            elif group_name in groups:
                for category in _findall(visibility, "dataCategories"):
                    value = (category.text or "").strip()
                    if value and value not in groups[group_name]:
                        findings.append(
                            Finding(
                                "WARN",
                                f"Profile '{profile_file.name}' grants visibility to category "
                                f"'{value}' in group '{group_name}', but that category is not in "
                                f"the group's tree. Category developer names cannot be renamed, so "
                                f"this is usually a stale name left behind by a restructure.",
                            )
                        )

            if level and level not in {"ALL", "CUSTOM", "NONE"}:
                findings.append(
                    Finding(
                        "WARN",
                        f"Profile '{profile_file.name}' sets visibility '{level}' for group "
                        f"'{group_name}'. Valid values are ALL, CUSTOM and NONE.",
                    )
                )
            if level == "CUSTOM" and not _findall(visibility, "dataCategories"):
                findings.append(
                    Finding(
                        "WARN",
                        f"Profile '{profile_file.name}' sets visibility CUSTOM for group "
                        f"'{group_name}' but lists no <dataCategories>. That grants nothing.",
                    )
                )

    return granting_profiles


def check_permission_sets(
    manifest_dir: Path,
    findings: list[Finding],
    knowledge_object: str,
    groups: dict[str, set[str]],
    granting_profiles: int,
) -> None:
    """Check permission sets that touch the knowledge object."""
    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return

    files = sorted(
        set(ps_dir.glob("*.permissionset-meta.xml")) | set(ps_dir.glob("*.permissionset"))
    )
    for ps_file in files:
        root = _parse(ps_file, findings)
        if root is None:
            continue

        touches_knowledge = any(
            _text(perm, "object") == knowledge_object
            for perm in _findall(root, "objectPermissions")
        )
        if not touches_knowledge:
            continue

        # The Metadata API documents categoryGroupVisibilities on Profile only.
        # If someone hand-added it here, say so before the deploy fails.
        if _findall(root, "categoryGroupVisibilities"):
            findings.append(
                Finding(
                    "WARN",
                    f"Permission set '{ps_file.name}' contains <categoryGroupVisibilities>. The "
                    f"Metadata API documents that element on Profile only "
                    f"(ProfileCategoryGroupVisibility, API 41.0+); PermissionSet has no "
                    f"equivalent. Move it to the profile.",
                )
            )

        if groups and granting_profiles == 0:
            findings.append(
                Finding(
                    "WARN",
                    f"Permission set '{ps_file.name}' grants object access to {knowledge_object}, "
                    f"but no profile in this package grants any data category visibility. "
                    f"Permission sets cannot carry it. Users get the object and the Articles tab "
                    f"and see no articles.",
                )
            )


# --------------------------------------------------------------------------- #
# Knowledge object: record types, layouts, approval processes
# --------------------------------------------------------------------------- #


def check_knowledge_object(
    manifest_dir: Path, findings: list[Finding], knowledge_object: str
) -> None:
    object_dir = manifest_dir / "objects" / knowledge_object
    if not object_dir.exists():
        return

    record_types_dir = object_dir / "recordTypes"
    if not record_types_dir.exists() or not any(record_types_dir.glob("*.recordType*")):
        findings.append(
            Finding(
                "WARN",
                f"{knowledge_object} has no record types under {record_types_dir}. In Lightning "
                f"Knowledge the article type is the RecordType field on this object. Note that "
                f"RecordType does not support the package.xml wildcard - if the manifest used "
                f"'*', the record types were never retrieved and may exist in the org.",
            )
        )

    layouts_dir = manifest_dir / "layouts"
    if layouts_dir.exists() and not list(layouts_dir.glob(f"{knowledge_object}-*.layout*")):
        findings.append(
            Finding(
                "INFO",
                f"No page layouts found matching 'layouts/{knowledge_object}-*.layout*'. Each "
                f"record type needs a layout. Remember the guide's warning that record types are "
                f"not an access control: a user who cannot create with a record type can still "
                f"read records that use it, so internal fields need field permissions too.",
            )
        )

    approval_dir = manifest_dir / "approvalProcesses"
    if not approval_dir.exists():
        return

    approvals = sorted(approval_dir.glob(f"{knowledge_object}.*"))
    if not approvals:
        return

    fields_dir = object_dir / "fields"
    has_validation_status = fields_dir.exists() and any(
        fields_dir.glob("ValidationStatus.field*")
    )
    if not has_validation_status:
        findings.append(
            Finding(
                "INFO",
                f"Approval processes target {knowledge_object} but no ValidationStatus field file "
                f"was retrieved. ValidationStatus is a standard field surfaced by "
                f"showValidationStatusField in Knowledge settings, and is the usual handshake "
                f"between author and approver. Confirm the settings flag is on.",
            )
        )

    for approval_file in approvals:
        root = _parse(approval_file, findings)
        if root is None:
            continue
        if not _findall(root, "approvalStep"):
            findings.append(
                Finding(
                    "WARN",
                    f"Approval process '{approval_file.name}' on {knowledge_object} has no "
                    f"approval steps. An approval process without steps gates nothing.",
                )
            )


# --------------------------------------------------------------------------- #


def check_knowledge_base_administration(
    manifest_dir: Path, knowledge_object: str, max_depth: int
) -> list[Finding]:
    findings: list[Finding] = []

    if not manifest_dir.exists():
        findings.append(Finding("ERROR", f"Manifest directory not found: {manifest_dir}"))
        return findings

    groups = read_data_category_groups(manifest_dir, findings, max_depth)
    check_knowledge_settings(manifest_dir, findings)
    granting_profiles = check_profile_category_visibility(manifest_dir, findings, groups)
    check_permission_sets(manifest_dir, findings, knowledge_object, groups, granting_profiles)
    check_knowledge_object(manifest_dir, findings, knowledge_object)

    return findings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    findings = check_knowledge_base_administration(
        manifest_dir, args.knowledge_object, args.max_depth
    )

    if not findings:
        print(f"No issues found under {manifest_dir} for {args.knowledge_object}.")
        return 0

    for finding in findings:
        print(str(finding), file=sys.stderr)

    print(
        f"\n{len(findings)} finding(s). INFO items are worth a look; WARN and ERROR items "
        f"hide articles or fail the deploy.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
