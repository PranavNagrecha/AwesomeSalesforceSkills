#!/usr/bin/env python3
"""Checker for a Service Cloud Voice contact-center manifest.

Lints the metadata a Service Cloud Voice setup actually deploys, against element
names, enum values and required-field pairings taken from the Metadata API
Developer Guide (Summer '26 / v62) and the Object Reference. Stdlib only.

Checks performed
----------------
1. CallCenter          Parses; carries the three required labels (displayName,
                       displayNameLabel, internalNameLabel); every `sections`
                       block has label + name; every `items` block has
                       label + name + value.
                       api_meta.txt L31421-31552, sample L31626-31682.
2. ConversationVendorInfo
                       Parses; `vendorType` is one of the four documented enum
                       values; the connector/bridge/integration fields are
                       consistent with the declared vendor type; deprecated
                       fields are not set; agentSSO/recording-access flags carry
                       their documented companions.
                       api_meta.txt L38622-39064.
3. ServiceChannel      A Voice channel exists (relatedEntityType = VoiceCall) and
                       its After Conversation Work fields are internally
                       complete and inside the documented 10-3600 / 1-10 ranges.
                       api_meta.txt L107776-107905.
4. Presence config     Presence statuses name at least one service channel (a
                       channel-less status is silently an Away status), a Voice
                       channel is reachable from some status, and
                       PresenceUserConfig has the required `capacity` without
                       contradictory accept/decline flags.
                       api_meta.txt L96980-97062, L107966-107973.
5. PermissionSet       Voice-related permission sets do not use invented
                       `<userPermissions><name>` values (no catalogue of
                       permission API names is published in the grounded
                       sources) and grant VoiceCall/VoiceCallRecording sensibly.
                       api_meta.txt L95170-95179; object_reference.txt L306747.
6. Org settings        ServiceCloudVoice.settings uses fields that exist on
                       ServiceCloudVoiceSettings rather than Sales Dialer's
                       VoiceSettings, and MyDomain.settings does not leave
                       isFirstPartyCookieUseRequired true.
                       api_meta.txt L126818-126900, L128646-128712, L122293-122299.

Usage
-----
    python3 check_service_cloud_voice_setup.py --manifest-dir force-app/main/default
    python3 check_service_cloud_voice_setup.py --manifest-dir . --warn-only

Exit codes: 0 = no errors, 1 = at least one ERROR.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://soap.sforce.com/2006/04/metadata"

# api_meta.txt L39028-39034
VENDOR_TYPES = {
    "Amazon_Connect",
    "BringYourOwnChannelPartner",
    "BringYourOwnContactCenter",
    "ServiceCloudVoicePartner",
}
# Vendor types for which the guide scopes connector / bridge / integration-class
# fields (api_meta.txt L38708-39010). Plain Amazon_Connect is NOT among them.
PARTNER_VENDOR_TYPES = {
    "ServiceCloudVoicePartner",
    "BringYourOwnContactCenter",
    "BringYourOwnChannelPartner",
}
PARTNER_ONLY_FIELDS = (
    "connectorUrl",
    "bridgeComponent",
    "integrationClass",
    "clientAuthMode",
    "customLoginUrl",
    "telephonySettingsComponent",
)
# api_meta.txt L38684-38706, L38838-38845
AMAZON_ONLY_FIELDS = (
    "awsAccountKey",
    "awsRootEmail",
    "awsTenantVersion",
    "isTaxCompliant",
)
# api_meta.txt L38915-38925, L38957-38961
DEPRECATED_CVI_FIELDS = {
    "integrationClassName": "deprecated in API 53.0 — use integrationClass instead",
    "serverAuthMode": "deprecated in API 53.0 — set to None or omit",
}
# api_meta.txt L38739-38755
CLIENT_AUTH_MODES = {"Custom", "Mixed", "SSO"}
# api_meta.txt L126818-126900
SCV_SETTINGS_FIELDS = {
    "disableSCVTaskCreationForHVS",
    "enableAmazonQueueManagement",
    "enableDefaultChannelForSCV",
    "enableDigitalVoiceWhatsapp",
    "enableEndUserForSCV",
    "enableOmniCapacityForSCV",
    "enablePhoneNumberMaskingForSCV",
    "enablePTQueueManagement",
    "enableRZoneCloudVoiceOptIn",
    "enableSCVBYOT",
    "enableSCVExternalTelephony",
    "enableSCVOpenVCAsNewTabHVS",
    "enableSCVSupportBannerDisplayed",
    "enableServiceCloudVoice",
}
# api_meta.txt L128675-128712 — these belong to Sales Dialer's VoiceSettings.
DIALER_SETTINGS_FIELDS = {
    "enableCallDisposition",
    "enableConsentReminder",
    "enableDefaultRecording",
    "enableVoiceCallList",
    "enableVoiceCallRecording",
    "enableVoiceCoaching",
    "enableVoiceConferencing",
    "enableVoiceLocalPresence",
    "enableVoiceMail",
    "enableVoiceMailDrop",
}
ACW_MIN_SECONDS = 10        # api_meta.txt L107784-107788
ACW_MAX_SECONDS = 3600
MAX_EXTENSIONS_MIN = 1      # api_meta.txt L107852-107856
MAX_EXTENSIONS_MAX = 10


class Finding:
    """One lint result. `level` is 'ERROR' or 'WARN'."""

    def __init__(self, level: str, path: Path, message: str) -> None:
        self.level = level
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.level}: {self.path}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a Service Cloud Voice contact-center manifest: CallCenter, "
            "ConversationVendorInfo, ServiceChannel, presence config, permission "
            "sets and org settings."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the source-format metadata, e.g. force-app/main/default (default: .).",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Report findings but always exit 0.",
    )
    return parser.parse_args()


# --------------------------------------------------------------------------- #
# XML helpers. A leaf Element is falsy, so every lookup tests `is not None`.
# --------------------------------------------------------------------------- #

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def parse_xml(path: Path, findings: list[Finding]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(Finding("ERROR", path, f"is not well-formed XML: {exc}"))
        return None
    except OSError as exc:
        findings.append(Finding("ERROR", path, f"could not be read: {exc}"))
        return None


def child(element: ET.Element, name: str) -> ET.Element | None:
    """First direct child called `name`, namespace-agnostic. Never uses `or`."""
    found = element.find(f"{{{NS}}}{name}")
    if found is None:
        found = element.find(name)
    return found


def children(element: ET.Element, name: str) -> list[ET.Element]:
    found = element.findall(f"{{{NS}}}{name}")
    if not found:
        found = element.findall(name)
    return found


def text_of(element: ET.Element, name: str) -> str | None:
    node = child(element, name)
    if node is None:
        return None
    value = node.text
    if value is None:
        return None
    return value.strip()


def is_true(element: ET.Element, name: str) -> bool:
    value = text_of(element, name)
    if value is None:
        return False
    return value.lower() == "true"


def int_of(element: ET.Element, name: str) -> int | None:
    value = text_of(element, name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def files_in(manifest_dir: Path, folder: str, suffix: str) -> list[Path]:
    directory = manifest_dir / folder
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob(f"*{suffix}") if p.is_file())


# --------------------------------------------------------------------------- #
# Check 1 — CallCenter
# --------------------------------------------------------------------------- #

def check_call_centers(manifest_dir: Path, findings: list[Finding]) -> None:
    paths = files_in(manifest_dir, "callCenters", ".xml")
    for path in paths:
        root = parse_xml(path, findings)
        if root is None:
            continue
        if strip_ns(root.tag) != "CallCenter":
            findings.append(
                Finding("ERROR", path, f"root element is <{strip_ns(root.tag)}>, expected <CallCenter>")
            )
            continue

        # api_meta.txt L31465-31481: all three are Required.
        for required in ("displayName", "displayNameLabel", "internalNameLabel"):
            if not text_of(root, required):
                findings.append(
                    Finding("ERROR", path, f"missing required <{required}> (api_meta.txt L31465-31481)")
                )

        sections = children(root, "sections")
        if not sections:
            findings.append(
                Finding(
                    "WARN",
                    path,
                    "has no <sections> block; a contact center retrieved from an org always has at "
                    "least one. Retrieve the live definition rather than hand-authoring it.",
                )
            )
        seen_section_names: set[str] = set()
        for section in sections:
            label = text_of(section, "label")
            name = text_of(section, "name")
            # api_meta.txt L31501-31520: label and name are Required on a section.
            if not label or not name:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        "a <sections> block is missing a required <label> or <name> "
                        "(api_meta.txt L31501-31520)",
                    )
                )
            if name:
                if name in seen_section_names:
                    findings.append(
                        Finding("ERROR", path, f"duplicate section name '{name}'")
                    )
                seen_section_names.add(name)

            seen_item_names: set[str] = set()
            for item in children(section, "items"):
                # api_meta.txt L31522-31551: label, name and value are all Required.
                missing = [
                    field
                    for field in ("label", "name", "value")
                    if text_of(item, field) is None
                ]
                if missing:
                    findings.append(
                        Finding(
                            "ERROR",
                            path,
                            f"section '{name or '?'}' has an <items> block missing "
                            f"{', '.join('<' + m + '>' for m in missing)} "
                            "(api_meta.txt L31522-31551)",
                        )
                    )
                item_name = text_of(item, "name")
                if item_name:
                    if item_name in seen_item_names:
                        findings.append(
                            Finding(
                                "ERROR",
                                path,
                                f"section '{name or '?'}' has duplicate item name '{item_name}'",
                            )
                        )
                    seen_item_names.add(item_name)

        # api_meta.txt L31603-31619: handler/fallback values are org-specific IDs
        # carrying "Don't change the value in this field".
        for channel in children(root, "contactCenterChannels"):
            for guarded in (
                "voiceMailHandler",
                "voiceMailFallbackQueue",
                "omniCallbackHandler",
                "omniCallbackFallbackQueue",
            ):
                if text_of(channel, guarded):
                    findings.append(
                        Finding(
                            "WARN",
                            path,
                            f"<contactCenterChannels> sets <{guarded}>. The guide says \"Don't change "
                            "the value in this field. Instead, configure routing in Lightning "
                            "Experience\" (api_meta.txt L31575-31619) — these are org-specific IDs, so "
                            "a sandbox value deployed to production points at the wrong record.",
                        )
                    )


# --------------------------------------------------------------------------- #
# Check 2 — ConversationVendorInfo
# --------------------------------------------------------------------------- #

def check_vendor_info(manifest_dir: Path, findings: list[Finding]) -> None:
    paths = files_in(manifest_dir, "ConversationVendorInformation", ".xml")
    for path in paths:
        root = parse_xml(path, findings)
        if root is None:
            continue
        if strip_ns(root.tag) != "ConversationVendorInfo":
            findings.append(
                Finding(
                    "ERROR",
                    path,
                    f"root element is <{strip_ns(root.tag)}>, expected <ConversationVendorInfo>",
                )
            )
            continue

        vendor_type = text_of(root, "vendorType")
        if vendor_type is None:
            findings.append(
                Finding(
                    "ERROR",
                    path,
                    "missing <vendorType>; one of "
                    f"{', '.join(sorted(VENDOR_TYPES))} is required (api_meta.txt L39028-39034)",
                )
            )
        elif vendor_type not in VENDOR_TYPES:
            findings.append(
                Finding(
                    "ERROR",
                    path,
                    f"<vendorType>{vendor_type}</vendorType> is not a documented value. "
                    f"Valid values: {', '.join(sorted(VENDOR_TYPES))} (api_meta.txt L39028-39034)",
                )
            )

        if vendor_type == "Amazon_Connect":
            for field in PARTNER_ONLY_FIELDS:
                if text_of(root, field):
                    findings.append(
                        Finding(
                            "WARN",
                            path,
                            f"<{field}> is set but the guide scopes it to Partner Telephony / BYOC "
                            "implementations, not to Service Cloud Voice with Amazon Connect "
                            "(api_meta.txt L38708-39010)",
                        )
                    )
            master_label = text_of(root, "masterLabel")
            if master_label and master_label != "Service Cloud Voice":
                findings.append(
                    Finding(
                        "WARN",
                        path,
                        f"<masterLabel>{master_label}</masterLabel>: \"For Service Cloud Voice with "
                        "Amazon Connect, this field is always set to Service Cloud Voice\" "
                        "(api_meta.txt L38863-38864)",
                    )
                )
        elif vendor_type in PARTNER_VENDOR_TYPES:
            for field in AMAZON_ONLY_FIELDS:
                if text_of(root, field):
                    findings.append(
                        Finding(
                            "WARN",
                            path,
                            f"<{field}> applies only to Service Cloud Voice with Amazon Connect "
                            f"but vendorType is {vendor_type} (api_meta.txt L38684-38706)",
                        )
                    )
            if not text_of(root, "connectorUrl"):
                findings.append(
                    Finding(
                        "WARN",
                        path,
                        f"vendorType {vendor_type} has no <connectorUrl>; the guide describes it as "
                        "\"The URL that hosts your Service Cloud Voice or Bring Your Own Channel for "
                        "CCaaS connector\" for exactly these implementations (api_meta.txt L38759-38766)",
                    )
                )

        for field, why in DEPRECATED_CVI_FIELDS.items():
            if child(root, field) is not None:
                findings.append(Finding("ERROR", path, f"<{field}> is {why}"))

        auth_mode = text_of(root, "clientAuthMode")
        if auth_mode is not None and auth_mode not in CLIENT_AUTH_MODES:
            findings.append(
                Finding(
                    "ERROR",
                    path,
                    f"<clientAuthMode>{auth_mode}</clientAuthMode> is not a documented value. "
                    f"Valid values: {', '.join(sorted(CLIENT_AUTH_MODES))} (api_meta.txt L38739-38755)",
                )
            )

        # api_meta.txt L38660-38672: agentSSOSupported=true needs namedCredentialSupported=true
        # plus the service_cloud_voice.PartnerSSO interface in the integration class.
        if is_true(root, "agentSSOSupported"):
            if not is_true(root, "namedCredentialSupported"):
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        "agentSSOSupported is true but namedCredentialSupported is not; the guide "
                        "requires both to be true to use Salesforce as the IdP "
                        "(api_meta.txt L38660-38672)",
                    )
                )
            if not text_of(root, "integrationClass"):
                findings.append(
                    Finding(
                        "WARN",
                        path,
                        "agentSSOSupported is true but no <integrationClass> is set; the SSO path "
                        "requires the service_cloud_voice.PartnerSSO interface to be implemented "
                        "there (api_meta.txt L38660-38672)",
                    )
                )
        # api_meta.txt L38963-38973
        if is_true(root, "universalCallRecordingAccessSupported") and not text_of(
            root, "integrationClass"
        ):
            findings.append(
                Finding(
                    "WARN",
                    path,
                    "universalCallRecordingAccessSupported is true but no <integrationClass> is set; "
                    "the service_cloud_voice.RecordingMediaProvider interface has to live in one "
                    "(api_meta.txt L38963-38973)",
                )
            )


# --------------------------------------------------------------------------- #
# Check 3 — ServiceChannel and ACW
# --------------------------------------------------------------------------- #

def check_service_channels(
    manifest_dir: Path, findings: list[Finding]
) -> set[str]:
    """Return the set of API names of Voice service channels found."""
    voice_channels: set[str] = set()
    paths = files_in(manifest_dir, "serviceChannels", ".xml")
    if not paths:
        return voice_channels

    for path in paths:
        root = parse_xml(path, findings)
        if root is None:
            continue
        if strip_ns(root.tag) != "ServiceChannel":
            continue

        api_name = path.name.split(".")[0]
        # api_meta.txt L107858: Required, and the element is relatedEntityType.
        related = text_of(root, "relatedEntityType")
        if related is None:
            if child(root, "relatedEntity") is not None:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        "uses <relatedEntity>; the documented element is <relatedEntityType> "
                        "(api_meta.txt L107858)",
                    )
                )
            else:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        "missing required <relatedEntityType> (api_meta.txt L107858)",
                    )
                )
            continue

        is_voice = related == "VoiceCall"
        if is_voice:
            voice_channels.add(api_name)

        has_timer = is_true(root, "hasAfterConvoWorkTimer")
        # The guide spells the max-time element two ways (api_meta.txt L107784 vs
        # L107832). Accept either; flag only a genuinely absent value.
        max_time = int_of(root, "afterConvoMaxTime")
        if max_time is None:
            max_time = int_of(root, "afterConvoWorkMaxTime")

        if has_timer:
            if not is_voice and related != "MessagingSession":
                findings.append(
                    Finding(
                        "WARN",
                        path,
                        f"After Conversation Work is enabled on a channel whose relatedEntityType is "
                        f"'{related}'. The ACW fields are \"Available only for service channels of "
                        "type Messaging or Voice\" (api_meta.txt L107784-107792)",
                    )
                )
            if max_time is None:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        "hasAfterConvoWorkTimer is true but no max-time value is set; the guide "
                        "requires it (api_meta.txt L107832-107841)",
                    )
                )
            elif not ACW_MIN_SECONDS <= max_time <= ACW_MAX_SECONDS:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        f"ACW max time is {max_time}s; the documented range is "
                        f"{ACW_MIN_SECONDS}-{ACW_MAX_SECONDS} seconds (api_meta.txt L107784-107788)",
                    )
                )
        elif max_time is not None:
            findings.append(
                Finding(
                    "WARN",
                    path,
                    "an ACW max-time value is set but hasAfterConvoWorkTimer is not true, so it has "
                    "no effect (api_meta.txt L107832-107841)",
                )
            )

        if is_true(root, "hasAcwExtensionEnabled"):
            if not has_timer:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        "hasAcwExtensionEnabled requires hasAfterConvoWorkTimer to be true "
                        "(api_meta.txt L107825-107831)",
                    )
                )
            extension = int_of(root, "acwExtensionDuration")
            if extension is None:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        "hasAcwExtensionEnabled is true but <acwExtensionDuration> is missing "
                        "(api_meta.txt L107825-107831)",
                    )
                )
            elif not ACW_MIN_SECONDS <= extension <= ACW_MAX_SECONDS:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        f"acwExtensionDuration is {extension}s; documented range is "
                        f"{ACW_MIN_SECONDS}-{ACW_MAX_SECONDS} (api_meta.txt L107778-107783)",
                    )
                )
            extensions = int_of(root, "maxExtensions")
            if extensions is None:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        "hasAcwExtensionEnabled is true but <maxExtensions> is missing "
                        "(api_meta.txt L107825-107831)",
                    )
                )
            elif not MAX_EXTENSIONS_MIN <= extensions <= MAX_EXTENSIONS_MAX:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        f"maxExtensions is {extensions}; documented range is "
                        f"{MAX_EXTENSIONS_MIN}-{MAX_EXTENSIONS_MAX} (api_meta.txt L107852-107856)",
                    )
                )

    if not voice_channels:
        findings.append(
            Finding(
                "ERROR",
                manifest_dir / "serviceChannels",
                "no ServiceChannel with <relatedEntityType>VoiceCall</relatedEntityType> found. "
                "Service Cloud Voice routes through an Omni-Channel Voice service channel; without "
                "one, calls have nowhere to be queued.",
            )
        )
    return voice_channels


# --------------------------------------------------------------------------- #
# Check 4 — presence statuses and presence configurations
# --------------------------------------------------------------------------- #

def check_presence(
    manifest_dir: Path, voice_channels: set[str], findings: list[Finding]
) -> None:
    status_paths = files_in(manifest_dir, "servicePresenceStatuses", ".xml")
    voice_status_found = False

    for path in status_paths:
        root = parse_xml(path, findings)
        if root is None:
            continue
        if strip_ns(root.tag) != "ServicePresenceStatus":
            continue

        assigned = [
            text_of(block, "channel")
            for block in children(root, "channels")
        ]
        assigned = [name for name in assigned if name]
        if not assigned:
            findings.append(
                Finding(
                    "WARN",
                    path,
                    "has no <channels>/<channel>. \"If no service channels are included, the presence "
                    "status is automatically marked as 'Away'\" (api_meta.txt L107966-107970), so an "
                    "agent in this status is never routed work.",
                )
            )
            continue
        if voice_channels and any(name in voice_channels for name in assigned):
            voice_status_found = True
        elif voice_channels:
            unknown = [name for name in assigned if name not in voice_channels]
            del unknown  # non-voice statuses are legitimate; nothing to report

    if status_paths and voice_channels and not voice_status_found:
        findings.append(
            Finding(
                "ERROR",
                manifest_dir / "servicePresenceStatuses",
                "no ServicePresenceStatus references a Voice service channel "
                f"({', '.join(sorted(voice_channels))}). Agents can be online and still never "
                "receive a call (api_meta.txt L107966-107973).",
            )
        )

    for path in files_in(manifest_dir, "presenceUserConfigs", ".xml"):
        root = parse_xml(path, findings)
        if root is None:
            continue
        if strip_ns(root.tag) != "PresenceUserConfig":
            continue

        capacity = int_of(root, "capacity")
        if capacity is None:
            findings.append(
                Finding(
                    "ERROR",
                    path,
                    "missing required <capacity> (api_meta.txt L96998-97001)",
                )
            )
        elif capacity <= 0:
            findings.append(
                Finding(
                    "ERROR",
                    path,
                    f"<capacity>{capacity}</capacity> leaves no room for work to be routed",
                )
            )

        # api_meta.txt L97004-97012: each is available only if the other is false.
        if is_true(root, "enableAutoAccept") and is_true(root, "enableDecline"):
            findings.append(
                Finding(
                    "ERROR",
                    path,
                    "enableAutoAccept and enableDecline are both true; each is \"Available only if\" "
                    "the other is false (api_meta.txt L97004-97012)",
                )
            )
        if is_true(root, "enableDeclineReason") and not is_true(root, "enableDecline"):
            findings.append(
                Finding(
                    "WARN",
                    path,
                    "enableDeclineReason is true but enableDecline is not; decline reasons \"can be "
                    "selected only if decline reasons are enabled\" (api_meta.txt L97021-97024)",
                )
            )


# --------------------------------------------------------------------------- #
# Check 5 — permission sets
# --------------------------------------------------------------------------- #

def check_permission_sets(manifest_dir: Path, findings: list[Finding]) -> None:
    paths = files_in(manifest_dir, "permissionsets", ".xml")
    if not paths:
        return

    grants_voice_call = False
    for path in paths:
        root = parse_xml(path, findings)
        if root is None:
            continue
        if strip_ns(root.tag) != "PermissionSet":
            continue

        for block in children(root, "userPermissions"):
            name = text_of(block, "name")
            if name is None:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        "a <userPermissions> block has no <name>; both <enabled> and <name> are "
                        "Required (api_meta.txt L95170-95179)",
                    )
                )
                continue
            if child(block, "enabled") is None:
                findings.append(
                    Finding(
                        "ERROR",
                        path,
                        f"<userPermissions> '{name}' has no <enabled>; it is Required "
                        "(api_meta.txt L95170-95179)",
                    )
                )
            lowered = name.lower()
            if "voice" in lowered or "callcenter" in lowered or "contactcenter" in lowered:
                findings.append(
                    Finding(
                        "WARN",
                        path,
                        f"<userPermissions> names '{name}'. No catalogue of permission API names is "
                        "published in the grounded sources, so this string cannot be verified here. "
                        "Confirm it against a permission set retrieved from the org before deploying "
                        "— an unknown name fails the deploy outright.",
                    )
                )

        for block in children(root, "objectPermissions"):
            obj = text_of(block, "object")
            if obj == "VoiceCall":
                grants_voice_call = True
                if is_true(block, "allowDelete"):
                    findings.append(
                        Finding(
                            "WARN",
                            path,
                            "grants allowDelete on VoiceCall. \"Only users with the Modify All Data "
                            "permission can delete call records\" (object_reference.txt L306747), so "
                            "this either does nothing or implies an over-broad grant elsewhere.",
                        )
                    )
            if obj == "VoiceCallRecording" and is_true(block, "allowDelete"):
                findings.append(
                    Finding(
                        "WARN",
                        path,
                        "grants allowDelete on VoiceCallRecording. For Amazon Connect the audio lives "
                        "in S3 on your AWS account (object_reference.txt L308341-308343); deleting the "
                        "Salesforce row removes the link, not the recording.",
                    )
                )

    if not grants_voice_call:
        findings.append(
            Finding(
                "WARN",
                manifest_dir / "permissionsets",
                "no permission set in this manifest grants object access to VoiceCall. Agents may be "
                "relying on the standard Salesforce Voice Contact Center Rep / Admin sets "
                "(object_reference.txt L306746-306750), which are not source-controlled — record that "
                "assignment somewhere the release can verify.",
            )
        )


# --------------------------------------------------------------------------- #
# Check 6 — org settings
# --------------------------------------------------------------------------- #

def check_settings(manifest_dir: Path, findings: list[Finding]) -> None:
    settings_dir = manifest_dir / "settings"
    if not settings_dir.is_dir():
        return

    scv = next(iter(sorted(settings_dir.glob("ServiceCloudVoice.settings*"))), None)
    if scv is not None:
        root = parse_xml(scv, findings)
        if root is not None:
            for element in list(root):
                name = strip_ns(element.tag)
                if name in DIALER_SETTINGS_FIELDS:
                    findings.append(
                        Finding(
                            "ERROR",
                            scv,
                            f"<{name}> belongs to VoiceSettings (Sales Dialer, api_meta.txt "
                            "L128675-128712), not ServiceCloudVoiceSettings",
                        )
                    )
                elif name not in SCV_SETTINGS_FIELDS:
                    findings.append(
                        Finding(
                            "WARN",
                            scv,
                            f"<{name}> is not in the documented ServiceCloudVoiceSettings field list "
                            "(api_meta.txt L126818-126900); verify it against the target API version",
                        )
                    )
            if not is_true(root, "enableServiceCloudVoice") and not is_true(
                root, "enableSCVExternalTelephony"
            ):
                findings.append(
                    Finding(
                        "WARN",
                        scv,
                        "neither enableServiceCloudVoice (Amazon Connect) nor "
                        "enableSCVExternalTelephony (Partner Telephony) is true; the feature stays "
                        "off (api_meta.txt L126885-126900)",
                    )
                )

    my_domain = next(iter(sorted(settings_dir.glob("MyDomain.settings*"))), None)
    if my_domain is not None:
        root = parse_xml(my_domain, findings)
        if root is not None and is_true(root, "isFirstPartyCookieUseRequired"):
            findings.append(
                Finding(
                    "ERROR",
                    my_domain,
                    "isFirstPartyCookieUseRequired is true. \"Service Cloud Voice with Amazon Connect "
                    "and Service Cloud Voice with Partner Telephony from Amazon Connect aren't "
                    "compatible with this setting. If you use those features, set "
                    "isFirstPartyCookieUseRequired to false\" (api_meta.txt L122293-122299)",
                )
            )


# --------------------------------------------------------------------------- #

def run_checks(manifest_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not manifest_dir.exists():
        findings.append(
            Finding("ERROR", manifest_dir, "manifest directory not found")
        )
        return findings

    check_call_centers(manifest_dir, findings)
    check_vendor_info(manifest_dir, findings)
    voice_channels = check_service_channels(manifest_dir, findings)
    check_presence(manifest_dir, voice_channels, findings)
    check_permission_sets(manifest_dir, findings)
    check_settings(manifest_dir, findings)
    return findings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    findings = run_checks(manifest_dir)

    errors = [f for f in findings if f.level == "ERROR"]
    warnings = [f for f in findings if f.level == "WARN"]

    for finding in errors:
        print(str(finding), file=sys.stderr)
    for finding in warnings:
        print(str(finding), file=sys.stderr)

    if not findings:
        print(f"No issues found in {manifest_dir}.")
        return 0

    print(
        f"{len(errors)} error(s), {len(warnings)} warning(s) in {manifest_dir}.",
        file=sys.stderr,
    )
    if errors and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
