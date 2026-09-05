# Gotchas — Messaging and Chat Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Line citations are into the Metadata API Developer Guide (`api_meta.pdf`) and Object Reference (`object_reference.pdf`), v62 PDFs.

## Gotcha 1: A Non-Allowlisted Origin Returns HTTP 404, Not a CORS Error

**What happens:** The chat widget never appears. The browser network tab shows a **404** against the Salesforce org endpoint, so the admin concludes the URL in the snippet is wrong and starts editing the snippet. The URL is fine; the origin simply is not on the CORS allowlist.

**When it occurs:** Any request from an origin absent from `CorsWhitelistOrigin`. The guide is explicit: if a browser that supports CORS makes a request to an origin in your allowlist, Salesforce returns the origin in the `Access-Control-Allow-Origin` header — "If the origin isn't allow listed, Salesforce returns HTTP status code 404" (api_meta:39413). It bites hardest on staging and preview hosts that were never registered, and after a host moves to a new subdomain.

**How to avoid:** Register the origin before debugging the snippet. `urlPattern` must carry the HTTPS scheme and a domain, may carry a port, and **does** accept the wildcard `*` — but only "in front of a second-level domain name", so `https://*.example.com` is valid and `https://support.*.com` is not (api_meta:39362–39368). An IP address and a domain resolving to the same address are separate origins and need separate entries (api_meta:39374–39378). Then add the matching `CspTrustedSite` — see gotcha #8, because adding the CSP record alone does nothing.

---

## Gotcha 2: Legacy Chat and MIAW Are Different `deploymentFeature` Values, Not a Setting You Can Flip

**What happens:** An admin reuses an existing Embedded Service Deployment that was built for legacy Chat. Conversations do not appear as `MessagingSession` records, and the MIAW-only capabilities — enhanced-channel session statuses, Omni-Channel flow routing through `sessionHandlerFlow` — are simply absent.

**When it occurs:** Whenever `EmbeddedServiceConfig.deploymentFeature` is `LiveAgent` rather than `EmbeddedMessaging`. Those are two values of one enum alongside `Flows`, `FieldService` and `None` (api_meta:56842–56849), and the MIAW-only subtype `embeddedServiceMessagingChannel` is documented as applying to deployments "whose deploymentFeature is EmbeddedMessaging" (api_meta:57152–57156). Legacy Chat also has a routing ceiling the Metadata API states outright: on `LiveChatButton`, "Chats routed with Omni-Channel aren't supported in the Metadata API" (api_meta:85024).

