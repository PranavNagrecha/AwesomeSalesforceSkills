#!/usr/bin/env python3
"""Checker for Salesforce In-App Guidance (`Prompt`) metadata.

Reads `prompts/<Name>.prompt-meta.xml` files under --manifest-dir and reports
misconfigurations that the platform will either reject at deploy time or
accept and then behave unexpectedly at run time.

Every rule below is grounded in the Metadata API Developer Guide (v62 PDF,
`Prompt` / `PromptVersion` pp. 1801-1810):
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

  ERROR  published version with no targetPageType   -- targetPageType is Required
  ERROR  endDate earlier than startDate             -- the window never opens
  ERROR  stepNumber repeated or skipped             -- "Numbers must be consecutive
                                                       without repeated or skipped numbers"
  ERROR  more than 10 steps                         -- "Include up to 10 steps"
  ERROR  timesToDisplay above 30                    -- "Maximum value of 30"
  ERROR  both a video and an image                  -- videoLink XOR image; image XOR imageLink
  WARN   walkthrough with fewer than 2 steps        -- a stepNumber on a single version
  WARN   timesToDisplay of 0                        -- the guidance never displays
  WARN   versionNumber other than 1                 -- "The number remains 1"
  WARN   field longer than its documented maximum
  WARN   image element without imageAltText/imageLocation
  INFO   no uiFormulaRule and userAccess/userProfileAccess not restricted
         -- "If this field is null, the in-app guidance displays by default"

Exits 1 if any ERROR was reported, 0 otherwise. --strict also fails on WARN.
Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_in_app_guidance_and_walkthroughs.py --manifest-dir force-app/main/default
    python3 check_in_app_guidance_and_walkthroughs.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# --- Grounded constants (api_meta.txt line ranges in comments) ---------------
MAX_STEPS = 10  # stepNumber, L99190-99196
RECOMMENDED_MAX_STEPS = 5  # Salesforce adoption guidance
MAX_TIMES_TO_DISPLAY = 30  # timesToDisplay, L99276-99294
EXPECTED_VERSION_NUMBER = 1  # versionNumber, L99326-99329

# Field -> documented maximum length.
MAX_LENGTHS = {
    "title": 36,  # L99295-99298
    "header": 36,  # L99069-99084
    "actionButtonLabel": 25,  # L98962-98966
    "actionButtonLink": 1000,  # L98968-98984
    "dismissButtonLabel": 15,  # L99012-99015
    "description": 255,  # L99007-99010
    "videoLink": 1000,  # L99340-99347
}
MASTER_LABEL_MAX = 80  # Prompt.masterLabel, L98945-98948

VALID_DISPLAY_TYPES = {"DockedComposer", "FloatingPanel", "Targeted"}  # L99037-99044
VALID_USER_ACCESS = {"Everyone", "SpecificPermissions"}  # L99308-99316
VALID_USER_PROFILE_ACCESS = {"Everyone", "SpecificProfiles"}  # L99317-99325
VALID_OPERATORS = {"EQUAL"}  # L99394-99399


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check In-App Guidance (Prompt) metadata for misconfigurations. "
            "Point --manifest-dir at the root of a Salesforce metadata "
            "deployment (e.g. force-app/main/default or an SFDX project root)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN as well as ERROR.",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    """Return an element tag with any XML namespace stripped."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def child_text(element: ET.Element, name: str) -> str | None:
    """Return the text of the first direct child named `name`, or None.

    Deliberately does NOT use `element.find(a) or element.find(b)`: a leaf
    ElementTree Element is falsy, so `or` silently discards real matches.
    Every result is tested with `is not None`.
    """
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return None


def child_elements(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in element if local_name(c.tag) == name]


def has_child(element: ET.Element, name: str) -> bool:
    return child_text(element, name) not in (None, "")


def as_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def find_prompt_files(manifest_dir: Path) -> list[Path]:
    """Find every Prompt source file under manifest_dir, DX or MDAPI."""
    seen: dict[Path, None] = {}
    for pattern in ("*.prompt-meta.xml", "*.prompt"):
        for path in sorted(manifest_dir.rglob(pattern)):
            if path.is_file():
                seen.setdefault(path.resolve(), None)
    return list(seen.keys())


# --- Individual checks -------------------------------------------------------


