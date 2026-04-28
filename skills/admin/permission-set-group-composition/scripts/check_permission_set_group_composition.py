#!/usr/bin/env python3
"""check_permission_set_group_composition.py

Static checker for Permission Set Group composition tactics described in
`skills/admin/permission-set-group-composition/SKILL.md`.

Scans a Salesforce metadata directory containing
    permissionsetgroups/*.permissionsetgroup-meta.xml
    permissionsets/*.permissionset-meta.xml
    mutingpermissionsets/*.mutingpermissionset-meta.xml   (optional)

and reports:

  GOOD   PSes referenced in multiple PSGs            (composition reuse — desired)
  GOOD   PSGs that include a Mute Permission Set     (explicit subtract — desired)
  WARN   PSG with NO included permission sets        (orphan)
  WARN   PSG names that violate `PSG_<persona>_<env>` convention
  WARN   Mute Permission Set names that violate `MutePS_<scope>_<delta>` convention
  WARN   PSG references a permission set whose metadata file is missing
  WARN   Two PSGs differ by exactly one included PS  (consolidation candidate
         — likely should be one PSG plus a mute)

stdlib only. Exits 1 on any WARN finding, 0 if only GOOD findings (or empty).

Usage:
    python3 check_permission_set_group_composition.py --manifest-dir <path>

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


def analyse(manifest_dir: Path) -> tuple[list[str], list[str]]:
    """Return (good_findings, warn_findings)."""
    goods: list[str] = []
    warns: list[str] = []

    if not manifest_dir.exists():
        warns.append(f"Manifest directory not found: {manifest_dir}")
        return goods, warns

    psg_files = find_psg_files(manifest_dir)
    ps_files = find_ps_files(manifest_dir)
    mute_files = find_mute_files(manifest_dir)

    if not psg_files:
        warns.append(
            f"No *.permissionsetgroup-meta.xml files found under {manifest_dir}; "
            f"nothing to compose."
        )
        return goods, warns

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
            warns.append(f"{psg_path}: unable to parse PSG metadata.")
            continue

        included_pses = child_text_values(root, "permissionSets")
        included_mutes = child_text_values(root, "mutingPermissionSets")

        psg_composition[psg_name] = tuple(sorted(included_pses))

        if not included_pses:
            orphan_psgs.append(psg_name)

        if included_mutes:
            psgs_with_mutes.append((psg_name, included_mutes))

        for ps_name in included_pses:
            ps_to_psgs.setdefault(ps_name, []).append(psg_name)

        # Naming-convention check on the PSG itself.
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

    # WARN: orphan PSGs.
    for psg_name in sorted(orphan_psgs):
        warns.append(
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

    return goods, warns


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    goods, warns = analyse(manifest_dir)

    for finding in goods:
        print(f"GOOD: {finding}")

    for finding in warns:
        print(f"WARN: {finding}", file=sys.stderr)

    summary = (
        f"Summary: {len(goods)} good, {len(warns)} warn, scanned "
        f"{len(find_psg_files(manifest_dir))} PSG file(s)."
    )
    print("")
    print(summary)

    if warns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
