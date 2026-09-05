#!/usr/bin/env python3
"""Static checks for Lightning app, tab, and utility-bar metadata.

Reads a Salesforce metadata source tree (sfdx source format or MDAPI format) and
reports structural problems in `CustomApplication`, `CustomTab`, and utility-bar
`FlexiPage` files before they are deployed. Nothing here contacts an org.

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_app_and_tab_configuration.py --manifest-dir force-app/main/default

Checks performed
----------------
ERROR  APP-DUP-TAB     The same tab appears twice in one app's <tabs> list.
ERROR  APP-UITYPE      navType/uiType/isServiceCloudConsole contradict each other
                       (for example uiType Aloha on an app that declares navType,
                       or a Lightning console app that also sets
                       isServiceCloudConsole).
WARN   APP-TAB-MISSING An app references a tab that is neither a standard tab
                       (standard- prefix) nor present as a CustomTab in the tree.
WARN   APP-NO-WSCONFIG navType is Console but the app has no <workspaceConfig>,
                       or a mapped tab has no <mappings> entry.
WARN   APP-UTILBAR     The app names a <utilityBar> FlexiPage that is not in the
                       tree, or the named FlexiPage is not of type UtilityBar.
INFO   APP-NO-LANDING  The app sets no <defaultLandingTab>.

Exit status
-----------
1 when any ERROR or WARN finding exists, 0 otherwise. INFO notes never fail the
run; they are printed so a reviewer sees them.

Grounding: Metadata API Developer Guide (v62) -- CustomApplication `tabs`,
`navType`, `uiType`, `isServiceCloudConsole`, `defaultLandingTab`, `utilityBar`,
`workspaceConfig`/`mappings`; CustomTab file suffix; FlexiPage `type` UtilityBar.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"

# Findings at these levels make the run fail.
FAILING_LEVELS = (ERROR, WARN)


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


class Finding:
    """One reported problem, with the level that decides the exit status."""

    def __init__(self, level: str, code: str, subject: str, message: str) -> None:
        self.level = level
        self.code = code
        self.subject = subject
        self.message = message

    def __str__(self) -> str:
        return f"{self.level} {self.code} [{self.subject}] {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Lightning app, tab, and utility-bar metadata for "
            "structural problems before deployment."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root of the Salesforce metadata source (sfdx source format or mdapi "
            "format). Default: current directory."
        ),
    )
    return parser.parse_args()


def find_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    """Return every file under *root* whose name ends with one of *suffixes*."""
    found: list[Path] = []
    for suffix in suffixes:
        found.extend(sorted(root.rglob(f"*{suffix}")))
    # rglob patterns can overlap (".tab-meta.xml" also matches "*.xml" style
    # suffixes if a caller passes both), so de-duplicate while keeping order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in found:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def component_name(path: Path, suffixes: tuple[str, ...]) -> str:
    """Strip the metadata suffix off a file name to get the component API name."""
    name = path.name
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def child(element: ET.Element, tag: str) -> ET.Element | None:
    """Return the first child named *tag*, or None.

    Written as an explicit `is not None` test on purpose: a leaf ``Element`` with
    no children is falsy, so ``element.find(a) or element.find(b)`` silently
    discards real elements.
    """
    found = element.find(_tag(tag))
    if found is not None:
        return found
    return None


def text_of(element: ET.Element, tag: str) -> str:
    """Return the stripped text of the first child named *tag*, or ""."""
    found = child(element, tag)
    if found is None:
        return ""
    if found.text is None:
        return ""
    return found.text.strip()


def texts_of(element: ET.Element, tag: str) -> list[str]:
    """Return the stripped text of every child named *tag*, skipping empties."""
    values: list[str] = []
    for found in element.findall(_tag(tag)):
        if found.text is not None and found.text.strip():
            values.append(found.text.strip())
    return values


def load_root(path: Path, findings: list[Finding]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(Finding(ERROR, "XML-PARSE", path.name, f"XML parse error: {exc}"))
        return None


APP_SUFFIXES = (".app-meta.xml", ".app")
TAB_SUFFIXES = (".tab-meta.xml", ".tab")
FLEXI_SUFFIXES = (".flexipage-meta.xml", ".flexipage")


def collect_tabs(root: Path) -> set[str]:
    """Every CustomTab API name present in the tree."""
    names: set[str] = set()
    for path in find_files(root, TAB_SUFFIXES):
        names.add(component_name(path, TAB_SUFFIXES))
    return names


def collect_flexipages(root: Path, findings: list[Finding]) -> dict[str, str]:
    """Map every FlexiPage API name in the tree to its declared ``type``."""
    pages: dict[str, str] = {}
    for path in find_files(root, FLEXI_SUFFIXES):
        name = component_name(path, FLEXI_SUFFIXES)
        element = load_root(path, findings)
        pages[name] = "" if element is None else text_of(element, "type")
    return pages


def check_duplicate_tabs(app: str, tabs: list[str], findings: list[Finding]) -> None:
    seen: set[str] = set()
    reported: set[str] = set()
    for tab in tabs:
        if tab in seen and tab not in reported:
            findings.append(
                Finding(
                    ERROR,
                    "APP-DUP-TAB",
                    app,
                    f"Tab '{tab}' is listed more than once in <tabs>. A duplicate "
                    "navigation item is not a second item; remove the extra element.",
                )
            )
            reported.add(tab)
        seen.add(tab)


def check_ui_type(app: str, element: ET.Element, findings: list[Finding]) -> None:
    nav_type = text_of(element, "navType")
    ui_type = text_of(element, "uiType")
    classic_console = text_of(element, "isServiceCloudConsole").lower()

    if nav_type and ui_type == "Aloha":
        findings.append(
            Finding(
                ERROR,
                "APP-UITYPE",
                app,
                f"uiType is Aloha (Salesforce Classic) but navType is '{nav_type}'. "
                "navType describes Lightning navigation only; an Aloha app must not "
                "declare it. Both fields are documented Not updateable, so this cannot "
                "be corrected by redeploying over the live app.",
            )
        )

    if ui_type == "Lightning" and classic_console == "true":
        findings.append(
            Finding(
                ERROR,
                "APP-UITYPE",
                app,
                "uiType is Lightning but isServiceCloudConsole is true. For a Lightning "
                "console app that field is null and navType is Console instead.",
            )
        )

    if ui_type and ui_type not in ("Lightning", "Aloha"):
        findings.append(
            Finding(
                ERROR,
                "APP-UITYPE",
                app,
                f"uiType '{ui_type}' is not a valid value. Use Lightning or Aloha.",
            )
        )

    if nav_type and nav_type not in ("Standard", "Console"):
        findings.append(
            Finding(
                ERROR,
                "APP-UITYPE",
                app,
                f"navType '{nav_type}' is not a valid value. Use Standard or Console.",
            )
        )


def check_tab_references(
    app: str, tabs: list[str], known_tabs: set[str], findings: list[Finding]
) -> None:
    reported: set[str] = set()
    for tab in tabs:
        if tab in reported:
            continue
        reported.add(tab)
        if tab.startswith("standard-") or tab.startswith("standard__"):
            continue
        if "__" in tab and not tab.endswith("__c") and not tab.endswith("__x"):
            # Namespaced tab from an installed package; not expected in this tree.
            continue
        if tab in known_tabs:
            continue
        findings.append(
            Finding(
                WARN,
                "APP-TAB-MISSING",
                app,
                f"Tab '{tab}' is referenced by the app but no CustomTab file for it is "
                "in this tree, and it carries no 'standard-' prefix. Either include the "
                "tab in the deployment or fix the name -- built-in tabs need the "
                "'standard-' prefix and a wrong name deploys clean and drops the item.",
            )
        )


def check_workspace_config(
    app: str, element: ET.Element, tabs: list[str], findings: list[Finding]
) -> None:
    nav_type = text_of(element, "navType")
    if nav_type != "Console":
        return

    workspace = child(element, "workspaceConfig")
    if workspace is None:
        findings.append(
            Finding(
                WARN,
                "APP-NO-WSCONFIG",
                app,
                "navType is Console but the app declares no <workspaceConfig>. A "
                "mapping is required for each tab in a console app; without one, how a "
                "record opens is undefined.",
            )
        )
        return

    mapped: list[str] = []
    for mapping in workspace.findall(_tag("mappings")):
        tab_name = text_of(mapping, "tab")
        if tab_name:
            mapped.append(tab_name)

    seen: set[str] = set()
    for tab in tabs:
        if tab in seen:
            continue
        seen.add(tab)
        if tab not in mapped:
            findings.append(
                Finding(
                    WARN,
                    "APP-NO-WSCONFIG",
                    app,
                    f"Console tab '{tab}' has no <mappings> entry in <workspaceConfig>. "
                    "Add one, and decide deliberately whether it carries a <fieldName> "
                    "(subtab of that lookup) or omits it (its own workspace tab).",
                )
            )


def check_utility_bar(
    app: str, element: ET.Element, flexipages: dict[str, str], findings: list[Finding]
) -> None:
    utility_bar = text_of(element, "utilityBar")
    if not utility_bar:
        return

    if utility_bar not in flexipages:
        findings.append(
            Finding(
                WARN,
                "APP-UTILBAR",
                app,
                f"The app references utility bar '{utility_bar}' but no FlexiPage by "
                "that name is in this tree. The app's <utilityBar> is a reference, not a "
                "definition -- the FlexiPage must already exist in the org or ship "
                "earlier in the same deployment.",
            )
        )
        return

    declared_type = flexipages[utility_bar]
    if declared_type != "UtilityBar":
        findings.append(
            Finding(
                WARN,
                "APP-UTILBAR",
                app,
                f"FlexiPage '{utility_bar}' is referenced as a utility bar but its "
                f"<type> is '{declared_type or 'missing'}', not UtilityBar.",
            )
        )


def check_landing_tab(app: str, element: ET.Element, findings: list[Finding]) -> None:
    if not text_of(element, "defaultLandingTab"):
        findings.append(
            Finding(
                INFO,
                "APP-NO-LANDING",
                app,
                "No <defaultLandingTab>. The landing page is then whatever the platform "
                "picks rather than a reviewed decision. Standard tabs need the "
                "'standard-' prefix here too (for example standard-home).",
            )
        )


def check_tree(manifest_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    known_tabs = collect_tabs(manifest_dir)
    flexipages = collect_flexipages(manifest_dir, findings)

    for path in find_files(manifest_dir, APP_SUFFIXES):
        element = load_root(path, findings)
        if element is None:
            continue

        app = component_name(path, APP_SUFFIXES)
        tabs = texts_of(element, "tabs")

        check_duplicate_tabs(app, tabs, findings)
        check_ui_type(app, element, findings)
        check_tab_references(app, tabs, known_tabs, findings)
        check_workspace_config(app, element, tabs, findings)
        check_utility_bar(app, element, flexipages, findings)
        check_landing_tab(app, element, findings)

    return findings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}")
        return 1

    findings = check_tree(manifest_dir)

    for level in (ERROR, WARN, INFO):
        for finding in findings:
            if finding.level == level:
                print(finding)

    failing = [f for f in findings if f.level in FAILING_LEVELS]
    notes = [f for f in findings if f.level == INFO]

    if not findings:
        print("OK: no Lightning app, tab, or utility-bar issues detected.")
        return 0

    print(
        f"\n{len(failing)} finding(s) at ERROR/WARN, {len(notes)} INFO note(s)."
    )
    if failing:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        sys.exit(1)
    sys.exit(0)