def check_root(name: str, root: ET.Element) -> list[str]:
    issues: list[str] = []
    if local_name(root.tag) != "Prompt":
        issues.append(
            f"ERROR: {name}: root element is <{local_name(root.tag)}>, expected <Prompt>."
        )
    master = child_text(root, "masterLabel")
    if not master:
        issues.append(f"ERROR: {name}: <Prompt> has no <masterLabel> (Required).")
    elif len(master) > MASTER_LABEL_MAX:
        issues.append(
            f"WARN: {name}: Prompt masterLabel is {len(master)} characters — "
            f"documented maximum is {MASTER_LABEL_MAX}."
        )
    if not child_elements(root, "promptVersions"):
        issues.append(f"ERROR: {name}: no <promptVersions> entries — nothing will deploy.")
    return issues


def check_version(
    name: str, index: int, version: ET.Element, check_audience: bool = True
) -> list[str]:
    """Check one <promptVersions> entry.

    `check_audience` is False for walkthrough steps after the first: the
    audience gate is read from the first step, so a bare step 2 is normal.
    """
    issues: list[str] = []
    step = as_int(child_text(version, "stepNumber"))
    where = f"{name} [step {step}]" if step is not None else f"{name} [version {index}]"

    published = (child_text(version, "isPublished") or "").lower() == "true"

    # Required fields (L99206-99210, L99244-99248, L98986-98998, L99295-99298).
    if published and not has_child(version, "targetPageType"):
        issues.append(
            f"ERROR: {where}: isPublished is true but <targetPageType> is missing. "
            f"It is a required field; retrieve a Setup-built prompt for this page "
            f"to obtain the value."
        )
    if published and not has_child(version, "targetPageKey1"):
        issues.append(
            f"ERROR: {where}: isPublished is true but <targetPageKey1> is missing (Required)."
        )
    for required in ("body", "title", "displayType", "masterLabel", "versionNumber"):
        if not has_child(version, required):
            issues.append(f"ERROR: {where}: <{required}> is missing (Required).")

    # Enums.
    display_type = child_text(version, "displayType")
    if display_type and display_type not in VALID_DISPLAY_TYPES:
        issues.append(
            f"ERROR: {where}: displayType '{display_type}' is not valid — "
            f"expected one of {sorted(VALID_DISPLAY_TYPES)}."
        )
    user_access = child_text(version, "userAccess")
    if user_access and user_access not in VALID_USER_ACCESS:
        issues.append(
            f"ERROR: {where}: userAccess '{user_access}' is not valid — "
            f"expected one of {sorted(VALID_USER_ACCESS)}."
        )
    profile_access = child_text(version, "userProfileAccess")
    if profile_access and profile_access not in VALID_USER_PROFILE_ACCESS:
        issues.append(
            f"ERROR: {where}: userProfileAccess '{profile_access}' is not valid — "
            f"expected one of {sorted(VALID_USER_PROFILE_ACCESS)}."
        )

    # Scheduling window.
    start = child_text(version, "startDate")
    end = child_text(version, "endDate")
    if start and end and end < start:
        # ISO dates sort lexicographically, so a string compare is exact here.
        issues.append(
            f"ERROR: {where}: endDate {end} is earlier than startDate {start} — "
            f"the display window never opens."
        )

    times = as_int(child_text(version, "timesToDisplay"))
    if times is not None:
        if times > MAX_TIMES_TO_DISPLAY:
            issues.append(
                f"ERROR: {where}: timesToDisplay is {times} — documented maximum is "
                f"{MAX_TIMES_TO_DISPLAY}."
            )
        elif times == 0:
            issues.append(
                f"WARN: {where}: timesToDisplay is 0 — the guidance will never be shown. "
                f"Use 1 for 'once per user', or omit the field."
            )

    version_number = as_int(child_text(version, "versionNumber"))
    if version_number is not None and version_number != EXPECTED_VERSION_NUMBER:
        issues.append(
            f"WARN: {where}: versionNumber is {version_number}. The guide states it "
            f"remains 1 because multiple versions aren't saved in the org — "
            f"stepNumber is the field that increments."
        )

    # Media exclusivity (L99086-99090, L99098-99102, L99340-99347).
    has_video = has_child(version, "videoLink") or has_child(version, "videolink")
    has_image = has_child(version, "image")
    has_image_link = has_child(version, "imageLink")
    if has_video and (has_image or has_image_link):
        issues.append(
            f"ERROR: {where}: both a video and an image are set. videoLink and image "
            f"are mutually exclusive."
        )
    if has_image and has_image_link:
        issues.append(
            f"ERROR: {where}: both <image> and <imageLink> are set — specify one, not both."
        )
    if has_child(version, "videolink") and not has_child(version, "videoLink"):
        issues.append(
            f"ERROR: {where}: element is spelled <videolink>. The field is videoLink — "
            f"the guide's sample definition uses the wrong casing."
        )
    if (has_image or has_image_link) and not has_child(version, "imageAltText"):
        issues.append(
            f"WARN: {where}: an image is set but <imageAltText> is missing — it is "
            f"required when image, imageLink, or imageLocation is specified."
        )
    if (has_image or has_image_link) and not has_child(version, "imageLocation"):
        issues.append(
            f"WARN: {where}: an image is set but <imageLocation> is missing — it is "
            f"required when image, imageLink, or imageAltText is specified."
        )

    # Theme pair (L99250-99275).
    if has_child(version, "themeColor") != has_child(version, "themeSaturation"):
        issues.append(
            f"WARN: {where}: themeColor and themeSaturation require each other; only one is set."
        )

    # Documented field lengths.
    for field, maximum in MAX_LENGTHS.items():
        value = child_text(version, field)
        if value is not None and len(value) > maximum:
            issues.append(
                f"WARN: {where}: {field} is {len(value)} characters — documented "
                f"maximum is {maximum}."
            )

    # Docked-only and floating/targeted-only fields.
    if display_type and display_type != "DockedComposer":
        if has_child(version, "videoLink"):
            issues.append(
                f"WARN: {where}: videoLink is set on a {display_type} prompt — video is "
                f"documented for docked prompts."
            )
        if has_child(version, "header"):
            issues.append(
                f"WARN: {where}: header is set on a {display_type} prompt — header is the "
                f"docked prompt's browser-bar label."
            )
    if display_type == "DockedComposer" and has_child(version, "dismissButtonLabel"):
        issues.append(
            f"WARN: {where}: dismissButtonLabel is documented for floating or targeted "
            f"prompts, not docked."
        )

    # Action button consistency.
    shows_button = (child_text(version, "shouldDisplayActionButton") or "").lower() == "true"
    if shows_button and not has_child(version, "actionButtonLabel"):
        issues.append(
            f"WARN: {where}: shouldDisplayActionButton is true but actionButtonLabel is missing."
        )

    issues.extend(check_ui_formula_rule(where, version))
    if check_audience:
        issues.extend(check_audience_scope(where, version))
    return issues


