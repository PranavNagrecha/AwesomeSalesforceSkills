#!/usr/bin/env python3
"""Audit PermissionSetGroup, MutingPermissionSet, PermissionSet, and Profile metadata.

Rules (grounded in the Metadata API Developer Guide and Object Reference, Summer '26):

  ERROR   a metadata file does not parse
  HIGH    a muting permission set enables nothing (every permission value is false):
          in a muting set, ENABLED means MUTED, so an all-false file mutes nothing
          and usually means the author inverted the semantics
  MEDIUM  a muting set mutes an object or field permission that a profile in the
          same tree also grants; muting acts only inside the group, so users of that
          profile keep the access
  REVIEW  a group references a permission set or muting set that is not in the tree
          (the group file holds no permissions; deploy them together)
  REVIEW  a group lists more than one muting permission set
  REVIEW  more than 10 profiles and no permission set groups (profile-heavy model)

Exit codes: 1 if the directory is missing or any ERROR/HIGH finding exists
(MEDIUM and REVIEW too with --strict); 0 otherwise. Prints a JSON summary.
Stdlib only.

Usage:
    python3 check_permission_set_groups_and_muting.py --manifest-dir force-app [--strict]
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PERM_FLAGS = {"allowCreate", "allowDelete", "allowEdit", "allowRead", "modifyAllRecords", "viewAllRecords",
              "editable", "readable", "enabled", "visible"}
WEIGHTS = {"ERROR": 25, "HIGH": 10, "MEDIUM": 5, "REVIEW": 0}


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _files(root: Path, suffix: str) -> list[Path]:
    return sorted(p for p in root.rglob(f"*{suffix}") if p.is_file())


def _parse(path: Path, findings: list[tuple[str, str, str]]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(("ERROR", str(path), f"XML does not parse: {exc}"))
        return None


def _name(path: Path, suffix: str) -> str:
    return path.name[: -len(suffix)]


def _grants(root: ET.Element) -> set[str]:
    """Return keys like 'object:Case:allowDelete' or 'field:Case.Priority:editable' that are true."""
    keys: set[str] = set()
    for block in root:
        tag = _local(block.tag)
        if tag == "objectPermissions":
            obj = next(((c.text or "").strip() for c in block if _local(c.tag) == "object"), "")
            for c in block:
                if _local(c.tag) in PERM_FLAGS and (c.text or "").strip() == "true":
                    keys.add(f"object:{obj}:{_local(c.tag)}")
        elif tag == "fieldPermissions":
            fld = next(((c.text or "").strip() for c in block if _local(c.tag) == "field"), "")
            for c in block:
                if _local(c.tag) in ("editable", "readable") and (c.text or "").strip() == "true":
                    keys.add(f"field:{fld}:{_local(c.tag)}")
    return keys


def _any_true(root: ET.Element) -> bool:
    for el in root.iter():
        if _local(el.tag) in PERM_FLAGS and (el.text or "").strip() == "true":
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check permission set group and muting metadata.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of retrieved metadata.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on MEDIUM and REVIEW findings too.")
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    findings: list[tuple[str, str, str]] = []
    psg_sfx, mute_sfx, ps_sfx, prof_sfx = (".permissionsetgroup-meta.xml", ".mutingpermissionset-meta.xml",
                                           ".permissionset-meta.xml", ".profile-meta.xml")
    psgs = _files(root, psg_sfx)
    mutes = _files(root, mute_sfx)
    psets = _files(root, ps_sfx)
    profiles = _files(root, prof_sfx)
    pset_names = {_name(p, ps_sfx) for p in psets}
    mute_names = {_name(p, mute_sfx) for p in mutes}

    profile_grants: dict[str, set[str]] = {}
    for prof in profiles:
        r = _parse(prof, findings)
        if r is not None:
            profile_grants[_name(prof, prof_sfx)] = _grants(r)

    for mute in mutes:
        r = _parse(mute, findings)
        if r is None:
            continue
        if not _any_true(r):
            findings.append(("HIGH", str(mute), "muting permission set enables nothing; in a muting set, true = muted"))
            continue
        muted = _grants(r)
        for prof_name, grants in profile_grants.items():
            overlap = sorted(muted & grants)
            if overlap:
                findings.append(("MEDIUM", str(mute),
                                 f"mutes {', '.join(overlap)} but profile '{prof_name}' also grants it; "
                                 "muting can't remove a profile grant"))

    for psg in psgs:
        r = _parse(psg, findings)
        if r is None:
            continue
        refs = [(_local(c.tag), (c.text or "").strip()) for c in r]
        muting_refs = [v for t, v in refs if t == "mutingPermissionSets"]
        if len(muting_refs) > 1:
            findings.append(("REVIEW", str(psg), f"{len(muting_refs)} muting permission sets listed; plan for one per group"))
        if psets:
            for ref in (v for t, v in refs if t == "permissionSets"):
                if ref not in pset_names:
                    findings.append(("REVIEW", str(psg), f"references permission set '{ref}' that is not in the tree; deploy it with the group"))
        for ref in muting_refs:
            if ref not in mute_names:
                findings.append(("REVIEW", str(psg), f"references muting set '{ref}' that is not in the tree; deploy it with the group"))

    if len(profiles) > 10 and not psgs:
        findings.append(("REVIEW", str(root), f"{len(profiles)} profiles and no permission set groups; access may still be profile-heavy"))

    scanned = len(psgs) + len(mutes) + len(psets) + len(profiles)
    score = max(0, 100 - sum(WEIGHTS.get(s, 0) for s, _, _ in findings))
    print(json.dumps({"score": score,
                      "findings": [{"severity": s, "location": l, "message": m} for s, l, m in findings],
                      "summary": f"Scanned {len(psgs)} PSG, {len(mutes)} muting, {len(psets)} permission set, "
                                 f"{len(profiles)} profile file(s); {len(findings)} finding(s)."}, indent=2))
    if scanned == 0:
        print("WARN: no profile, permission set, PSG, or muting metadata found", file=sys.stderr)
        return 0
    blocking = {"ERROR", "HIGH"} | ({"MEDIUM", "REVIEW"} if args.strict else set())
    return 1 if any(s in blocking for s, _, _ in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
