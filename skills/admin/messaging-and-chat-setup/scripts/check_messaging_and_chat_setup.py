#!/usr/bin/env python3
"""Checker for Messaging for In-App and Web (MIAW) configuration metadata.

Inspects a retrieved Salesforce metadata tree for the shape errors that the
Metadata API Developer Guide (v62) says will either fail the deploy or, worse,
deploy cleanly and do nothing.

Checks performed:
  1. MessagingChannel required fields and enum values (messagingChannelType,
     sessionHandlerType), and routing-pointer coherence between
     sessionHandlerType / sessionHandlerFlow / sessionHandlerQueue.
  2. MessagingChannel routing targets resolve inside the manifest when the
     sibling Omni-Channel artefacts (queues, flows) were retrieved with it.
  3. MessagingChannel automated responses: enum, content-type pairing, and
     responseTimeoutInMins inside the documented 5-60 range.
  4. EmbeddedServiceConfig required fields (masterLabel, site), deploymentFeature
     for MIAW, and that its messagingChannel / site / branding references
     resolve inside the manifest.
  5. Pre-chat form field shape rules (isHidden implies displayOrder -1,
     isRequired false, and a Custom parameter type).
  6. CspTrustedSite records that grant nothing (every directive false) and
     CorsWhitelistOrigin patterns with a misplaced wildcard or no scheme.
  7. Legacy Chat metadata present alongside MIAW metadata, including
     EmbeddedServiceBranding, which does not apply to MIAW.
  8. package.xml using the * wildcard for EmbeddedServiceConfig, which the
     guide says the type does not support.

Grounding, Metadata API Developer Guide v62 (api_meta.pdf):
  MessagingChannel                          p.1589-1601
  EmbeddedServiceConfig / form subtypes     p.1027-1037
  EmbeddedServiceBranding (legacy only)     p.1025
  CorsWhitelistOrigin / CspTrustedSite      p.710-714

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_messaging_and_chat_setup.py --manifest-dir force-app/main/default
    python3 check_messaging_and_chat_setup.py --manifest-dir . --warnings-as-errors
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# --- Documented enum values (api_meta.pdf) ---------------------------------

MESSAGING_CHANNEL_TYPES = {
    "AppleMessagesForBusiness",
    "Custom",
    "EmbeddedMessaging",
    "Facebook",
    "Line",
    "PstnVoice",
    "Text",
    "SipVoice",
    "Voice",
    "WhatsApp",
    "WhatsAppVoice",
}

# Channel types whose MessagingChannel metadata Salesforce says is not the
# provisioning path (guide: "Third-party Messaging channels in Salesforce,
# such as WhatsApp and Facebook Messenger, don't use this metadata type").
THIRD_PARTY_CHANNEL_TYPES = {"WhatsApp", "WhatsAppVoice", "Facebook", "Line", "Text"}

SESSION_HANDLER_TYPES = {"AgentforceServiceAgent", "Flow", "Queue", "User"}

AUTO_RESPONSE_TYPES = {
    "AgentEndEngagementResponse",
    "AgentEngagedResponse",
    "CustomResponse",
    "DoubleOptInPrompt",
    "EndUserIdleResponse",
    "EndUserInactiveResponse",
    "HelpResponse",
    "InitialResponse",
    "OptInConfirmation",
    "OptInPrompt",
    "OptOutConfirmation",
}

AUTO_RESPONSE_CONTENT_TYPES = {"TextResponse", "MessageDefinition"}

DEPLOYMENT_FEATURES = {"EmbeddedMessaging", "Flows", "FieldService", "LiveAgent", "None"}
DEPLOYMENT_TYPES = {"Mobile", "Web", "API"}

CSP_GRANT_FIELDS = (
    "isApplicableToConnectSrc",
    "isApplicableToFontSrc",
    "isApplicableToFrameSrc",
    "isApplicableToImgSrc",
    "isApplicableToMediaSrc",
    "isApplicableToStyleSrc",
    "canAccessCamera",
    "canAccessMicrophone",
)

# Root tag -> friendly name, for files we care about.
INTERESTING_ROOTS = {
    "MessagingChannel",
    "EmbeddedServiceConfig",
    "EmbeddedServiceBranding",
    "BrandingSet",
    "CorsWhitelistOrigin",
    "CspTrustedSite",
    "Queue",
    "Flow",
    "Network",
    "CustomSite",
    "LiveChatButton",
    "LiveChatDeployment",
    "LiveChatAgentConfig",
    "EmbeddedServiceLiveAgent",
    "Package",
}

RESPONSE_TEXT_MAX = 1000  # sanity ceiling only; see note in report_findings()


# --- XML helpers -----------------------------------------------------------


def strip_ns(tag: str) -> str:
    """Strip an XML namespace from a tag string."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def child(element: ET.Element, tag: str) -> ET.Element | None:
    """Return the first direct child with this local tag, or None.

    Never rely on the truthiness of an Element: an element with no children is
    falsy even when it exists. Always compare against None.
    """
    for node in element:
        if strip_ns(node.tag) == tag:
            return node
    return None


