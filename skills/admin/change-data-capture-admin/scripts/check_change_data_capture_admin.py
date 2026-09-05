#!/usr/bin/env python3
"""Checker script for the Change Data Capture Admin skill.

Inspects PlatformEventChannel / PlatformEventChannelMember metadata in SFDX
source format (or a retrieved unzip) for the configuration mistakes documented
in references/gotchas.md and references/metadata-examples.md.

Uses stdlib only - no pip dependencies.

Checks
    1. ERROR  selectedEntity on a `data` channel that is not a change event
              (must end in `ChangeEvent`).
    2. ERROR  the same enriched field listed twice on one channel member.
    3. WARN   a member whose eventChannel is a custom `__chn` channel that has
              no PlatformEventChannel file in the tree.
    4. WARN   a channel file that looks Data Cloud-managed.
    5. INFO   filterExpression / enrichedFields used below the API version that
              introduced them (56.0 / 51.0), read from package.xml or
              sfdx-project.json.
    6. INFO   a `data` channel with no member files pointing at it.

Usage:
    python3 check_change_data_capture_admin.py [--manifest-dir path/to/metadata]

Exit codes:
    0 - no ERROR or WARN findings (INFO findings may still be printed)
    1 - at least one ERROR or WARN finding, or the directory does not exist
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Metadata API Developer Guide, PlatformEventChannelMember:
# enrichedFields "Available in API version 51.0 and later";
# filterExpression "Available in API version 56.0 and later".
ENRICHED_FIELDS_MIN_API = 51.0
FILTER_EXPRESSION_MIN_API = 56.0

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"


class Finding:
    def __init__(self, severity: str, path: Path, message: str) -> None:
        self.severity = severity
        self.path = path
        self.message = message

    def render(self) -> str:
        return f"{self.severity}: {self.path.name}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Change Data Capture channel metadata for known configuration mistakes.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce project or retrieved metadata (default: current directory).",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def _find(parent: ET.Element, name: str) -> ET.Element | None:
    """Direct child lookup that works with or without the metadata namespace.

    `parent.find(a) or parent.find(b)` must never be used here: an Element with
    no children is falsy, so a found leaf such as <eventChannel> would be
    discarded and every namespaced file would look empty (fail-open).
    """
    element = parent.find(_tag(name))
    if element is not None:
        return element
    return parent.find(name)


def _findall(parent: ET.Element, name: str) -> list[ET.Element]:
    found = parent.findall(_tag(name))
    if found:
        return found
    return parent.findall(name)


def _text(parent: ET.Element, name: str) -> str:
    element = _find(parent, name)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _files(root: Path, suffix: str) -> list[Path]:
    """All files for one metadata suffix, in DX (-meta.xml) or retrieved form."""
    results = list(root.rglob(f"*.{suffix}-meta.xml"))
    results.extend(p for p in root.rglob(f"*.{suffix}") if p.is_file())
    return sorted(set(results))


def _component_name(path: Path, suffix: str) -> str:
    """`SalesEvents__chn.platformEventChannel-meta.xml` -> `SalesEvents__chn`."""
    name = path.name
    for tail in (f".{suffix}-meta.xml", f".{suffix}"):
        if name.endswith(tail):
            return name[: -len(tail)]
    return path.stem


def detect_api_version(root: Path) -> tuple[float | None, str]:
    """Highest API version declared by the project, and where it came from."""
    versions: list[tuple[float, str]] = []

    for manifest in root.rglob("package.xml"):
        try:
            tree = ET.parse(manifest)
        except (ET.ParseError, OSError):
            continue
        raw = _text(tree.getroot(), "version")
        if raw:
            try:
                versions.append((float(raw), manifest.name))
            except ValueError:
                continue

    for project in root.rglob("sfdx-project.json"):
        try:
            data = json.loads(project.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        raw = data.get("sourceApiVersion")
        if raw:
            try:
                versions.append((float(raw), project.name))
            except (TypeError, ValueError):
                continue

    if not versions:
        return None, ""
    best = max(versions, key=lambda item: item[0])
    return best[0], best[1]


def read_channels(root: Path) -> tuple[dict[str, str], list[Finding]]:
    """Map custom channel name -> channelType, plus findings about the files."""
    channels: dict[str, str] = {}
    findings: list[Finding] = []

    for path in _files(root, "platformEventChannel"):
        try:
            element = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            findings.append(Finding(ERROR, path, f"could not be parsed as XML ({exc})."))
            continue

        name = _component_name(path, "platformEventChannel")
        channels[name] = _text(element, "channelType")

        if "datacloud" in name.lower() or "data_cloud" in name.lower():
            findings.append(
                Finding(
                    WARN,
                    path,
                    f"channel '{name}' looks Data Cloud-managed. Deploying members for a "
                    "feature-managed channel can disrupt that feature's ingestion silently; "
                    "manage it in that feature's own admin UI (references/gotchas.md, Gotcha 1).",
                )
            )

    return channels, findings


def check_member(path: Path, channels: dict[str, str], api_version: float | None,
                 api_source: str) -> tuple[list[Finding], str]:
    """Check one PlatformEventChannelMember file. Returns findings and its channel."""
    findings: list[Finding] = []

    try:
        element = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        return [Finding(ERROR, path, f"could not be parsed as XML ({exc}).")], ""

    channel = _text(element, "eventChannel")
    entity = _text(element, "selectedEntity")

    if not channel:
        findings.append(
            Finding(ERROR, path, "<eventChannel> is missing; it is a required field on "
                                 "PlatformEventChannelMember.")
        )
    if not entity:
        findings.append(
            Finding(ERROR, path, "<selectedEntity> is missing; it is a required field on "
                                 "PlatformEventChannelMember.")
        )

    # Standard channel is named ChangeEvents and has no PlatformEventChannel file:
    # "In API version 47.0 and later, you can't deploy or retrieve the ChangeEvents
    # standard channel." Custom channel names end in __chn.
    is_standard_channel = channel == "ChangeEvents"
    channel_type = "data" if is_standard_channel else channels.get(channel, "")

    if channel and not is_standard_channel and channel not in channels:
        findings.append(
            Finding(
                WARN,
                path,
                f"references channel '{channel}', which has no "
                f"platformEventChannels/{channel}.platformEventChannel-meta.xml in this tree. "
                "Deploy the channel in the same package as its members, or check for a "
                "double underscore that should have been collapsed in the file name "
                "(references/gotchas.md, Gotcha 5).",
            )
        )

    # A data channel carries change events only.
    if entity and channel_type == "data" and not entity.endswith("ChangeEvent"):
        findings.append(
            Finding(
                ERROR,
                path,
                f"selectedEntity '{entity}' on data channel '{channel}' is not a change "
                "event. On channelType=data the value is the change event name, such as "
                "AccountChangeEvent or MyObject__ChangeEvent. A custom platform event "
                "(MyEvent__e) belongs on a channelType=event channel.",
            )
        )

    enriched = [
        (_text(field, "name") or "").strip()
        for field in _findall(element, "enrichedFields")
    ]
    seen: set[str] = set()
    duplicates: list[str] = []
    for name in enriched:
        if not name:
            continue
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    for name in duplicates:
        findings.append(
            Finding(
                ERROR,
                path,
                f"enriched field '{name}' is listed more than once. Each field is enriched "
                "once per channel member; remove the duplicate <enrichedFields> block.",
            )
        )

    filter_element = _find(element, "filterExpression")

    if api_version is not None:
        where = f" (API {api_version:g} from {api_source})" if api_source else ""
        if filter_element is not None and api_version < FILTER_EXPRESSION_MIN_API:
            findings.append(
                Finding(
                    INFO,
                    path,
                    f"uses <filterExpression> but the project targets API {api_version:g}"
                    f"{where}. filterExpression is 'Available in API version 56.0 and later' "
                    "(Metadata API Developer Guide, PlatformEventChannelMember).",
                )
            )
        if enriched and api_version < ENRICHED_FIELDS_MIN_API:
            findings.append(
                Finding(
                    INFO,
                    path,
                    f"uses <enrichedFields> but the project targets API {api_version:g}"
                    f"{where}. enrichedFields is 'Available in API version 51.0 and later' "
                    "(Metadata API Developer Guide, PlatformEventChannelMember).",
                )
            )

    return findings, channel


def check_change_data_capture_admin(manifest_dir: Path) -> list[Finding]:
    if not manifest_dir.exists():
        return [Finding(ERROR, manifest_dir, "manifest directory not found.")]

    channels, findings = read_channels(manifest_dir)
    api_version, api_source = detect_api_version(manifest_dir)

    member_files = _files(manifest_dir, "platformEventChannelMember")
    if not channels and not member_files:
        print(f"INFO: no PlatformEventChannel or PlatformEventChannelMember metadata "
              f"found under {manifest_dir}.")
        return findings

    referenced: dict[str, int] = {}
    for path in member_files:
        member_findings, channel = check_member(path, channels, api_version, api_source)
        findings.extend(member_findings)
        if channel:
            referenced[channel] = referenced.get(channel, 0) + 1

    for name, channel_type in sorted(channels.items()):
        if channel_type == "data" and referenced.get(name, 0) == 0:
            findings.append(
                Finding(
                    INFO,
                    manifest_dir / "platformEventChannels" / f"{name}.platformEventChannel-meta.xml",
                    f"data channel '{name}' has no PlatformEventChannelMember files in this "
                    "tree, so it publishes nothing. Add a member per selected entity, or drop "
                    "the channel from the package.",
                )
            )

    return findings


def main() -> int:
    args = parse_args()
    findings = check_change_data_capture_admin(Path(args.manifest_dir))

    order = {ERROR: 0, WARN: 1, INFO: 2}
    for finding in sorted(findings, key=lambda f: (order[f.severity], str(f.path))):
        print(finding.render())

    blocking = [f for f in findings if f.severity in (ERROR, WARN)]
    if not blocking:
        if not findings:
            print("No CDC channel configuration issues found.")
        return 0

    print(
        f"{len(blocking)} blocking finding(s): "
        f"{sum(1 for f in blocking if f.severity == ERROR)} ERROR, "
        f"{sum(1 for f in blocking if f.severity == WARN)} WARN.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
