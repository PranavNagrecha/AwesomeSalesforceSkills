#!/usr/bin/env python3
"""Checker script for Lightning Experience Transition skill.

Scans force-app/ metadata for assets that block or complicate a Classic-to-Lightning
rollout and emits a triage report. Stdlib only — no pip dependencies.

Checks:
  1. JavaScript buttons (WebLink linkType=javascript) — always flag, never LEX-ready.
  2. S-controls — deprecated Classic asset; Lightning incompatible.
  3. Visualforce pages with a renderAs="pdf" or controller="..." attribute that
     suggests Classic-only rendering pathways the team should re-test in LEX.
  4. Custom Console apps (uiType="Aloha" inside CustomApplication.app-meta.xml).
  5. References to UserPreferencesLightningExperiencePreferred or
     "lightning_experience_user" license in Profile/PermissionSet metadata.
  6. AppExchange-installed package indicators in installedPackages/.

Usage:
    python3 check_lightning_experience_transition.py
    python3 check_lightning_experience_transition.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Triage Salesforce metadata for Lightning Experience Transition blockers.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def find_javascript_buttons(root: Path) -> list[str]:
    issues: list[str] = []
    for f in root.rglob("*.weblink-meta.xml"):
        text = _read(f)
        if "<linkType>javascript</linkType>" in text or "<linkType>onClickJavaScript</linkType>" in text:
            issues.append(
                f"BLOCKER: JavaScript button at {f.relative_to(root)} — JS buttons do not run in LEX. "
                f"Triage as Replace (Quick Action / flow / LWC) before any wave that uses this object."
            )
    return issues


def find_scontrols(root: Path) -> list[str]:
    issues: list[str] = []
    for f in root.rglob("*.scf-meta.xml"):
        issues.append(
            f"BLOCKER: S-Control at {f.relative_to(root)} — S-Controls are deprecated and not supported in LEX. "
            f"Retire or rebuild as LWC."
        )
    for f in root.rglob("*.scf"):
        if not f.with_suffix(".scf-meta.xml").exists():
            issues.append(
                f"BLOCKER: S-Control source at {f.relative_to(root)} — confirm asset is retired."
            )
    return issues


VF_RISKY_PATTERNS = [
    (re.compile(r"<apex:page[^>]*renderAs\s*=\s*\"pdf\"", re.IGNORECASE | re.DOTALL),
     "renderAs=pdf — verify pixel parity in LEX iframe and any Classic-only print chrome."),
    (re.compile(r"window\.parent\."),
     "uses window.parent — likely blocked by same-origin policy in LEX iframe; refactor to postMessage or LWC."),
    (re.compile(r"sforce\.connection\."),
     "uses sforce.connection — Classic-era client API; rewrite as Apex @AuraEnabled or REST."),
    (re.compile(r"location\.hash"),
     "manipulates location.hash — fragile inside LEX iframe; use Lightning navigation events."),
]


def find_visualforce_risks(root: Path) -> list[str]:
    issues: list[str] = []
    for f in root.rglob("*.page"):
        text = _read(f)
        for pattern, description in VF_RISKY_PATTERNS:
            if pattern.search(text):
                issues.append(
                    f"REVIEW: Visualforce page at {f.relative_to(root)} — {description}"
                )
    for f in root.rglob("*.component"):
        text = _read(f)
        if "window.parent" in text or "sforce.connection" in text:
            issues.append(
                f"REVIEW: Visualforce component at {f.relative_to(root)} — Classic-era JS API; revalidate in LEX."
            )
    return issues


def find_classic_console_apps(root: Path) -> list[str]:
    issues: list[str] = []
    for f in root.rglob("*.app-meta.xml"):
        text = _read(f)
        if "<uiType>Aloha</uiType>" in text:
            issues.append(
                f"REVIEW: Classic (Aloha) app at {f.relative_to(root)} — needs an explicit Lightning app counterpart. "
                f"If this is a Classic Service Console, schedule a Lightning Console rebuild."
            )
    return issues


def find_installed_packages(root: Path) -> list[str]:
    issues: list[str] = []
    pkg_dir = None
    for candidate in [root / "installedPackages", root / "main" / "default" / "installedPackages"]:
        if candidate.exists():
            pkg_dir = candidate
            break
    if pkg_dir is None:
        return issues
    pkgs = list(pkg_dir.glob("*.installedPackage-meta.xml"))
    if pkgs:
        issues.append(
            f"AUDIT: {len(pkgs)} managed package(s) installed (in {pkg_dir.relative_to(root)}). "
            f"Verify each is on a Lightning-Ready version and run a workflow walkthrough in a LEX sandbox "
            f"BEFORE the wave that touches the package's apps."
        )
    return issues


def find_lex_permission_signals(root: Path) -> list[str]:
    issues: list[str] = []
    found_lex_user_perm = False
    found_hide_classic_perm = False
    for f in list(root.rglob("*.permissionset-meta.xml")) + list(root.rglob("*.profile-meta.xml")):
        text = _read(f)
        if "LightningExperienceUser" in text:
            found_lex_user_perm = True
        if "LightningExperienceHidesClassicSwitcher" in text or "HidesClassicSwitcher" in text:
            found_hide_classic_perm = True
    if not found_lex_user_perm:
        issues.append(
            "INFO: No PermissionSet or Profile in scope grants the 'Lightning Experience User' permission. "
            "Permission-set-driven wave rollout requires an explicit grant — confirm one exists."
        )
    if not found_hide_classic_perm:
        issues.append(
            "INFO: No PermissionSet grants 'Hides Classic Switcher' (or equivalent). "
            "Cutover requires a switcher-removal mechanism to prevent users from sticky-preference-switching back."
        )
    return issues


def check_lightning_experience_transition(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    issues.extend(find_javascript_buttons(manifest_dir))
    issues.extend(find_scontrols(manifest_dir))
    issues.extend(find_visualforce_risks(manifest_dir))
    issues.extend(find_classic_console_apps(manifest_dir))
    issues.extend(find_installed_packages(manifest_dir))
    issues.extend(find_lex_permission_signals(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_lightning_experience_transition(manifest_dir)

    if not issues:
        print("No Lightning Experience Transition blockers detected.")
        return 0

    blockers = [i for i in issues if i.startswith("BLOCKER")]
    reviews = [i for i in issues if i.startswith("REVIEW")]
    audits = [i for i in issues if i.startswith("AUDIT")]
    infos = [i for i in issues if i.startswith("INFO")]

    print(f"Lightning Experience Transition triage — {manifest_dir}")
    print(f"  blockers: {len(blockers)}  review: {len(reviews)}  audit: {len(audits)}  info: {len(infos)}")
    print()
    for group_name, group in [("BLOCKERS", blockers), ("REVIEWS", reviews), ("AUDITS", audits), ("INFO", infos)]:
        if not group:
            continue
        print(f"--- {group_name} ---")
        for issue in group:
            print(f"  {issue}")
        print()

    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