def child_text(element: ET.Element, tag: str) -> str | None:
    """Return the stripped text of the first matching child, or None."""
    node = child(element, tag)
    if node is None:
        return None
    return (node.text or "").strip()


def children(element: ET.Element, tag: str) -> list[ET.Element]:
    """Return every direct child with this local tag."""
    return [node for node in element if strip_ns(node.tag) == tag]


def first_present(element: ET.Element, *tags: str) -> str | None:
    """Return the text of the first of these tags that is present."""
    for tag in tags:
        node = child(element, tag)
        if node is not None:
            return (node.text or "").strip()
    return None


def is_true(value: str | None) -> bool:
    return value is not None and value.strip().lower() == "true"


# --- Loading ---------------------------------------------------------------


class Component:
    __slots__ = ("path", "root", "tag", "name")

    def __init__(self, path: Path, root: ET.Element) -> None:
        self.path = path
        self.root = root
        self.tag = strip_ns(root.tag)
        # Metadata API files are named by the component's developer name; the
        # source-format "-meta.xml" tail and the type suffix are both noise.
        stem = path.name
        for tail in ("-meta.xml", ".xml"):
            if stem.endswith(tail):
                stem = stem[: -len(tail)]
        if "." in stem:
            stem = stem.rsplit(".", 1)[0]
        self.name = stem


