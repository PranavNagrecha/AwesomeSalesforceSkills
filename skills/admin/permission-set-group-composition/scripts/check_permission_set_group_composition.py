#!/usr/bin/env python3
"""check_permission_set_group_composition.py

Static checker for Permission Set Group composition tactics described in
`skills/admin/permission-set-group-composition/SKILL.md`.

Scans a Salesforce metadata directory containing
    permissionsetgroups/*.permissionsetgroup-meta.xml
    permissionsets/*.permissionset-meta.xml
    mutingpermissionsets/*.mutingpermissionset-meta.xml   (optional)

and reports, by severity:

  ERROR  PSG with no `<permissionSets>` at all. A group composes permission
         sets; one that composes none grants nothing and cannot be the thing
         the design intends.
  ERROR  The same permission set listed twice inside one PSG.
  ERROR  PSG (or muting permission set) with no `<label>`. `label` is a
         required field on PermissionSetGroup and MutingPermissionSet in the
         Metadata API; a file without one does not deploy.
  ERROR  `<status>` present with a value outside the documented
         PermissionSetGroup status enum (Updated / Outdated / Updating /
         Failed). `status` is read-only on deploy, so its ABSENCE is normal
         and is not a finding.
  ERROR  A PSG or muting file that will not parse as XML.
  WARN   PSG names that violate the `PSG_<persona>_<env>` house convention.
  WARN   Mute Permission Set names that violate `MutePS_<scope>_<delta>`.
  WARN   PSG references a permission set (or mute) whose metadata file is not
         in the tree — usually a partial retrieve, sometimes a real dangling
         reference.
  WARN   Two PSGs differ by exactly one included PS (consolidation candidate
         — likely should be one PSG plus a mute).
  INFO   No PSG files under the scanned tree; nothing to compose.
  GOOD   PSes referenced in multiple PSGs (composition reuse — desired)
  GOOD   PSGs that include a Mute Permission Set (explicit subtract — desired)
  ERROR  PSGC-DESC-01 -- a PermissionSet, PermissionSetGroup, or
         MutingPermissionSet file whose <description> exceeds 255 characters.
         Grounded for PermissionSet: Metadata API Developer Guide, "The
         permission set description. Limit: 255 characters." (api_meta
         L94788); MutingPermissionSet shares PermissionSet's field table.
         Empirically confirmed by `sf project deploy start --dry-run` against
         a Summer '26 developer org on 2026-09-11: four PermissionSet files
         rejected with `Description: data value too large ... (max
         length=255)` (examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md,
         once exported). PermissionSetGroup.description has no documented
         limit (api_meta L95328) -- UNVERIFIED (2026-09-11) as a direct
         rejection, applied here anyway because a PSG that references a
         rejected member set fails to deploy as a cascade ("permission set
         names are invalid").
  WARN   PSGC-DESC-02 -- the same file types with a <description> over 200
         characters (headroom below the 255-character limit).

Naming conventions are house style, not platform behaviour, so they never
fail the run on their own. Use `--strict` in a governance gate where the
convention is enforced.

stdlib only.

Exit codes:
  0 -- no ERROR (and no WARN when --strict is passed)
  1 -- at least one ERROR, or at least one WARN under --strict
  2 -- the manifest directory does not exist

Usage:
    python3 check_permission_set_group_composition.py --manifest-dir <path>
    python3 check_permission_set_group_composition.py --manifest-dir <path> --strict

The <path> may point at the project root, the `force-app/main/default/`
directory, or any parent of the `permissionsetgroups/` and `permissionsets/`
folders — the checker walks recursively.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

SF_NS = "http://soap.sforce.com/2006/04/metadata"

PSG_NAME_RE = re.compile(r"^PSG_[A-Za-z0-9]+_[A-Za-z0-9]+$")
# MutePS_<scope>_<delta>, but also accept the common shorthand
# MutePS_<descriptor> (e.g. MutePS_NoOpportunityDelete) — the prefix is the
# load-bearing part because it makes the file searchable as a mute.
MUTE_NAME_RE = re.compile(r"^MutePS_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$")

# PermissionSetGroup.status is read-only on deploy; the Metadata API documents
# exactly these values. Absence is normal, an unknown value is not.
PSG_STATUS_VALUES = {"Updated", "Outdated", "Updating", "Failed"}

# PSGC-DESC-01 / PSGC-DESC-02 thresholds. 255 is the Metadata API's documented
# ceiling for PermissionSet.description; 200 is headroom to catch a
# description before it grows past the limit.
DESC_MAX_LEN = 255
DESC_WARN_LEN = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Permission Set Group composition for multi-PSG PSes (good),"
            " mute usage (good), orphan PSGs, and naming-convention violations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit 1 on warnings as well as errors — use where the "
            "PSG_<persona>_<env> naming convention is actually enforced."
        ),
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    """Strip an XML namespace prefix from a tag, if present."""
    return tag.rsplit("}", 1)[-1]


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def find_psg_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.permissionsetgroup-meta.xml"))


def find_ps_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.permissionset-meta.xml"))


def find_mute_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.mutingpermissionset-meta.xml"))


def stem_developer_name(path: Path) -> str:
    """`PSG_SalesRep_Prod.permissionsetgroup-meta.xml` -> `PSG_SalesRep_Prod`."""
    name = path.name
    for suffix in (
        ".permissionsetgroup-meta.xml",
        ".permissionset-meta.xml",
        ".mutingpermissionset-meta.xml",
    ):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def child_text_values(root: ET.Element, child_name: str) -> list[str]:
    """Return text values for all top-level children matching child_name (namespace-agnostic)."""
    results: list[str] = []
    for elem in root:
        if local_name(elem.tag) == child_name:
            text = (elem.text or "").strip()
            if text:
                results.append(text)
    return results


def check_description_length(
    path: Path, root: ET.Element, kind: str
) -> tuple[list[str], list[str]]:
    """PSGC-DESC-01 (ERROR, >255 chars) / PSGC-DESC-02 (WARN, >200 chars).

    Grounded for PermissionSet: Metadata API Developer Guide, "The permission
    set description. Limit: 255 characters." (api_meta L94788).
    MutingPermissionSet has the same field table as PermissionSet.
    Empirically confirmed by `sf project deploy start --dry-run` against a
    Summer '26 developer org on 2026-09-11: four PermissionSet files rejected
    with `Description: data value too large ... (max length=255)`
    (examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md, once
    exported). PermissionSetGroup.description has no documented limit
    (api_meta L95328) -- UNVERIFIED (2026-09-11) as a direct rejection,
    applied here anyway because a PSG that references a rejected member set
    fails to deploy as a cascade ("permission set names are invalid")
    regardless of its own description length.
    """
    errs: list[str] = []
    warns: list[str] = []
    description = "".join(child_text_values(root, "description"))
    if not description:
        return errs, warns
    length = len(description)
    if length > DESC_MAX_LEN:
        errs.append(
            f"{path}: PSGC-DESC-01 {kind} description is {length} characters, "
            f"over the {DESC_MAX_LEN}-character limit; move rationale to "
            "deploy-order.md or the configuration workbook."
        )
    elif length > DESC_WARN_LEN:
        warns.append(
            f"{path}: PSGC-DESC-02 {kind} description is {length} characters, "
            f"approaching the {DESC_MAX_LEN}-character limit."
        )
    return errs, warns


def analyse(
    manifest_dir: Path,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return (good_findings, error_findings, warn_findings, info_findings)."""
    goods: list[str] = []
    errors: list[str] = []
    warns: list[str] = []
    infos: list[str] = []

    psg_files = find_psg_files(manifest_dir)
    ps_files = find_ps_files(manifest_dir)
    mute_files = find_mute_files(manifest_dir)

    if not psg_files:
        infos.append(
            f"No *.permissionsetgroup-meta.xml files found under {manifest_dir}; "
            f"nothing to compose. If a PSG was expected here, the retrieve or "
            f"the build step scope is wrong."
        )
        return goods, errors, warns, infos

    # Muting permission sets are their own metadata type and carry a required
    # label of their own.
    for mute_path in mute_files:
        mute_root = parse_xml(mute_path)
        if mute_root is None:
            errors.append(f"{mute_path}: unable to parse muting permission set metadata.")
            continue
        if not child_text_values(mute_root, "label"):
            errors.append(
                f"{mute_path}: muting permission set has no <label>; label is a "
                f"required field and the file will not deploy without one."
            )
        desc_errs, desc_warns = check_description_length(mute_path, mute_root, "MutingPermissionSet")
        errors.extend(desc_errs)
        warns.extend(desc_warns)

    for ps_path in ps_files:
        ps_root = parse_xml(ps_path)
        if ps_root is None:
            errors.append(f"{ps_path}: unable to parse permission set metadata.")
            continue
        desc_errs, desc_warns = check_description_length(ps_path, ps_root, "PermissionSet")
        errors.extend(desc_errs)
        warns.extend(desc_warns)

    ps_names_known: set[str] = {stem_developer_name(p) for p in ps_files}
    mute_names_known: set[str] = {stem_developer_name(p) for p in mute_files}

    # Map of permission set name -> list of PSG names that include it.
    ps_to_psgs: dict[str, list[str]] = {}
    # Map of PSG name -> sorted tuple of included PS names (for overlap analysis).
    psg_composition: dict[str, tuple[str, ...]] = {}
    # PSGs that include at least one mute.
    psgs_with_mutes: list[tuple[str, list[str]]] = []
    # PSGs with no included PSes.
    orphan_psgs: list[str] = []

    for psg_path in psg_files:
        root = parse_xml(psg_path)
        psg_name = stem_developer_name(psg_path)
        if root is None:
            errors.append(f"{psg_path}: unable to parse PSG metadata.")
            continue

        desc_errs, desc_warns = check_description_length(psg_path, root, "PermissionSetGroup")
        errors.extend(desc_errs)
        warns.extend(desc_warns)

        included_pses = child_text_values(root, "permissionSets")
        included_mutes = child_text_values(root, "mutingPermissionSets")

        # ERROR: required label.
        if not child_text_values(root, "label"):
            errors.append(
                f"{psg_path}: PSG '{psg_name}' has no <label>; label is a "
                f"required field on PermissionSetGroup and the file will not "
                f"deploy without one."
            )

        # ERROR: status present but not a documented value. Absence is normal
        # (the field is read-only on deploy), so absence is never a finding.
        declared_status = child_text_values(root, "status")
        for status_value in declared_status:
            if status_value not in PSG_STATUS_VALUES:
                errors.append(
                    f"{psg_path}: PSG '{psg_name}' declares <status>"
                    f"{status_value}</status>, which is not one of "
                    f"{sorted(PSG_STATUS_VALUES)}."
                )

        # ERROR: the same permission set listed twice in one group.
        seen_pses: set[str] = set()
        for ps_name in included_pses:
            if ps_name in seen_pses:
                errors.append(
                    f"{psg_path}: PSG '{psg_name}' lists permission set "
                    f"'{ps_name}' more than once."
                )
            seen_pses.add(ps_name)

        psg_composition[psg_name] = tuple(sorted(included_pses))

        if not included_pses:
            orphan_psgs.append(psg_name)

        if included_mutes:
            psgs_with_mutes.append((psg_name, included_mutes))

        for ps_name in sorted(set(included_pses)):
            ps_to_psgs.setdefault(ps_name, []).append(psg_name)

        # Naming-convention check on the PSG itself. House style, not a
        # platform rule — WARN, never ERROR.
        if not PSG_NAME_RE.match(psg_name):
            warns.append(
                f"{psg_path}: PSG name '{psg_name}' does not match convention "
                f"PSG_<persona>_<env> (e.g. PSG_SalesRep_Prod)."
            )

        # Reference integrity — flag PSGs that include a PS we cannot find.
        for ps_name in included_pses:
            if ps_names_known and ps_name not in ps_names_known:
                warns.append(
                    f"{psg_path}: includes permission set '{ps_name}' but no "
                    f"matching *.permissionset-meta.xml file was found in "
                    f"{manifest_dir}."
                )
        for mute_name in included_mutes:
            if mute_names_known and mute_name not in mute_names_known:
                warns.append(
                    f"{psg_path}: includes muting permission set '{mute_name}' "
                    f"but no matching *.mutingpermissionset-meta.xml file was "
                    f"found — change-set or package.xml may have missed the "
                    f"MutingPermissionSet metadata type."
                )

    # GOOD: PSes referenced in multiple PSGs (composition reuse working).
    for ps_name, psg_list in sorted(ps_to_psgs.items()):
        if len(psg_list) >= 2:
            goods.append(
                f"reuse: permission set '{ps_name}' is referenced by "
                f"{len(psg_list)} PSGs ({', '.join(sorted(set(psg_list)))}) — "
                f"composition reuse working as intended."
            )

    # GOOD: PSGs that use mutes (explicit subtract — desired pattern).
    for psg_name, mutes in sorted(psgs_with_mutes):
        for mute_name in mutes:
            goods.append(
                f"mute: PSG '{psg_name}' uses muting permission set "
                f"'{mute_name}' — explicit subtractive delta, preferred over "
                f"cloning."
            )
            if not MUTE_NAME_RE.match(mute_name):
                warns.append(
                    f"PSG '{psg_name}': muting permission set name "
                    f"'{mute_name}' does not match convention "
                    f"MutePS_<scope>_<delta> (e.g. MutePS_NoOpportunityDelete)."
                )

    # ERROR: orphan PSGs — a group that composes nothing grants nothing.
    for psg_name in sorted(orphan_psgs):
        errors.append(
            f"PSG '{psg_name}' has zero included permission sets; "
            f"either delete the PSG or add the PSes that define its access."
        )

    # WARN: PSG pairs that differ by exactly one included PS — possible
    # consolidation candidates (almost-clones that should be one PSG + mute).
    psg_names = sorted(psg_composition.keys())
    for i in range(len(psg_names)):
        for j in range(i + 1, len(psg_names)):
            a_name = psg_names[i]
            b_name = psg_names[j]
            a_set = set(psg_composition[a_name])
            b_set = set(psg_composition[b_name])
            if not a_set or not b_set:
                continue
            symmetric_diff = a_set.symmetric_difference(b_set)
            shared = a_set.intersection(b_set)
            # Heuristic: 4+ shared PSes and exactly one PS difference -> likely
            # a clone-and-edit pair that should be one PSG + a mute.
            if len(shared) >= 4 and len(symmetric_diff) == 1:
                warns.append(
                    f"PSGs '{a_name}' and '{b_name}' share {len(shared)} "
                    f"permission sets and differ by exactly one ({sorted(symmetric_diff)[0]}). "
                    f"Likely a clone-and-edit pair — consider one PSG plus a "
                    f"Mute Permission Set instead."
                )

    return goods, errors, warns, infos


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.is_dir():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    goods, errors, warns, infos = analyse(manifest_dir)

    for finding in goods:
        print(f"GOOD: {finding}")

    for finding in infos:
        print(f"INFO: {finding}")

    for finding in errors:
        print(f"ERROR: {finding}", file=sys.stderr)

    for finding in warns:
        print(f"WARN: {finding}", file=sys.stderr)

    summary = (
        f"Summary: {len(goods)} good, {len(errors)} error, {len(warns)} warn, "
        f"{len(infos)} info, scanned "
        f"{len(find_psg_files(manifest_dir))} PSG file(s)."
    )
    print("")
    print(summary)

    if errors:
        return 1
    if args.strict and warns:
        print("--strict: failing on warnings.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