def check_ui_formula_rule(where: str, version: ET.Element) -> list[str]:
    issues: list[str] = []
    for rule in child_elements(version, "uiFormulaRule"):
        criteria = child_elements(rule, "criteria")
        if not criteria:
            issues.append(
                f"ERROR: {where}: <uiFormulaRule> has no <criteria> — an empty rule "
                f"gates nothing."
            )
        for criterion in criteria:
            left = child_text(criterion, "leftValue")
            operator = child_text(criterion, "operator")
            right = child_text(criterion, "rightValue")
            if operator is not None and operator not in VALID_OPERATORS:
                issues.append(
                    f"ERROR: {where}: uiFormulaRule operator '{operator}' is not valid — "
                    f"EQUAL is the only supported value."
                )
            if not left:
                issues.append(f"ERROR: {where}: uiFormulaRule criterion has no leftValue (Required).")
                continue
            is_permission = left.startswith("{!$Permission.")
            is_profile = left.startswith("{!ENCODED:")
            if not (is_permission or is_profile):
                issues.append(
                    f"ERROR: {where}: uiFormulaRule leftValue '{left}' is not a supported "
                    f"expression. Only {{!$Permission.CustomPermission.<name>}}, "
                    f"{{!$Permission.StandardPermission.<name>}}, and "
                    f"{{!ENCODED:{{!ID:$User.Profile.Key}}}} are accepted."
                )
            if is_permission and (right or "").lower() != "true":
                issues.append(
                    f"WARN: {where}: uiFormulaRule permission criterion has rightValue "
                    f"'{right}' — permissions are evaluated against true."
                )
    return issues


def check_audience_scope(where: str, version: ET.Element) -> list[str]:
    """INFO when nothing narrows the audience: the guidance shows to everyone."""
    has_rule = bool(child_elements(version, "uiFormulaRule"))
    user_access = child_text(version, "userAccess")
    profile_access = child_text(version, "userProfileAccess")
    restricted = user_access == "SpecificPermissions" or profile_access == "SpecificProfiles"
    if not has_rule and not restricted:
        return [
            f"INFO: {where}: no uiFormulaRule and neither userAccess nor "
            f"userProfileAccess is restricted — this guidance displays to everyone "
            f"who reaches the page. Intentional for an org-wide announcement; a gap "
            f"for anything cohort-scoped."
        ]
    if restricted and not has_rule:
        return [
            f"WARN: {where}: userAccess/userProfileAccess is set to a Specific* value "
            f"but there is no <uiFormulaRule> to evaluate — the restriction has no "
            f"criteria, so the guidance displays by default."
        ]
    return []