**How to avoid:** Build a net-new `EmbeddedServiceConfig` with `deploymentFeature` set to `EmbeddedMessaging` and a `embeddedServiceMessagingChannel/messagingChannel` pointing at the MIAW channel. Run old and new side by side during cutover. Before decommissioning the legacy path, re-point every report and integration that reads `LiveChatTranscript` — and note that the on-platform `ConversationEntry` schema is legacy-only too (gotcha #10).

---

## Gotcha 3: `MessagingSession.EndUserContactId` Is Read-Only — Write the Contact on `MessagingEndUser`

**What happens:** An admin configures pre-chat to collect an email, then writes a trigger or flow that tries to stamp the Contact onto the session. The write silently does nothing, or the deploy fails on a non-updateable field. Agents keep seeing anonymous conversations.

**When it occurs:** Always, when the automation targets the session. `MessagingSession.EndUserContactId` carries the properties `Filter, Group, Nillable, Sort` — no `Create`, no `Update` (object_reference:182121–182129). `MessagingEndUser.ContactId`, by contrast, is `Create, Filter, Group, Nillable, Sort, Update` (object_reference:181625–181632), and the same object also exposes writeable `AccountId` (43.0+) and `LeadId` (57.0+).

**How to avoid:** Match the identified person on `MessagingEndUser`, not on the session — that object represents "a single address — such as a phone number or Facebook page — communicating with a single Messaging channel" (object_reference:181587), which is the durable identity across resumed conversations. Verify with `SELECT Id, MessageType, ContactId FROM MessagingEndUser WHERE MessageType = 'EmbeddedMessaging'` and treat a null `ContactId` there as the defect, not a null `EndUserContactId` on the session.

---

## Gotcha 4: Status-Based Capacity Has Two Switches — An Org Gate and a Per-Channel Field Since API 65.0

**What happens:** A team enables status-based capacity org-wide, expects messaging capacity to behave, and finds one channel still releasing capacity when a console tab closes. Or the reverse: they set the channel field and nothing changes because the org gate is off.

**When it occurs:** From API version 65.0 onwards, when the two settings disagree. `OmniChannelSettings.enableOmniStatusCapModel` is an org-level boolean defaulting to `false` (api_meta:123168), and `ServiceChannel.capacityModel` — `STATUS_BASED` or `TAB_BASED` — is a per-channel picklist available in API version 65.0 and later (api_meta:107793–107802). Before 65.0 the per-channel field did not exist, which is why older runbooks describe this as a single org-wide toggle.

**How to avoid:** Read both before changing either. Under `STATUS_BASED`, "work remains assigned and applied to an agent's capacity until the work is completed or reassigned to a different agent"; under `TAB_BASED` capacity is released when the work tab closes in the service console (api_meta:107795–107799). Asynchronous messaging outlives a tab, so a messaging `ServiceChannel` left on `TAB_BASED` over-assigns. The capacity numbers themselves live on `PresenceUserConfig` — design them in `admin/omni-channel-routing-setup`, not here.

---

## Gotcha 5: `sessionHandlerQueue` Is Required and Doubles as the Flow's Fallback — the Failure Is a Queue That Cannot Take Work

**What happens:** A routing flow faults or reaches a path that assigns nobody. The session sits in `Waiting` with no owner. Nothing in the supervisor view names the flow as the cause.

**When it occurs:** Not because the fallback field was left blank — the Metadata API will not let you. `sessionHandlerQueue` is marked **Required**, and its description reads: "The queue used to route messages. If a sessionHandlerFlow is also selected, sessionHandlerQueue is the fallback queue used if a message can't be routed using the selected flow" (api_meta:87506–87508). The real failure is a fallback queue that exists but has no routing configuration, no members, or no agent whose presence status covers the messaging channel — so the session is handed somewhere that can never accept it.

**How to avoid:** Treat `sessionHandlerQueue` as a live queue with an owner, not a placeholder. Confirm it has a `QueueRoutingConfig` and at least one member who can go available on the messaging service channel (`admin/omni-channel-routing-setup`). Then alert on the symptom directly: `SELECT COUNT(Id), Status FROM MessagingSession WHERE StartTime = LAST_N_DAYS:7 GROUP BY Status` — a growing `Waiting` or `Error` bucket is the only signal you get. `Error` is an enhanced-channel-only status (object_reference:182297–182320), so it points at the channel or the flow rather than the queue.

---

## Gotcha 6: `messagingChannelType` Lists WhatsApp and Facebook — but Those Channels Don't Use This Metadata Type

**What happens:** An admin reads the `messagingChannelType` enum, sees `WhatsApp` and `Facebook`, and authors a `MessagingChannel` XML file for a WhatsApp rollout. The work does not produce a working channel, and the mismatch is not obvious because the enum value was genuinely valid.

**When it occurs:** On third-party messaging channels. The guide states both things in the same field description: the enum includes `Facebook`, `Line`, `Text`, `WhatsApp`, `WhatsAppVoice` and more (api_meta:87456–87469), and then, four lines later, "Third-party Messaging channels in Salesforce, such as WhatsApp and Facebook Messenger, don't use this metadata type" (api_meta:87470–87472).

**How to avoid:** Use `MessagingChannel` metadata for `EmbeddedMessaging` (web and in-app chat — captioned "Enhanced Chat", api_meta:87460) and for `Custom`, which is Bring Your Own Channel for Messaging or for CCaaS, available in API version 61.0 and later (api_meta:87458). A Bring Your Own Channel build also needs a `ConversationChannelDefinition`, a separate type available in API version 60.0 and later that requires interaction service to be configured (api_meta:113413–113436). For WhatsApp or Facebook Messenger, provision through the channel's own setup path and treat the enum value as a read-side label.

---

## Gotcha 7: `EmbeddedServiceConfig` Does Not Support the `*` Wildcard — a Wildcard Manifest Retrieves It Silently as Nothing

**What happens:** A `package.xml` uses `<members>*</members>` across the messaging types. The retrieve succeeds. The deployment package contains the messaging channel, the CORS entry and the CSP entry — and no Embedded Service deployment at all. The gap surfaces in the target org as a channel with nothing rendering it.

**When it occurs:** Every wildcard retrieve or change set built by pattern. The guide is explicit for this type: "This metadata type doesn't support the wildcard character * (asterisk) in the package.xml manifest file" (api_meta:57363). `EmbeddedServiceBranding` is the same (api_meta:56790). `MessagingChannel` (api_meta:88041), `CorsWhitelistOrigin` (api_meta:39417) and `CspTrustedSite` (api_meta:39617) all *do* support it, which is exactly why the omission looks like a fluke rather than a rule.

**How to avoid:** Name every `EmbeddedServiceConfig` member explicitly in the manifest and diff the retrieved tree against the manifest before deploying. `scripts/check_messaging_and_chat_setup.py` fails the manifest when a channel is present with no deployment referencing it.

---

## Gotcha 8: Every CSP Directive Defaults to `false` — a Trusted Site With No Directives Allows Nothing

**What happens:** The admin adds the widget host under Trusted URLs, sees it listed in Setup, and the widget is still blocked. The record exists and is active; it just grants nothing.

**When it occurs:** Whenever the `isApplicableTo*Src` fields are left at their defaults. Each of `isApplicableToConnectSrc`, `isApplicableToFontSrc`, `isApplicableToFrameSrc`, `isApplicableToImgSrc`, `isApplicableToMediaSrc` and `isApplicableToStyleSrc` "has a default value of false" (api_meta:39526–39575). API version 59.0 and later requires that "for each trusted URL, at least one CSPTrustedSite starting with isApplicable or canAccess must be set to true" (api_meta:39562–39564), so a directive-free record is now rejected — but records created under older versions survive in the org unchanged. In API versions 50.0 to 58.0 an all-false record silently became image-source-only; in 49.0 and earlier all directives defaulted to true, which is why old orgs behave differently from new ones (api_meta:39565–39568).

**How to avoid:** Set the directives the widget actually needs and record why. Also check `context`: a widget on an Experience Cloud site needs `Communities` or `All`, not `LEX` (api_meta:39470–39492). And watch the header budget — keep the generated CSP header under 12 KB, with reported issues as it approaches 16 KB (api_meta:39443), which caps how many per-environment subdomains you can list before the whole header degrades. Malformed URLs are a quieter version of the same failure: `https://{subdomain}.example.com` fails the syntax check, and malformed entries saved before February 2025 are excluded from the generated header while still appearing in the list (api_meta:39511–39520).

---

## Gotcha 9: MIAW Branding Uses `BrandingSet` — `EmbeddedServiceBranding` Deploys Cleanly and Changes Nothing

**What happens:** Colours are set on an `EmbeddedServiceBranding` record. The deploy succeeds. The chat window keeps its previous appearance. The admin re-deploys with different hex values, gets the same result, and escalates it as a caching problem.

**When it occurs:** Any branding change against a MIAW deployment. The `EmbeddedServiceBranding` type description states: "This object works only with the legacy chat products. For Messaging for In-app and Web, use the BrandingSet object" (api_meta:56699). `EmbeddedServiceConfig.branding` (52.0+) is a string naming a `BrandingSet` (api_meta:56836) — the same type used for Experience Builder themes (api_meta:30571).

**How to avoid:** Author a `BrandingSet` and point `EmbeddedServiceConfig.branding` at it. Branding property names are case-sensitive and all capitals (api_meta:30620). One more trap in the same type: on `EmbeddedServiceBranding`, changes to `contrastInvertedColor` made through the API "aren't reflected in the embedded component" (api_meta:56724) — a field that accepts a value and discards it, even on the legacy path it does serve.

---

## Gotcha 10: The On-Platform `ConversationEntry` Schema Covers Legacy Chat Only

**What happens:** A team builds transcript reporting, QA sampling or an Apex summariser on `ConversationEntry` after moving to enhanced channels. Queries return far less than the conversations they watched happen, and the shape of what does come back does not match the documented fields.

**When it occurs:** On enhanced (MIAW) channels. The Object Reference says of `ConversationEntry`: "The schema on this page only applies to conversation entries for legacy chat. Refer to the ConversationEntry (Off-Core) schema in the Messaging Object Model guide to see the ConversationEntry schema for Enhanced Channels" (object_reference:83414–83416). Using the object at all also needs the Access Conversation Entries user permission from API version 50.0 onwards (object_reference:83424–83425).

**How to avoid:** Build session-level reporting on `MessagingSession` — it carries `AgentMessageCount`, `EndUserMessageCount`, `AcceptTime`, `EndTime`, `EndedByType` and `AgentType` without touching message bodies (object_reference:181946–182330). Treat message-level access on enhanced channels as an off-core integration to scope deliberately, not as a SOQL query you can assume. **UNVERIFIED (2026-09-05): the off-core ConversationEntry schema lives in the Messaging Object Model guide, which is not among the extracted sources for this skill; confirm field names there before designing against them.**
