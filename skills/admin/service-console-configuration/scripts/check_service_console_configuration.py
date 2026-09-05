#!/usr/bin/env python3
"""Checker script for the service-console-configuration skill.

Static checks on retrieved / hand-authored Salesforce source for a Lightning
Service Console app. Every rule below is grounded in the Metadata API Developer
Guide (Summer '26 / v62,
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf):

  1. A CustomApplication with <navType>Console</navType> must carry a
     <workspaceConfig> with at least one <mappings> entry.
     "AppWorkspaceConfig.mappings ... Required for each tab specified in the
     CustomApplication" (api_meta L40025-40032); a tab with no mapping opens as
     a primary tab because "If not specified, tab opens as a primary tab"
     (L40044-40046). Tabs present in <tabs> but absent from <mappings> are
     reported.
  2. Every <mappings><fieldName> must name a field that exists on the mapped
     tab's own object, when that object's CustomObject metadata is in the
     manifest. fieldName is the lookup on the CHILD pointing at the parent
     (guide sample: standard-Contact keyed on AccountId, L40712-40724).
  3. <utilityBar> must name a FlexiPage present in the manifest whose <type> is
     UtilityBar ("A Lightning page used as the utility bar in Lightning
     Experience apps", L67084-67086).
  4. <tabLimitConfig> values must be in the documented enums:
     maxNumberOfPrimaryTabs in {5,10,20,30}, maxNumberOfSubTabs in {5,10,15}
     (L40382-40395).
  5. <listPlacement><location> must be one of full | top | left, with width
     required for left and height required for top, and units always required
     (L40245-40254).
  6. Every <profileActionOverrides><content> naming a Flexipage override must
     resolve to a FlexiPage in the manifest.

Reports a warning (not an error) when a Lightning app sets
<isServiceCloudConsole>true</isServiceCloudConsole>, which the guide reserves
for Salesforce Classic console apps (L39702-39706).

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_service_console_configuration.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://soap.sforce.com/2006/04/metadata"

PRIMARY_TAB_LIMITS = {"5", "10", "20", "30"}
SUBTAB_LIMITS = {"5", "10", "15"}
LIST_LOCATIONS = {"full", "top", "left"}

# Standard tabs whose backing object is the tab name minus the "standard-"
# prefix. Only used to map a tab to an object name; a tab we cannot resolve is
# skipped rather than guessed at.
STANDARD_TAB_PREFIX = "standard-"


def tag(name: str) -> str:
    return f"{{{NS}}}{name}"


def child(element, name):
    """Return the first child element with this tag, or None.

    Written as an explicit `is not None` test: a childless ElementTree Element
    is falsy, so `el.find(a) or el.find(b)` silently discards real leaf nodes.
    """
    found = element.find(tag(name))
    if found is not None:
        return found
    return None


def text_of(element, name, default=""):
    found = child(element, name)
    if found is None:
        return default
    if found.text is None:
        return default
    return found.text.strip()


def parse(path: Path):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        return exc


def api_name_from_path(path: Path, suffix: str) -> str:
    name = path.name
    if name.endswith(suffix):
        return name[: -len(suffix)]
    return path.stem


def collect_flexipages(root: Path) -> dict:
    """developer name -> FlexiPage <type> text (empty string if absent)."""
    pages = {}
    for path in root.rglob("*.flexipage-meta.xml"):
        element = parse(path)
        if isinstance(element, ET.ParseError) or element is None:
            continue
        pages[api_name_from_path(path, ".flexipage-meta.xml")] = text_of(element, "type")
    return pages


def collect_object_fields(root: Path) -> dict:
    """object API name -> set of field API names found in the manifest.

    Handles both decomposed source format (objects/Foo__c/fields/Bar__c.field-meta.xml)
    and a single .object-meta.xml carrying <fields> children.
    """
    fields: dict = {}
    for path in root.rglob("*.object-meta.xml"):
        obj = api_name_from_path(path, ".object-meta.xml")
        names = fields.setdefault(obj, set())
        element = parse(path)
        if isinstance(element, ET.ParseError) or element is None:
            continue
        for field_el in element.findall(tag("fields")):
            full = text_of(field_el, "fullName")
            if full:
                names.add(full)
    for path in root.rglob("*.field-meta.xml"):
        # .../objects/<Object>/fields/<Field>.field-meta.xml
        parts = path.parts
        if "fields" not in parts:
            continue
        idx = len(parts) - 1 - parts[::-1].index("fields")
        if idx == 0:
            continue
        obj = parts[idx - 1]
        fields.setdefault(obj, set()).add(api_name_from_path(path, ".field-meta.xml"))
    return fields


def object_for_tab(tab_name: str) -> str:
    """Best-effort object API name behind a <tabs> / <tab> value."""
    if tab_name.startswith(STANDARD_TAB_PREFIX):
        return tab_name[len(STANDARD_TAB_PREFIX):]
    return tab_name


def check_manifest(manifest_dir: Path) -> list:
    issues = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    flexipages = collect_flexipages(manifest_dir)
    object_fields = collect_object_fields(manifest_dir)

    app_paths = sorted(manifest_dir.rglob("*.app-meta.xml"))
    if not app_paths:
        return [
            f"No *.app-meta.xml files found under {manifest_dir}. "
            "CustomApplication components have the suffix .app and live in the "
            "applications folder (api_meta L39627-39628); point --manifest-dir at "
            "the source root that contains applications/."
        ]

    for app_path in app_paths:
        app = api_name_from_path(app_path, ".app-meta.xml")
        root = parse(app_path)
        if isinstance(root, ET.ParseError):
            issues.append(f"App '{app}': not well-formed XML - {root}")
            continue
        if root is None:
            continue

        nav_type = text_of(root, "navType")
        is_console = nav_type == "Console"

        if text_of(root, "isServiceCloudConsole").lower() == "true" and is_console:
            issues.append(
                f"App '{app}': sets isServiceCloudConsole=true alongside navType=Console. "
                "The guide reserves isServiceCloudConsole for Salesforce Classic console "
                "apps - 'For Lightning Experience console apps, this field is null and the "
                "navType field is set to Console' (api_meta L39702-39706)."
            )

        # --- Check 1: console app must have workspaceConfig mappings ---
        tabs = [t.text.strip() for t in root.findall(tag("tabs")) if t.text and t.text.strip()]
        workspace = child(root, "workspaceConfig")
        mappings = workspace.findall(tag("mappings")) if workspace is not None else []

        if is_console and not mappings:
            issues.append(
                f"Console app '{app}': no <workspaceConfig><mappings> entries. "
                "AppWorkspaceConfig.mappings is 'Required for each tab specified in the "
                "CustomApplication' (api_meta L40025-40032), and an unmapped tab opens as "
                "a primary tab because 'If not specified, tab opens as a primary tab' "
                "(L40044-40046). Every record click will open a new workspace tab."
            )

        mapped_tabs = []
        for mapping in mappings:
            mapped_tab = text_of(mapping, "tab")
            field_name = text_of(mapping, "fieldName")
            if not mapped_tab:
                issues.append(
                    f"App '{app}': a <mappings> entry has no <tab>. "
                    "WorkspaceMapping.tab is Required (api_meta L40047)."
                )
                continue
            mapped_tabs.append(mapped_tab)

            if mapped_tab not in tabs:
                issues.append(
                    f"App '{app}': mapping for tab '{mapped_tab}' has no matching <tabs> "
                    "entry in the same app. The mapping applies to nothing."
                )

            # --- Check 2: fieldName must exist on the mapped tab's object ---
            if not field_name:
                continue
            obj = object_for_tab(mapped_tab)
            known = object_fields.get(obj)
            if known is None:
                continue  # object not in this manifest - cannot verify, do not guess
            if field_name not in known:
                issues.append(
                    f"App '{app}': mapping <tab>{mapped_tab}</tab> uses "
                    f"<fieldName>{field_name}</fieldName>, but '{field_name}' is not a field "
                    f"on '{obj}' in this manifest. fieldName is the lookup on the SUBTAB's own "
                    "object pointing at the parent - the guide's sample keys standard-Contact "
                    "on Contact.AccountId (api_meta L40712-40724). A reversed mapping deploys "
                    "cleanly and never opens a subtab."
                )

        if is_console:
            unmapped = [t for t in tabs if t not in mapped_tabs]
            if unmapped and mappings:
                issues.append(
                    f"Console app '{app}': tabs with no workspaceConfig mapping - "
                    f"{', '.join(unmapped)}. Each will open as a primary tab by default "
                    "(api_meta L40044-40046). Add an explicit mapping even for tabs that "
                    "should be primary, so the choice is reviewable."
                )

        # --- Check 3: utilityBar must resolve to a UtilityBar FlexiPage ---
        utility_bar = text_of(root, "utilityBar")
        if utility_bar:
            if utility_bar not in flexipages:
                issues.append(
                    f"App '{app}': <utilityBar>{utility_bar}</utilityBar> names a FlexiPage "
                    "that is not in this manifest. Deploying the app without it leaves the "
                    "reference dangling; deploy the FlexiPage first."
                )
            elif flexipages[utility_bar] != "UtilityBar":
                issues.append(
                    f"App '{app}': <utilityBar>{utility_bar}</utilityBar> resolves to a "
                    f"FlexiPage of type '{flexipages[utility_bar] or '(none)'}', not "
                    "'UtilityBar' (api_meta L67084-67086)."
                )

        console_config = child(root, "consoleConfig")
        if console_config is not None:
            # --- Check 4: tabLimitConfig enums ---
            limits = child(console_config, "tabLimitConfig")
            if limits is not None:
                primary = text_of(limits, "maxNumberOfPrimaryTabs")
                subtabs = text_of(limits, "maxNumberOfSubTabs")
                if primary and primary not in PRIMARY_TAB_LIMITS:
                    issues.append(
                        f"App '{app}': maxNumberOfPrimaryTabs '{primary}' is not a valid "
                        f"value. Valid values are {sorted(PRIMARY_TAB_LIMITS, key=int)} "
                        "(api_meta L40382-40388)."
                    )
                if subtabs and subtabs not in SUBTAB_LIMITS:
                    issues.append(
                        f"App '{app}': maxNumberOfSubTabs '{subtabs}' is not a valid value. "
                        f"Valid values are {sorted(SUBTAB_LIMITS, key=int)} "
                        "(api_meta L40389-40395)."
                    )

            # --- Check 5: listPlacement ---
            placement = child(console_config, "listPlacement")
            if placement is not None:
                location = text_of(placement, "location")
                width = text_of(placement, "width")
                height = text_of(placement, "height")
                units = text_of(placement, "units")
                if location not in LIST_LOCATIONS:
                    issues.append(
                        f"App '{app}': listPlacement location '{location or '(missing)'}' is "
                        f"not valid. Valid values are {sorted(LIST_LOCATIONS)} "
                        "(api_meta L40247-40250); location is Required."
                    )
                if location == "left" and not width:
                    issues.append(
                        f"App '{app}': listPlacement location is 'left' but <width> is "
                        "missing. Width is 'Required if location is left' (api_meta L40254)."
                    )
                if location == "top" and not height:
                    issues.append(
                        f"App '{app}': listPlacement location is 'top' but <height> is "
                        "missing. Height is 'Required if location is top' (api_meta L40245)."
                    )
                if location in LIST_LOCATIONS and not units:
                    issues.append(
                        f"App '{app}': listPlacement has no <units>. Units is Required and "
                        "states whether height or width is px or % (api_meta L40252)."
                    )

        # --- Check 6: profileActionOverrides must resolve to real FlexiPages ---
        for override in root.findall(tag("profileActionOverrides")):
            override_type = text_of(override, "type").lower()
            content = text_of(override, "content")
            if override_type != "flexipage" or not content:
                continue
            if content not in flexipages:
                issues.append(
                    f"App '{app}': profileActionOverride <content>{content}</content> is a "
                    "Flexipage override naming a FlexiPage that is not in this manifest. "
                    "Note also that a Flexipage AppActionOverride set to App Default "
                    "can't be deleted via Metadata API (api_meta L39859-39861)."
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce source for Service Console configuration defects: missing or "
            "reversed workspaceConfig mappings, a utilityBar that does not resolve to a "
            "UtilityBar FlexiPage, out-of-enum tabLimitConfig / listPlacement values, and "
            "dangling Flexipage profile action overrides."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree, e.g. force-app/main/default (default: .).",
    )
    args = parser.parse_args()

    issues = check_manifest(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
