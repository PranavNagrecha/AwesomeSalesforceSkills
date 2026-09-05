#!/usr/bin/env python3
"""Checker script for the Omni-Channel Routing Setup skill.

Validates the six Omni-Channel metadata types against the shapes documented in
``references/metadata-examples.md`` (Metadata API Developer Guide v62), and —
the part a per-file lint cannot do — checks that they refer to each other.
An Omni-Channel package is only ever correct as a set: a channel with no
routing configuration, or a routing configuration with nobody who can go
available on it, deploys cleanly and routes nothing.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omni_channel_routing_setup.py --manifest-dir force-app/main/default
    python3 check_omni_channel_routing_setup.py --manifest-dir artefacts/M3-S05
    python3 check_omni_channel_routing_setup.py --help

Exit code
---------
ERROR findings exit 1. WARN and INFO findings are always printed but exit 0.

ERROR (exit 1)
  E1  A ServiceChannel with no QueueRoutingConfig anywhere in the manifest.
      Work items enter the channel and never reach a queue.
  E2  A ServiceChannel that no ServicePresenceStatus names under <channels>.
      No agent can select a status that receives its work.
  E3  A QueueRoutingConfig with neither a PresenceUserConfig nor a
      ServicePresenceStatus in the manifest: capacity is never assigned to
      anyone, so the routing configuration has no one to route to.
  E4  A ServiceChannel with no <relatedEntityType>: nothing defines what kind
      of work item it routes.
  E5  A QueueRoutingConfig whose <routingModel> is outside the documented enum,
      or with no <routingPriority> (the guide: routingPriority is required).
  E6  A PresenceUserConfig whose <capacity> is missing or 0: agents assigned to
      it have no workload ceiling and receive nothing.
  E0  A file under one of the Omni-Channel folders that does not parse.

WARN (printed, exit 0)
  W0  No Omni-Channel metadata found under --manifest-dir.
  W1  <pushTimeout> missing or 0. 0 is documented as "push timeout off", which
      is a decision, not a default — a declined item then blocks capacity.
  W2  A ServicePresenceStatus with no <channels>: the guide says it is treated
      as Away. Legitimate for a real Away status, a bug for a working one.
  W3  A PresenceUserConfig with no <assignments>: nobody uses it.
  W5  An Apex trigger that looks like it sets Case.OwnerId directly, which
      bypasses Omni-Channel capacity enforcement.

INFO (printed, exit 0)
  I1  A <presenceStatusOnPushTimeout> or <presenceStatusOnDecline> naming a
      status that is not in this manifest. Often correct — the standard
      statuses are not part of the package — so it is reported, not enforced.

Worked example
--------------
Build a manifest from the six xml fences in ``references/metadata-examples.md``
and the checker exits 0::

    $ python3 check_omni_channel_routing_setup.py --manifest-dir /tmp/fixture
    OK: no ERROR findings (0 warning(s)).
    $ echo $?
    0

Drop the routing configuration and the presence statuses, leaving the channel
on its own, and the mutual-consistency rules fire::

    $ python3 check_omni_channel_routing_setup.py --manifest-dir /tmp/lone-channel
    ERROR E1  [serviceChannels/Case_Channel.serviceChannel-meta.xml] ...
    ERROR E2  [serviceChannels/Case_Channel.serviceChannel-meta.xml] ...
    $ echo $?
    1
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# routingModel enum, references/metadata-examples.md § 6 (Metadata API guide).
_ROUTING_MODELS = {"LEAST_ACTIVE", "MOST_AVAILABLE", "EXTERNAL_ROUTING"}

# Type -> the file suffix the Metadata API writes it under.
_SUFFIXES = {
    "ServiceChannel": "serviceChannel",
    "ServicePresenceStatus": "servicePresenceStatus",
    "PresenceDeclineReason": "presenceDeclineReason",
    "PresenceUserConfig": "presenceUserConfig",
    "QueueRoutingConfig": "queueRoutingConfig",
    "Skill": "skill",
}


class Finding:
    """One check result. Severity is ERROR, WARN or INFO."""

    def __init__(self, severity: str, code: str, where: str, message: str) -> None:
        self.severity = severity
        self.code = code
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity:5} {self.code}  [{self.where}] {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Omni-Channel routing setup metadata for common configuration issues. "
            "Checks Service Channels, Routing Configurations, Presence Configurations "
            "and Presence Statuses individually, and checks that they reference each "
            "other: a channel with no routing configuration is an error, not silence."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--quiet-info",
        action="store_true",
        help="Suppress INFO findings; print only ERROR and WARN.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _local(tag: str) -> str:
    """Local name of a possibly namespaced ElementTree tag."""
    return tag.split("}")[-1] if "}" in tag else tag


def _children(element: ET.Element, tag: str) -> list[ET.Element]:
    """Every direct child with this local name.

    Matching is on the local name so namespaced (retrieved) and bare
    (hand-written) files behave the same. Presence is always tested on the
    length of this list or with ``is not None`` — never on an Element's own
    truthiness, which is False for any element that has no children.
    """
    return [child for child in element if _local(child.tag) == tag]


def _text(element: ET.Element, tag: str) -> str:
    """Text of the first direct child with this local name, stripped."""
    found = _children(element, tag)
    if not found:
        return ""
    return (found[0].text or "").strip()


def _descendant_texts(element: ET.Element, tag: str) -> list[str]:
    """Stripped text of every descendant with this local name, at any depth."""
    values = []
    for node in element.iter():
        if _local(node.tag) == tag:
            value = (node.text or "").strip()
            if value:
                values.append(value)
    return values


class MetadataFile:
    """One parsed Omni-Channel metadata file."""

    def __init__(self, path: Path, root: ET.Element, manifest_dir: Path) -> None:
        self.path = path
        self.root = root
        try:
            self.where = str(path.relative_to(manifest_dir))
        except ValueError:
            self.where = path.name

    @property
    def dev_name(self) -> str:
        """Developer name: <fullName> when present, else the file stem."""
        return _text(self.root, "fullName") or self.path.name.split(".")[0]


def collect(manifest_dir: Path, metadata_type: str) -> tuple[list[MetadataFile], list[Finding]]:
    """Return every file of this metadata type under the manifest, plus parse errors."""
    suffix = _SUFFIXES[metadata_type]
    paths = sorted(
        set(manifest_dir.rglob(f"*.{suffix}-meta.xml"))
        | set(manifest_dir.rglob(f"*.{suffix}"))
    )
    files: list[MetadataFile] = []
    findings: list[Finding] = []
    for path in paths:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            findings.append(Finding("ERROR", "E0", path.name, f"XML parse error: {exc}"))
            continue
        if _local(root.tag) != metadata_type:
            continue
        files.append(MetadataFile(path, root, manifest_dir))
    return files, findings


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_service_channels(
    channels: list[MetadataFile],
    routing_configs: list[MetadataFile],
    statuses: list[MetadataFile],
) -> list[Finding]:
    """Per-channel shape, plus the two cross-references a channel depends on."""
    findings: list[Finding] = []

    # Every channel developer name any presence status claims.
    claimed: set[str] = set()
    for status in statuses:
        claimed.update(_descendant_texts(status.root, "channel"))

    for channel in channels:
        name = channel.dev_name

        if not _text(channel.root, "relatedEntityType"):
            findings.append(
                Finding(
                    "ERROR", "E4", channel.where,
                    f"ServiceChannel '{name}': <relatedEntityType> is not set. Every "
                    "service channel must name the object whose records it routes "
                    "(Case, MessagingSession, ...).",
                )
            )

        if not routing_configs:
            findings.append(
                Finding(
                    "ERROR", "E1", channel.where,
                    f"ServiceChannel '{name}': this manifest contains no "
                    "QueueRoutingConfig. Work items enter the channel and never reach a "
                    "queue. Deploy the routing configuration with the channel "
                    "(references/metadata-examples.md § 6).",
                )
            )

        if name not in claimed:
            if statuses:
                detail = (
                    "none of the "
                    f"{len(statuses)} ServicePresenceStatus file(s) in this manifest "
                    f"name it under <channels>: {', '.join(sorted(claimed)) or '(none)'}"
                )
            else:
                detail = "this manifest contains no ServicePresenceStatus at all"
            findings.append(
                Finding(
                    "ERROR", "E2", channel.where,
                    f"ServiceChannel '{name}': {detail}. No agent can select a status "
                    "that receives work on this channel, so nothing routes "
                    "(references/metadata-examples.md § 2).",
                )
            )

    return findings


def check_routing_configurations(
    routing_configs: list[MetadataFile],
    presence_configs: list[MetadataFile],
    statuses: list[MetadataFile],
) -> list[Finding]:
    """Per-config shape, plus the presence side a routing configuration needs."""
    findings: list[Finding] = []

    for config in routing_configs:
        name = config.dev_name

        routing_model = _text(config.root, "routingModel")
        if routing_model and routing_model not in _ROUTING_MODELS:
            findings.append(
                Finding(
                    "ERROR", "E5", config.where,
                    f"QueueRoutingConfig '{name}': routingModel '{routing_model}' is not "
                    f"one of {', '.join(sorted(_ROUTING_MODELS))}.",
                )
            )

        if not _text(config.root, "routingPriority"):
            findings.append(
                Finding(
                    "ERROR", "E5", config.where,
                    f"QueueRoutingConfig '{name}': <routingPriority> is required and is "
                    "missing. Lower numbers route first; leaving it out makes the "
                    "sequencing across queues undefined.",
                )
            )

        push_timeout = _text(config.root, "pushTimeout")
        if push_timeout in ("", "0"):
            shown = "0 (push timeout off)" if push_timeout else "missing"
            findings.append(
                Finding(
                    "WARN", "W1", config.where,
                    f"QueueRoutingConfig '{name}': pushTimeout is {shown}. A work item an "
                    "agent never accepts then holds their capacity indefinitely. Set a "
                    "timeout and pair it with <presenceStatusOnPushTimeout>, or record "
                    "that off is deliberate.",
                )
            )

        if not presence_configs and not statuses:
            findings.append(
                Finding(
                    "ERROR", "E3", config.where,
                    f"QueueRoutingConfig '{name}': this manifest contains neither a "
                    "PresenceUserConfig nor a ServicePresenceStatus. Nobody is given "
                    "capacity and no status makes an agent available, so this routing "
                    "configuration has no one to route to.",
                )
            )

    return findings


def check_presence_configurations(
    presence_configs: list[MetadataFile], statuses: list[MetadataFile]
) -> list[Finding]:
    """PresenceUserConfig capacity, assignment, and status references."""
    findings: list[Finding] = []
    known_statuses = {status.dev_name for status in statuses}

    for config in presence_configs:
        name = config.dev_name

        capacity = _text(config.root, "capacity")
        if capacity in ("", "0", "0.0"):
            findings.append(
                Finding(
                    "ERROR", "E6", config.where,
                    f"PresenceUserConfig '{name}': capacity is "
                    f"{capacity or 'missing'}. Agents on this configuration have no "
                    "workload ceiling and receive no work.",
                )
            )

        if not _children(config.root, "assignments"):
            findings.append(
                Finding(
                    "WARN", "W3", config.where,
                    f"PresenceUserConfig '{name}': no <assignments>. No profile or user "
                    "is on this configuration, so it governs nobody.",
                )
            )

        for tag in ("presenceStatusOnDecline", "presenceStatusOnPushTimeout"):
            referenced = _text(config.root, tag)
            if referenced and known_statuses and referenced not in known_statuses:
                findings.append(
                    Finding(
                        "INFO", "I1", config.where,
                        f"PresenceUserConfig '{name}': <{tag}>{referenced}</{tag}> is not "
                        f"among the statuses in this manifest "
                        f"({', '.join(sorted(known_statuses))}). Standard statuses are "
                        "fine here; confirm this one exists in the target org.",
                    )
                )

    return findings


def check_presence_statuses(statuses: list[MetadataFile]) -> list[Finding]:
    """A status with no channels is an Away status, whether or not that was meant."""
    findings: list[Finding] = []
    for status in statuses:
        if not _descendant_texts(status.root, "channel"):
            findings.append(
                Finding(
                    "WARN", "W2", status.where,
                    f"ServicePresenceStatus '{status.dev_name}': no <channels>. The guide "
                    "treats a status with no channels as Away — correct for a break "
                    "status, a bug for one agents are meant to work from.",
                )
            )
    return findings


def check_for_apex_routing_triggers(manifest_dir: Path) -> list[Finding]:
    """Flag Apex that looks like it assigns Case.OwnerId to a user directly."""
    findings: list[Finding] = []

    trigger_files = list(manifest_dir.rglob("*.trigger"))
    trigger_files += list(manifest_dir.rglob("triggers/*.cls"))

    for trigger_path in trigger_files:
        try:
            content = trigger_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Heuristic: not all OwnerId sets are wrong, but in a routing package they
        # usually are. Assigning to a Queue id is the legitimate case.
        if (
            "OwnerId" in content
            and "Case" in content
            and ("insert" in content.lower() or "update" in content.lower())
            and "Queue" not in content
        ):
            findings.append(
                Finding(
                    "WARN", "W5", trigger_path.name,
                    "may set Case.OwnerId directly to a User for routing. That bypasses "
                    "Omni-Channel capacity enforcement and availability checks. Route "
                    "through a queue with a routing configuration instead.",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_omni_channel_routing_setup(manifest_dir: Path) -> list[Finding]:
    """Return every finding for the Omni-Channel metadata under this directory."""
    if not manifest_dir.exists():
        return [
            Finding("ERROR", "E0", str(manifest_dir), "manifest directory not found.")
        ]

    findings: list[Finding] = []
    collected: dict[str, list[MetadataFile]] = {}
    for metadata_type in _SUFFIXES:
        files, parse_errors = collect(manifest_dir, metadata_type)
        collected[metadata_type] = files
        findings.extend(parse_errors)

    channels = collected["ServiceChannel"]
    routing_configs = collected["QueueRoutingConfig"]
    presence_configs = collected["PresenceUserConfig"]
    statuses = collected["ServicePresenceStatus"]

    if not any(collected.values()) and not findings:
        # Not every package configures Omni-Channel; absence is not a failure.
        # It is never silent either: a step that was supposed to build a channel
        # and built nothing must not read as a clean pass.
        return [
            Finding(
                "WARN", "W0", str(manifest_dir),
                "no Omni-Channel metadata found under --manifest-dir (looked for "
                + ", ".join(f"*.{suffix}-meta.xml" for suffix in sorted(_SUFFIXES.values()))
                + " anywhere beneath it). Nothing was checked.",
            )
        ]

    findings.extend(check_service_channels(channels, routing_configs, statuses))
    findings.extend(check_routing_configurations(routing_configs, presence_configs, statuses))
    findings.extend(check_presence_configurations(presence_configs, statuses))
    findings.extend(check_presence_statuses(statuses))
    findings.extend(check_for_apex_routing_triggers(manifest_dir))

    return findings


def main() -> int:
    args = parse_args()
    findings = check_omni_channel_routing_setup(Path(args.manifest_dir))

    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARN"]
    infos = [f for f in findings if f.severity == "INFO"]

    for finding in errors + warnings + ([] if args.quiet_info else infos):
        print(finding)

    if not errors:
        print(f"OK: no ERROR findings ({len(warnings)} warning(s)).")
        return 0

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1


if __name__ == "__main__":
    if main() != 0:
        sys.exit(1)
    sys.exit(0)