def load_components(manifest_dir: Path) -> list[Component]:
    """Parse every file under manifest_dir whose root tag we recognise."""
    components: list[Component] = []
    for path in sorted(manifest_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.stat().st_size > 5_000_000:
            continue
        try:
            root = ET.parse(path).getroot()
        except (ET.ParseError, OSError, UnicodeDecodeError):
            continue
        if strip_ns(root.tag) in INTERESTING_ROOTS:
            components.append(Component(path, root))
    return components


def by_tag(components: list[Component], tag: str) -> list[Component]:
    return [c for c in components if c.tag == tag]


def names_of(components: list[Component], tag: str) -> set[str]:
    return {c.name for c in by_tag(components, tag)}


# --- Checks ----------------------------------------------------------------


def check_messaging_channels(
    components: list[Component], errors: list[str], warnings: list[str]
) -> None:
    channels = by_tag(components, "MessagingChannel")
    queue_names = names_of(components, "Queue")
    flow_names = names_of(components, "Flow")
    have_queues = bool(queue_names)
    have_flows = bool(flow_names)

    for comp in channels:
        where = comp.path.name
        root = comp.root

        label = child_text(root, "masterLabel")
        if not label:
            errors.append(f"{where}: MessagingChannel has no masterLabel; the field is Required.")

        channel_type = child_text(root, "messagingChannelType")
        if not channel_type:
            errors.append(
                f"{where}: MessagingChannel has no messagingChannelType; the field is Required. "
                f"For web and in-app chat use EmbeddedMessaging."
            )
        elif channel_type not in MESSAGING_CHANNEL_TYPES:
            errors.append(
                f"{where}: messagingChannelType '{channel_type}' is not a documented value. "
                f"Valid values: {', '.join(sorted(MESSAGING_CHANNEL_TYPES))}."
            )
        elif channel_type in THIRD_PARTY_CHANNEL_TYPES:
            warnings.append(
                f"{where}: messagingChannelType is '{channel_type}'. The Metadata API guide states "
                f"that third-party Messaging channels such as WhatsApp and Facebook Messenger do not "
                f"use this metadata type; confirm the provisioning path before relying on this file."
            )

        handler_type = child_text(root, "sessionHandlerType")
        if not handler_type:
            errors.append(
                f"{where}: MessagingChannel has no sessionHandlerType; the field is Required. "
                f"Valid values: {', '.join(sorted(SESSION_HANDLER_TYPES))}."
            )
        elif handler_type not in SESSION_HANDLER_TYPES:
            errors.append(
                f"{where}: sessionHandlerType '{handler_type}' is not a documented value. "
                f"Valid values: {', '.join(sorted(SESSION_HANDLER_TYPES))}."
            )

        handler_queue = child_text(root, "sessionHandlerQueue")
        handler_flow = child_text(root, "sessionHandlerFlow")
        handler_user = child_text(root, "sessionHandlerUser")

        if not handler_queue:
            errors.append(
                f"{where}: MessagingChannel has no sessionHandlerQueue. The field is Required, and "
                f"when sessionHandlerFlow is set it is also the fallback queue for sessions the flow "
                f"cannot route."
            )

        if handler_type == "Flow" and not handler_flow:
            errors.append(
                f"{where}: sessionHandlerType is Flow but sessionHandlerFlow is empty; nothing will "
                f"route the session."
            )
        if handler_type == "Queue" and handler_flow:
            warnings.append(
                f"{where}: sessionHandlerType is Queue but sessionHandlerFlow names '{handler_flow}'. "
                f"The flow is ignored; set sessionHandlerType to Flow or remove the pointer."
            )
        if handler_type == "User" and not handler_user:
            errors.append(
                f"{where}: sessionHandlerType is User but sessionHandlerUser is empty."
            )

        # Resolve routing pointers only when the sibling metadata is in the tree,
        # so a channel-only package does not produce false alarms.
        if handler_queue and have_queues and handler_queue not in queue_names:
            errors.append(
                f"{where}: sessionHandlerQueue '{handler_queue}' does not match any Queue in the "
                f"manifest. Deploy the queue from admin/omni-channel-routing-setup first, or add it "
                f"to this package."
            )
        if handler_flow and have_flows and handler_flow not in flow_names:
            errors.append(
                f"{where}: sessionHandlerFlow '{handler_flow}' does not match any Flow in the manifest."
            )
        if handler_queue and not have_queues:
            warnings.append(
                f"{where}: sessionHandlerQueue '{handler_queue}' could not be verified - no Queue "
                f"metadata was retrieved alongside this channel. Confirm the queue exists in the "
                f"target org and has a routing configuration and members."
            )

        check_automated_responses(comp, errors, warnings)


def check_automated_responses(
    comp: Component, errors: list[str], warnings: list[str]
) -> None:
    where = comp.path.name
    seen_types: set[str] = set()

    for response in children(comp.root, "automatedResponses"):
        rtype = child_text(response, "type")
        content_type = child_text(response, "autoResponseContentType")
        text = child_text(response, "response")
        definition = child_text(response, "messageDefinitionName")
        timeout = child_text(response, "responseTimeoutInMins")

        if not rtype:
            errors.append(f"{where}: an automatedResponses entry has no type; the field is Required.")
        elif rtype not in AUTO_RESPONSE_TYPES:
            errors.append(
                f"{where}: automatedResponses type '{rtype}' is not a documented value. "
                f"Valid values: {', '.join(sorted(AUTO_RESPONSE_TYPES))}."
            )
        else:
            if rtype in seen_types:
                warnings.append(
                    f"{where}: automatedResponses type '{rtype}' appears more than once for this "
                    f"channel; only one will be used per language."
                )
            seen_types.add(rtype)

        if content_type and content_type not in AUTO_RESPONSE_CONTENT_TYPES:
            errors.append(
                f"{where}: autoResponseContentType '{content_type}' is not TextResponse or "
                f"MessageDefinition."
            )
        if content_type == "TextResponse":
            if not text:
                errors.append(
                    f"{where}: automatedResponses '{rtype or 'unknown'}' is a TextResponse with no "
                    f"response text."
                )
            elif len(text) > RESPONSE_TEXT_MAX:
                warnings.append(
                    f"{where}: automatedResponses '{rtype or 'unknown'}' response text is "
                    f"{len(text)} characters. No maximum is documented in the Metadata API guide, "
                    f"but text this long is not readable in a chat bubble - confirm against the org."
                )
            if not child_text(response, "language"):
                warnings.append(
                    f"{where}: automatedResponses '{rtype or 'unknown'}' is a TextResponse with no "
                    f"language; set one (for example en_US) so the right response is selected."
                )
        if content_type == "MessageDefinition" and not definition:
            errors.append(
                f"{where}: automatedResponses '{rtype or 'unknown'}' is a MessageDefinition with no "
                f"messageDefinitionName."
            )

        if timeout:
            try:
                minutes = int(timeout)
            except ValueError:
                errors.append(
                    f"{where}: responseTimeoutInMins '{timeout}' is not an integer."
                )
            else:
                if not 5 <= minutes <= 60:
                    errors.append(
                        f"{where}: responseTimeoutInMins is {minutes}. The documented range is 5 to 60."
                    )


def check_embedded_service_configs(
    components: list[Component], errors: list[str], warnings: list[str]
) -> None:
    configs = by_tag(components, "EmbeddedServiceConfig")
    channel_names = names_of(components, "MessagingChannel")
    branding_names = names_of(components, "BrandingSet")
    site_names = names_of(components, "Network") | names_of(components, "CustomSite")

    for comp in configs:
        where = comp.path.name
        root = comp.root

        if not child_text(root, "masterLabel"):
            errors.append(
                f"{where}: EmbeddedServiceConfig has no masterLabel; the field is Required."
            )

        site = child_text(root, "site")
        if not site:
            errors.append(
                f"{where}: EmbeddedServiceConfig has no site. The field is Required - a deployment "
                f"must name the Experience site or website it belongs to."
            )
        elif site_names and site not in site_names:
            warnings.append(
                f"{where}: site '{site}' does not match any Network or CustomSite in the manifest. "
                f"Deploy the site first (admin/experience-cloud-site-setup)."
            )

        feature = child_text(root, "deploymentFeature")
        if feature and feature not in DEPLOYMENT_FEATURES:
            errors.append(
                f"{where}: deploymentFeature '{feature}' is not a documented value. "
                f"Valid values: {', '.join(sorted(DEPLOYMENT_FEATURES))}."
            )
        if feature == "LiveAgent" and channel_names:
            errors.append(
                f"{where}: deploymentFeature is LiveAgent while MessagingChannel metadata is present "
                f"in the same package. A MIAW deployment must use EmbeddedMessaging; a legacy Chat "
                f"deployment cannot be converted."
            )

        dtype = child_text(root, "deploymentType")
        if dtype and dtype not in DEPLOYMENT_TYPES:
            errors.append(
                f"{where}: deploymentType '{dtype}' is not a documented value. "
                f"Valid values: {', '.join(sorted(DEPLOYMENT_TYPES))}."
            )
        if dtype == "Mobile":
            warnings.append(
                f"{where}: deploymentType is Mobile, which the Metadata API guide marks 'For future "
                f"use'. A website deployment should be Web."
            )

        branding = child_text(root, "branding")
        if branding and branding_names and branding not in branding_names:
            warnings.append(
                f"{where}: branding '{branding}' does not match any BrandingSet in the manifest."
            )

        block = child(root, "embeddedServiceMessagingChannel")
        if feature == "EmbeddedMessaging" and block is None:
            errors.append(
                f"{where}: deploymentFeature is EmbeddedMessaging but there is no "
                f"embeddedServiceMessagingChannel block, so no messaging channel is bound to this "
                f"deployment."
            )
        if block is not None:
            required_in_block = (
                "isEnabled",
                "messagingChannel",
                "shouldShowDeliveryReceipts",
                "shouldShowEmojiSelection",
                "shouldShowReadReceipts",
                "shouldShowTypingIndicators",
                "shouldStartNewLineOnEnter",
            )
            missing = [tag for tag in required_in_block if child(block, tag) is None]
            if missing:
                errors.append(
                    f"{where}: embeddedServiceMessagingChannel is missing Required field(s): "
                    f"{', '.join(missing)}. Every field in this block is Required, so a partial edit "
                    f"fails the deploy."
                )
            bound = child_text(block, "messagingChannel")
            if bound and channel_names and bound not in channel_names:
                errors.append(
                    f"{where}: embeddedServiceMessagingChannel/messagingChannel '{bound}' does not "
                    f"match any MessagingChannel in the manifest."
                )
            if child(block, "isEnabled") is not None and not is_true(
                child_text(block, "isEnabled")
            ):
                warnings.append(
                    f"{where}: embeddedServiceMessagingChannel/isEnabled is not true; the deployment "
                    f"will render nothing."
                )

        check_prechat_form(comp, errors, warnings)


def check_prechat_form(
    comp: Component, errors: list[str], warnings: list[str]
) -> None:
    where = comp.path.name
    for form in children(comp.root, "embeddedServiceForms"):
        context = child_text(form, "displayContext")
        if not context:
            errors.append(
                f"{where}: embeddedServiceForms has no displayContext; the field is Required "
                f"(Session or Conversation)."
            )
        elif context == "None":
            warnings.append(
                f"{where}: embeddedServiceForms displayContext is None. The Metadata API guide says "
                f"of this value: \"Don't select this option.\""
            )
        elif context not in {"Session", "Conversation"}:
            errors.append(
                f"{where}: embeddedServiceForms displayContext '{context}' is not a documented value."
            )

        if child(form, "isActive") is None or not is_true(child_text(form, "isActive")):
            warnings.append(
                f"{where}: embeddedServiceForms isActive is not true (it defaults to false), so the "
                f"pre-chat form collects nothing."
            )

        orders: list[str] = []
        for field in children(form, "embeddedServiceFormFields"):
            name = child_text(field, "formField") or "(unnamed)"
            param_type = child_text(field, "messagingChannelParameterType")
            hidden = is_true(child_text(field, "isHidden"))
            required = is_true(child_text(field, "isRequired"))
            order = child_text(field, "displayOrder")

            for tag in ("formField", "messagingChannelParameterType", "formFieldType"):
                if child(field, tag) is None:
                    errors.append(
                        f"{where}: pre-chat field '{name}' has no {tag}; the field is Required."
                    )

            if hidden:
                if order != "-1":
                    errors.append(
                        f"{where}: pre-chat field '{name}' has isHidden true, so displayOrder must be "
                        f"-1 (found '{order}')."
                    )
                if required:
                    errors.append(
                        f"{where}: pre-chat field '{name}' has isHidden true, so isRequired must be "
                        f"false."
                    )
                if param_type != "Custom":
                    errors.append(
                        f"{where}: pre-chat field '{name}' has isHidden true, which is only allowed "
                        f"for a Custom messagingChannelParameterType (found '{param_type}')."
                    )
            else:
                if order is not None and order.lstrip("-").isdigit() and int(order) < 0:
                    errors.append(
                        f"{where}: pre-chat field '{name}' is visible, so displayOrder must be 0 or "
                        f"greater (found '{order}')."
                    )
                if order is not None:
                    orders.append(order)

            if child(field, "choiceList") is not None and param_type != "Custom":
                errors.append(
                    f"{where}: pre-chat field '{name}' has a choiceList, which attaches only to a "
                    f"Custom messagingChannelParameterType."
                )

        duplicates = {o for o in orders if orders.count(o) > 1}
        if duplicates:
            warnings.append(
                f"{where}: pre-chat fields share displayOrder value(s) "
                f"{', '.join(sorted(duplicates))}; field order will be arbitrary."
            )


def check_trusted_sites(
    components: list[Component], errors: list[str], warnings: list[str]
) -> None:
    for comp in by_tag(components, "CspTrustedSite"):
        where = comp.path.name
        root = comp.root
        endpoint = child_text(root, "endpointUrl")
        if not endpoint:
            errors.append(f"{where}: CspTrustedSite has no endpointUrl; the field is Required.")
        elif "{" in endpoint or "^" in endpoint or " " in endpoint:
            errors.append(
                f"{where}: endpointUrl '{endpoint}' looks malformed. Malformed URLs are excluded "
                f"from the generated CSP header while still appearing in Setup."
            )
        if child(root, "isActive") is not None and not is_true(child_text(root, "isActive")):
            warnings.append(f"{where}: CspTrustedSite isActive is false; it grants nothing.")

        granted = [tag for tag in CSP_GRANT_FIELDS if is_true(child_text(root, tag))]
        if not granted:
            errors.append(
                f"{where}: CspTrustedSite has no directive set to true. Every isApplicableTo* field "
                f"defaults to false, and API 59.0+ requires at least one isApplicable* or canAccess* "
                f"field to be true. As deployed, this record allows nothing."
            )

        context = child_text(root, "context")
        if context == "LEX":
            warnings.append(
                f"{where}: CspTrustedSite context is LEX, which covers Lightning Experience pages "
                f"only. A widget hosted on an Experience Cloud site needs Communities or All."
            )

    for comp in by_tag(components, "CorsWhitelistOrigin"):
        where = comp.path.name
        pattern = child_text(comp.root, "urlPattern")
        if not pattern:
            errors.append(f"{where}: CorsWhitelistOrigin has no urlPattern.")
            continue
        if pattern.startswith("http://"):
            errors.append(
                f"{where}: urlPattern '{pattern}' uses http. The origin pattern must include the "
                f"HTTPS protocol."
            )
        elif not pattern.startswith(("https://", "chrome-extension://", "moz-extension://")):
            errors.append(
                f"{where}: urlPattern '{pattern}' has no scheme. The origin pattern must include the "
                f"HTTPS protocol and a domain name."
            )
        if "*" in pattern and not pattern.startswith("https://*."):
            errors.append(
                f"{where}: urlPattern '{pattern}' places the wildcard somewhere other than in front "
                f"of a second-level domain name. Only the form https://*.example.com is supported."
            )


def check_legacy_chat(
    components: list[Component], errors: list[str], warnings: list[str]
) -> None:
    miaw_present = bool(names_of(components, "MessagingChannel"))
    legacy_tags = (
        "LiveChatButton",
        "LiveChatDeployment",
        "LiveChatAgentConfig",
        "EmbeddedServiceLiveAgent",
    )
    legacy = [c for c in components if c.tag in legacy_tags]
    if legacy and miaw_present:
        listed = ", ".join(f"{c.tag} ({c.path.name})" for c in legacy)
        warnings.append(
            "Legacy Chat metadata is deployed alongside MIAW metadata: "
            f"{listed}. Legacy Chat writes LiveChatTranscript, not MessagingSession, and the guide "
            "notes that chats routed with Omni-Channel are not supported in the Metadata API. Run "
            "the two in parallel deliberately during cutover, or remove the legacy path."
        )

    for comp in by_tag(components, "EmbeddedServiceBranding"):
        target = child_text(comp.root, "embeddedServiceConfig") or "(unnamed)"
        message = (
            f"{comp.path.name}: EmbeddedServiceBranding targets '{target}'. This type works only "
            f"with the legacy chat products; Messaging for In-App and Web branding uses a BrandingSet "
            f"named by EmbeddedServiceConfig/branding."
        )
        if miaw_present:
            errors.append(message)
        else:
            warnings.append(message)


def check_package_manifest(
    components: list[Component], errors: list[str], warnings: list[str]
) -> None:
    for comp in by_tag(components, "Package"):
        for types_node in children(comp.root, "types"):
            type_name = child_text(types_node, "name")
            members = [(m.text or "").strip() for m in children(types_node, "members")]
            if type_name in {"EmbeddedServiceConfig", "EmbeddedServiceBranding"} and "*" in members:
                errors.append(
                    f"{comp.path.name}: package.xml uses the * wildcard for {type_name}. The "
                    f"Metadata API guide states this type does not support the wildcard, so the "
                    f"retrieve returns nothing for it and reports no error. Name each component."
                )


# --- Orchestration ---------------------------------------------------------


def run_checks(manifest_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not manifest_dir.exists():
        errors.append(f"Manifest directory not found: {manifest_dir}")
        return errors, warnings

    components = load_components(manifest_dir)
    relevant = [
        c
        for c in components
        if c.tag in {"MessagingChannel", "EmbeddedServiceConfig", "CspTrustedSite", "CorsWhitelistOrigin"}
    ]
    if not relevant:
        warnings.append(
            f"No MessagingChannel, EmbeddedServiceConfig, CspTrustedSite or CorsWhitelistOrigin "
            f"metadata found under {manifest_dir}. Retrieve the messaging package before running "
            f"this checker."
        )
        return errors, warnings

    check_messaging_channels(components, errors, warnings)
    check_embedded_service_configs(components, errors, warnings)
    check_trusted_sites(components, errors, warnings)
    check_legacy_chat(components, errors, warnings)
    check_package_manifest(components, errors, warnings)

    channels = names_of(components, "MessagingChannel")
    if channels and not names_of(components, "EmbeddedServiceConfig"):
        warnings.append(
            "MessagingChannel metadata is present with no EmbeddedServiceConfig. A channel with no "
            "deployment renders nothing. EmbeddedServiceConfig does not support the * wildcard, so "
            "check that the manifest names it explicitly."
        )

    cors = len(by_tag(components, "CorsWhitelistOrigin"))
    csp = len(by_tag(components, "CspTrustedSite"))
    if channels and cors and not csp:
        warnings.append(
            f"{cors} CORS origin(s) but no CSP trusted site. The widget needs both: an origin missing "
            f"from CORS gets HTTP 404, and a host missing from CSP has its resources blocked."
        )
    if channels and csp and not cors:
        warnings.append(
            f"{csp} CSP trusted site(s) but no CORS origin. A host missing from the CORS allowlist "
            f"receives HTTP 404 rather than a CORS-labelled error."
        )

    return errors, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Messaging for In-App and Web (MIAW) metadata for shape errors and "
            "silently-ineffective configuration."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the retrieved Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Exit non-zero when only warnings were found.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors, warnings = run_checks(Path(args.manifest_dir))

    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in warnings:
        print(f"WARN:  {message}", file=sys.stderr)

    if not errors and not warnings:
        print("No issues found.")
        return 0

    print(
        f"\n{len(errors)} error(s), {len(warnings)} warning(s).",
        file=sys.stderr,
    )
    if errors:
        return 1
    return 1 if args.warnings_as_errors else 0


if __name__ == "__main__":
    sys.exit(main())