def check_walkthrough(name: str, versions: list[ET.Element]) -> list[str]:
    """Cross-version rules: step numbering and step count."""
    issues: list[str] = []
    numbered = [
        (as_int(child_text(v, "stepNumber")), v)
        for v in versions
        if child_text(v, "stepNumber") is not None
    ]
    if not numbered:
        if len(versions) > 1:
            issues.append(
                f"ERROR: {name}: {len(versions)} promptVersions entries but no stepNumber "
                f"on any of them. stepNumber is required for walkthroughs."
            )
        return issues

    steps = sorted(n for n, _ in numbered if n is not None)
    if len(steps) != len(numbered):
        issues.append(f"ERROR: {name}: a stepNumber is present but not an integer.")
        return issues

    if len(steps) == 1:
        issues.append(
            f"WARN: {name}: stepNumber is set on a single version. A walkthrough needs "
            f"at least 2 steps; for a one-off prompt, remove stepNumber."
        )

    if len(steps) > MAX_STEPS:
        issues.append(
            f"ERROR: {name}: {len(steps)} steps — the documented maximum is {MAX_STEPS}."
        )
    elif len(steps) > RECOMMENDED_MAX_STEPS:
        issues.append(
            f"WARN: {name}: {len(steps)} steps — Salesforce recommends at most "
            f"{RECOMMENDED_MAX_STEPS} for acceptable completion rates. Consider splitting "
            f"into two walkthroughs."
        )

    duplicates = sorted({n for n in steps if steps.count(n) > 1})
    if duplicates:
        issues.append(
            f"ERROR: {name}: stepNumber repeated: {duplicates}. Numbers must be "
            f"consecutive without repeated or skipped numbers."
        )
    expected = list(range(1, len(steps) + 1))
    if not duplicates and steps != expected:
        issues.append(
            f"ERROR: {name}: stepNumber sequence is {steps}, expected {expected}. "
            f"Numbers must be consecutive without repeated or skipped numbers "
            f"(renumber from 1 after deleting a step)."
        )

    # Schedule fields belong on the first step; the action button on the last.
    by_step = {n: v for n, v in numbered if n is not None}
    first = by_step.get(min(steps))
    last = by_step.get(max(steps))
    if first is not None:
        for n, version in numbered:
            if version is first:
                continue
            for field in ("startDate", "endDate", "delayDays", "timesToDisplay", "publishedDate"):
                if has_child(version, field):
                    issues.append(
                        f"WARN: {name} [step {n}]: <{field}> is set on a step other than the "
                        f"first. For a walkthrough this value is read from the first step only."
                    )
    if last is not None:
        for n, version in numbered:
            if version is last:
                continue
            for field in ("actionButtonLabel", "actionButtonLink"):
                if has_child(version, field):
                    issues.append(
                        f"WARN: {name} [step {n}]: <{field}> is set on a step other than the "
                        f"last. For a walkthrough this value is read from the last step."
                    )
    return issues


def check_prompt_file(path: Path) -> list[str]:
    name = path.name
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"ERROR: {name}: XML is not well-formed: {exc}"]

    issues = check_root(name, root)
    versions = child_elements(root, "promptVersions")

    # The audience gate is read from the first step of a walkthrough, so only
    # that step (or a non-walkthrough version) is checked for an open audience.
    steps = [as_int(child_text(v, "stepNumber")) for v in versions]
    lowest = min((s for s in steps if s is not None), default=None)
    for index, version in enumerate(versions, start=1):
        step = steps[index - 1]
        audience = step is None or step == lowest
        issues.extend(check_version(name, index, version, check_audience=audience))
    issues.extend(check_walkthrough(name, versions))
    return issues


def check_in_app_guidance_and_walkthroughs(manifest_dir: Path) -> list[str]:
    if not manifest_dir.exists():
        return [f"ERROR: manifest directory not found: {manifest_dir}"]

    issues: list[str] = []
    for path in find_prompt_files(manifest_dir):
        issues.extend(check_prompt_file(path))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_in_app_guidance_and_walkthroughs(manifest_dir)

    if not issues:
        print("No In-App Guidance issues found.")
        return 0

    for issue in issues:
        print(issue)

    errors = [i for i in issues if i.startswith("ERROR")]
    warns = [i for i in issues if i.startswith("WARN")]
    infos = [i for i in issues if i.startswith("INFO")]
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s), {len(infos)} info.")

    if errors:
        return 1
    if args.strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
