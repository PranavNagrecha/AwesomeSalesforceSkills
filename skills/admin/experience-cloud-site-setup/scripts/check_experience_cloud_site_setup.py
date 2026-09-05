#!/usr/bin/env python3
"""Checker script for the Experience Cloud Site Setup skill.

Inspects Salesforce DX source for the metadata this skill produces:

  networks/<Name>.network-meta.xml               Network
  sites/<Name>.site-meta.xml                     CustomSite
  navigationMenus/<Name>.navigationMenu-meta.xml NavigationMenu
  experiences/<Name>/                            ExperienceBundle folder
  digitalExperiences/site/<Name>/                DigitalExperienceBundle folder

Checks (grounded in the Metadata API Developer Guide, Summer '26 / v62 text):

  ERROR  Network status Live with selfRegistration true and no selfRegProfile
         (selfRegProfile "is used only if selfRegistration is enabled",
         api_meta.txt L91035-L91042)
  WARN   Network with zero networkMemberGroups entries (api_meta.txt L90963-L90966)
  WARN   Network missing emailSenderAddress / emailSenderName / forgotPasswordTemplate
         / site / status / tabs, all marked Required
         (api_meta.txt L90782, L90797, L90917, L91045, L91054, L91081)
  WARN   CustomSite declaring requireHttps, removed in API 52.0+ and ignored earlier
         (api_meta.txt L47015-L47017); also weak clickjackProtectionLevel
         (api_meta.txt L46876-L46888)
  WARN   NavigationMenu ExternalLink whose target is not https
  WARN   Network naming an ExperienceBundle site whose folder is absent from source
  WARN   Legacy LWC / Aura shape problems for Experience Builder

Exit status: 0 when nothing is reported, 1 when any issue is reported.

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_experience_cloud_site_setup.py --help
    python3 check_experience_cloud_site_setup.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "{http://soap.sforce.com/2006/04/metadata}"

# Network fields the Metadata API Developer Guide marks Required.
NETWORK_REQUIRED = (
    "emailSenderAddress",
    "emailSenderName",
    "forgotPasswordTemplate",
    "site",
    "status",
    "tabs",
)

# clickjackProtectionLevel values the guide annotates as weak.
WEAK_CLICKJACK = {
    "AllowAllFraming": "no protection",
    "External": "good protection, but weaker than SameOriginOnly (recommended)",
}


# ---------------------------------------------------------------------------
# XML helpers
#
# NEVER write `el.find(a) or el.find(b)` on ElementTree: an Element with no
# children is falsy, so a real leaf match is discarded. Everything below tests
# `is not None` explicitly.
# ---------------------------------------------------------------------------

def parse_xml(path: Path) -> tuple[ET.Element | None, str | None]:
    """Return (root, error). Exactly one of the two is None."""
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, f"XML parse error in {path}: {exc}"
    except OSError as exc:  # unreadable file
        return None, f"Cannot read {path}: {exc}"


def local_name(tag: str) -> str:
    return tag.split("}", 1)[1] if tag.startswith("{") else tag


def child_text(parent: ET.Element, name: str) -> str | None:
    """Text of the first direct child called `name`, namespace-tolerant."""
    for child in parent:
        if local_name(child.tag) == name:
            found = child.text
            if found is None:
                return ""
            return found.strip()
    return None


def children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in parent if local_name(c.tag) == name]


def has_value(parent: ET.Element, name: str) -> bool:
    """True when `name` is present and carries either text or child elements.

    Required fields on Network are a mix of scalars (emailSenderAddress) and
    containers (tabs). A container element has no text of its own, so testing
    child_text() alone would report a populated <tabs> block as missing.
    """
    for child in parent:
        if local_name(child.tag) != name:
            continue
        if len(child) > 0:
            return True
        if child.text is not None and child.text.strip():
            return True
    return False


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Check 1 + 2 + 3 + 6: the Network files
# ---------------------------------------------------------------------------

def check_networks(manifest_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for every networks/*.network-meta.xml."""
    errors: list[str] = []
    warnings: list[str] = []

    networks_dir = manifest_dir / "networks"
    if not networks_dir.is_dir():
        return errors, warnings

    experience_folders = experience_bundle_names(manifest_dir)

    for net_file in sorted(networks_dir.glob("*.network-meta.xml")):
        root, err = parse_xml(net_file)
        if root is None:
            errors.append(err or f"Unparseable Network: {net_file}")
            continue

        where = rel(net_file, manifest_dir)
        name = net_file.name.split(".")[0]

        status = child_text(root, "status")
        self_reg = (child_text(root, "selfRegistration") or "").lower()
        self_reg_profile = child_text(root, "selfRegProfile")

        # ERROR: live site advertising self-registration with nowhere to put registrants.
        if status == "Live" and self_reg == "true" and not self_reg_profile:
            errors.append(
                f"{where}: status is Live and selfRegistration is true, but no "
                f"<selfRegProfile> is set. selfRegProfile is the profile assigned to "
                f"self-registering users and 'is used only if selfRegistration is "
                f"enabled for the site' (Metadata API Guide, Network, "
                f"api_meta.txt L91035-L91042). Set the profile or turn "
                f"selfRegistration off before publishing."
            )
        elif self_reg == "true" and not self_reg_profile:
            warnings.append(
                f"{where}: selfRegistration is true with no <selfRegProfile>. The site "
                f"is not Live yet, so this is not blocking, but it must be resolved "
                f"before status moves to Live."
            )

        # WARN: no members.
        member_groups = children(root, "networkMemberGroups")
        group_entries = 0
        for group in member_groups:
            group_entries += len(children(group, "profile"))
            group_entries += len(children(group, "permissionSet"))
        if group_entries == 0:
            warnings.append(
                f"{where}: no <networkMemberGroups> profile or permissionSet entries. "
                f"'Users with these profiles or permission sets are members of the "
                f"site' (api_meta.txt L90963-L90966) - with none listed the site has "
                f"no members beyond users holding Create and Set Up Experiences."
            )

        # WARN: Required fields absent.
        for field in NETWORK_REQUIRED:
            if not has_value(root, field):
                warnings.append(
                    f"{where}: missing required <{field}>. The Metadata API Developer "
                    f"Guide marks it Required on Network; the deploy will reject the "
                    f"file."
                )

        # WARN: named ExperienceBundle folder is not in source.
        if experience_folders is not None:
            expected = f"{name}1"
            if expected not in experience_folders and name not in experience_folders:
                warnings.append(
                    f"{where}: Network '{name}' has no matching Experience Builder "
                    f"content folder in source (looked for experiences/{expected} and "
                    f"experiences/{name}). Site settings will deploy without the pages, "
                    f"routes, themes and branding sets. Creating a Lightning site makes "
                    f"two records, <site_name> and <site_name>1 "
                    f"(api_meta.txt L130582-L130585)."
                )

    return errors, warnings


def experience_bundle_names(manifest_dir: Path) -> set[str] | None:
    """Folder names under experiences/, or None when the project has no such tree.

    Returning None (rather than an empty set) keeps the check quiet for projects
    that carry only Network settings and manage site content elsewhere.
    """
    experiences_dir = manifest_dir / "experiences"
    if not experiences_dir.is_dir():
        return None
    return {d.name for d in experiences_dir.iterdir() if d.is_dir()}


# ---------------------------------------------------------------------------
# Check 4: the CustomSite files
# ---------------------------------------------------------------------------

def check_custom_sites(manifest_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    sites_dir = manifest_dir / "sites"
    if not sites_dir.is_dir():
        return errors, warnings

    for site_file in sorted(sites_dir.glob("*.site-meta.xml")):
        root, err = parse_xml(site_file)
        if root is None:
            errors.append(err or f"Unparseable CustomSite: {site_file}")
            continue
        if local_name(root.tag) != "CustomSite":
            continue  # SiteDotCom shares the .site-meta.xml suffix

        where = rel(site_file, manifest_dir)

        require_https = child_text(root, "requireHttps")
        if require_https is not None:
            warnings.append(
                f"{where}: declares <requireHttps>{require_https}</requireHttps>. That "
                f"field 'is removed in API version 52.0 and later' and in 51.0 and "
                f"earlier 'the value in the field is ignored' "
                f"(api_meta.txt L47015-L47017). It buys no HTTPS enforcement at any "
                f"API version - remove it and use <redirectToCustomDomain> "
                f"(api_meta.txt L46982-L46989), which defaults to false in Experience "
                f"Cloud sites."
            )

        clickjack = child_text(root, "clickjackProtectionLevel")
        if clickjack is None:
            warnings.append(
                f"{where}: no <clickjackProtectionLevel>. The guide marks it Required "
                f"and annotates SameOriginOnly as '(recommended)' "
                f"(api_meta.txt L46876-L46888)."
            )
        elif clickjack in WEAK_CLICKJACK:
            warnings.append(
                f"{where}: clickjackProtectionLevel is {clickjack} - the guide "
                f"annotates this as {WEAK_CLICKJACK[clickjack]} "
                f"(api_meta.txt L46876-L46888). SameOriginOnly is the recommended "
                f"value unless an external domain must frame the site."
            )

        site_type = child_text(root, "siteType")
        if site_type is not None and site_type not in ("ChatterNetwork", "ChatterNetworkPicasso"):
            warnings.append(
                f"{where}: siteType is '{site_type}'. An Experience Cloud site's "
                f"CustomSite is ChatterNetwork and its paired SiteDotCom is "
                f"ChatterNetworkPicasso (api_meta.txt L130582-L130585); Siteforce is a "
                f"Site.com site (api_meta.txt L130607-L130609)."
            )

        for read_only in ("guestProfile", "subdomain"):
            if child_text(root, read_only) is not None:
                warnings.append(
                    f"{where}: declares <{read_only}>, which the guide marks Read only "
                    f"(api_meta.txt L46959, L47059). Source and org will diverge "
                    f"silently - remove it from version control."
                )

    return errors, warnings


# ---------------------------------------------------------------------------
# Check 5: NavigationMenu external links
# ---------------------------------------------------------------------------

def check_navigation_menus(manifest_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    menus_dir = manifest_dir / "navigationMenus"
    if not menus_dir.is_dir():
        return errors, warnings

    valid_types = {
        "SalesforceObject",
        "ExternalLink",
        "InternalLink",
        "MenuLabel",
        "NavigationalTopic",
    }
    valid_target_prefs = {"None", "OpenInExternalTab"}

    for menu_file in sorted(menus_dir.glob("*.navigationMenu-meta.xml")):
        root, err = parse_xml(menu_file)
        if root is None:
            errors.append(err or f"Unparseable NavigationMenu: {menu_file}")
            continue

        where = rel(menu_file, manifest_dir)

        for item in walk_menu_items(root):
            label = child_text(item, "label") or "(unlabelled)"
            item_type = child_text(item, "type")
            target = child_text(item, "target")
            target_pref = child_text(item, "targetPreference")

            if item_type is not None and item_type not in valid_types:
                warnings.append(
                    f"{where}: menu item '{label}' has type '{item_type}'. Valid values "
                    f"are {', '.join(sorted(valid_types))} "
                    f"(api_meta.txt L90546-L90564)."
                )

            if item_type == "ExternalLink" and target:
                if not target.lower().startswith("https://"):
                    warnings.append(
                        f"{where}: ExternalLink menu item '{label}' targets "
                        f"'{target}', which is not https. A plain-http destination "
                        f"linked from an HTTPS Experience Cloud page produces a mixed "
                        f"or downgraded navigation for every member who clicks it."
                    )

            if target_pref is not None and target_pref not in valid_target_prefs:
                warnings.append(
                    f"{where}: menu item '{label}' has targetPreference "
                    f"'{target_pref}'. The field table lists only None and "
                    f"OpenInExternalTab (api_meta.txt L90528-L90543); the guide's own "
                    f"sample uses an unlisted value at api_meta.txt L90627."
                )

            if item_type in ("ExternalLink", "InternalLink", "SalesforceObject") and not target:
                warnings.append(
                    f"{where}: menu item '{label}' is type {item_type} with no "
                    f"<target>. target is required for these three types "
                    f"(api_meta.txt L90515-L90527)."
                )

    return errors, warnings


def walk_menu_items(node: ET.Element) -> list[ET.Element]:
    """Every navigationMenuItem in the tree, including items nested in subMenu."""
    found: list[ET.Element] = []
    for child in node:
        if local_name(child.tag) == "navigationMenuItem":
            found.append(child)
            found.extend(walk_menu_items(child))
        elif local_name(child.tag) == "subMenu":
            found.extend(walk_menu_items(child))
    return found


# ---------------------------------------------------------------------------
# Legacy checks retained from the previous revision
# ---------------------------------------------------------------------------

def check_lwc_experience_targets(manifest_dir: Path) -> list[str]:
    """Warn when an exposed LWC lacks an Experience Cloud target.

    UNVERIFIED (2026-09-04): the Metadata API Developer Guide documents the
    targets/target element shape on LightningComponentBundle (api_meta.txt
    L84053-L84054, sample at L84157-L84163) but does not enumerate the valid
    target values, so the two strings matched below are not confirmed against
    that source. The lightningCommunity__ prefix is confirmed
    (lightningCommunity__Theme_Layout at api_meta.txt L53016-L53018,
    lightningCommunity__RelaxedCSP at L84064); these two exact spellings are
    not. If this check reports a false positive, verify the target names in the
    LWC Developer Guide's XML Configuration File Elements page before widening
    the set - this is the only check here resting on unverified strings.
    """
    issues: list[str] = []
    lwc_dir = manifest_dir / "lwc"
    if not lwc_dir.is_dir():
        return issues

    experience_targets = {"lightningCommunity__Page", "lightningCommunity__Default"}

    for meta_file in sorted(lwc_dir.rglob("*.js-meta.xml")):
        root, err = parse_xml(meta_file)
        if root is None:
            issues.append(err or f"Unparseable LWC metadata: {meta_file}")
            continue

        exposed = child_text(root, "isExposed")
        if exposed is None or exposed.lower() != "true":
            continue

        declared = {
            (el.text or "").strip()
            for el in root.iter()
            if local_name(el.tag) == "target"
        }
        if not (declared & experience_targets):
            issues.append(
                f"LWC '{meta_file.parent.name}' is exposed but declares no Experience "
                f"Cloud target (lightningCommunity__Page or "
                f"lightningCommunity__Default). It will not appear in Experience "
                f"Builder. File: {rel(meta_file, manifest_dir)}"
            )

    return issues


def check_aura_components_present(manifest_dir: Path) -> list[str]:
    """Warn when Aura components sit alongside an LWR-type ExperienceBundle."""
    issues: list[str] = []
    aura_dir = manifest_dir / "aura"
    experience_dir = manifest_dir / "experiences"

    if not aura_dir.is_dir() or not experience_dir.is_dir():
        return issues

    aura_components = [d for d in sorted(aura_dir.iterdir()) if d.is_dir()]
    if not aura_components:
        return issues

    lwr_sites: list[str] = []
    for config_file in sorted(experience_dir.rglob("*.json")):
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        site_type = str(data.get("type", ""))
        if "LWR" in site_type.upper():
            lwr_sites.append(str(data.get("label", config_file.parent.name)))

    if lwr_sites:
        names = [c.name for c in aura_components[:5]]
        extra = f" (and {len(aura_components) - 5} more)" if len(aura_components) > 5 else ""
        issues.append(
            f"Aura components found ({', '.join(names)}{extra}) alongside LWR site(s) "
            f"({', '.join(sorted(set(lwr_sites)))}). Aura components are not offered in "
            f"Experience Builder for LWR sites. Migrate to LWC or reconsider the "
            f"template."
        )

    return issues


def check_hardcoded_colors_in_lwc_css(manifest_dir: Path) -> list[str]:
    """Warn when LWC CSS hardcodes colours instead of consuming --dxp-* tokens."""
    issues: list[str] = []
    lwc_dir = manifest_dir / "lwc"
    if not lwc_dir.is_dir():
        return issues

    hex_pattern = re.compile(r":\s*#[0-9a-fA-F]{3,8}\b")

    for css_file in sorted(lwc_dir.rglob("*.css")):
        try:
            content = css_file.read_text(encoding="utf-8")
        except OSError:
            continue
        matches = hex_pattern.findall(content)
        if matches and "--dxp-" not in content:
            issues.append(
                f"LWC CSS '{rel(css_file, manifest_dir)}' uses {len(matches)} hardcoded "
                f"colour value(s) and no --dxp-* tokens. Branding-set changes in "
                f"Experience Builder will not reach this component."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud site setup metadata: Network, CustomSite, "
            "NavigationMenu, the Experience Builder content bundle, and the LWC "
            "shape that Experience Builder requires."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce DX source, e.g. force-app/main/default (default: .)",
    )
    return parser.parse_args()


def run_checks(manifest_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not manifest_dir.is_dir():
        errors.append(f"Manifest directory not found: {manifest_dir}")
        return errors, warnings

    for fn in (check_networks, check_custom_sites, check_navigation_menus):
        errs, warns = fn(manifest_dir)
        errors.extend(errs)
        warnings.extend(warns)

    warnings.extend(check_lwc_experience_targets(manifest_dir))
    warnings.extend(check_aura_components_present(manifest_dir))
    warnings.extend(check_hardcoded_colors_in_lwc_css(manifest_dir))

    return errors, warnings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    errors, warnings = run_checks(manifest_dir)

    for issue in errors:
        print(f"ERROR: {issue}", file=sys.stderr)
    for issue in warnings:
        print(f"WARN: {issue}", file=sys.stderr)

    if not errors and not warnings:
        print("No issues found.")
        return 0

    print(
        f"{len(errors)} error(s), {len(warnings)} warning(s).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
