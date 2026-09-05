---
name: messaging-and-chat-setup
description: "Configure Messaging for In-App and Web (MIAW) channels in Service Cloud: Messaging Channel, Embedded Service Deployment, CORS/CSP Trusted Sites, pre-chat fields, session routing by Queue or Omni-Channel Flow, Status-Based capacity, Live Agent migration. Trigger keywords: MessagingChannel, EmbeddedServiceConfig, messagingChannelType, EmbeddedMessaging, sessionHandlerQueue, sessionHandlerFlow, embeddedConfig, automatedResponses, CorsWhitelistOrigin, CspTrustedSite, BrandingSet, MessagingSession, MessagingEndUser, enhanced chat, embedded messaging, chat widget, pre-chat form, auto-response. NOT for an Agentforce agent in the chat window - use agentforce/agent-channel-deployment. NOT for Omni-Channel enablement, Service Channels or skills-based routing - use admin/omni-channel-routing-setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I set up a chat widget on my Salesforce support site using MIAW?"
  - "Chat button not showing up on website after configuring Embedded Service Deployment"
  - "How do I route messaging sessions to different queues based on language or business hours?"
  - "Migrating from Live Agent to Messaging for In-App and Web"
  - "CORS error when loading Salesforce chat widget on external website"
  - "chat widget request returns 404 instead of a CORS error"
  - "deploy a MessagingChannel to a sandbox and it fails on a required field"
  - "MessagingSession stuck in Waiting with no agent assigned"
  - "CSP Trusted Site added but the embedded messaging script is still blocked"
  - "configure the pre-chat form fields on an embedded messaging deployment"
  - "MessagingSession has no contact linked after the chat ends"
  - "package.xml wildcard does not retrieve EmbeddedServiceConfig"
  - "change the colours of the MIAW chat window"
  - "add an auto-response to an embedded messaging channel"
  - "route messaging sessions with an Omni-Channel flow and a fallback queue"
  - "set up a WhatsApp channel with MessagingChannel metadata"
tags:
  - messaging
  - chat
  - MIAW
  - omni-channel
  - embedded-service
  - live-agent
  - service-cloud
  - embedded-messaging
  - cors
  - csp
  - messaging-session
inputs:
  - Org edition and Messaging for In-App and Web feature availability confirmation
  - List of widget domains where the chat button will be embedded
  - Omni-Channel routing strategy (Queue-based or Flow-based)
  - Agent capacity model preference (Tab-Based or Status-Based)
  - Pre-chat field requirements (fields to collect before session begins)
  - Name of the Experience site or website the deployment attaches to
  - Name of the fallback queue and confirmation that it has members
  - Auto-response text and languages for the initial, inactive and agent-end paths
outputs:
  - MessagingChannel metadata with routing, embeddedConfig, auto-responses and pre-chat parameters
  - EmbeddedServiceConfig metadata binding the channel, site, branding set and pre-chat form
  - BrandingSet for the chat window (not EmbeddedServiceBranding, which is legacy-only)
  - CorsWhitelistOrigin and CspTrustedSite entries for every widget domain
  - package.xml naming each EmbeddedServiceConfig explicitly (the type has no wildcard support)
  - Checker run with no ERROR from scripts/check_messaging_and_chat_setup.py
  - MessagingSession and MessagingEndUser verification query results from a test conversation
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Messaging and Chat Setup

This skill activates when a practitioner needs to set up or troubleshoot real-time or asynchronous chat channels in Salesforce Service Cloud using Messaging for In-App and Web (MIAW). It covers the full administrative configuration path from channel creation through Omni-Channel routing to agent capacity management.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has **Messaging for In-App and Web** enabled (Setup > Messaging Settings). This is separate from legacy Live Agent. The `MessagingChannel` metadata type is documented as available only when the org has the "Configure Messaging" and "View Setup and Configuration" permissions enabled for Messaging — a retrieve or deploy that fails on access rather than shape points here. There is no `MessagingSettings` metadata type to deploy the enablement itself.
- Identify every domain (hostname + protocol) where the chat widget will be embedded. Each domain needs both a CORS Trusted Site and a CSP Trusted Site entry — missing either causes the widget to silently fail.
- Determine whether routing will use a simple Queue assignment or a dynamic Omni-Channel Flow. Queue-based routing is simpler but Flow-based routing supports conditional logic such as language routing or business-hours fallback.
- Decide the capacity model upfront: **Tab-Based** (capacity released when the console work tab closes) or **Status-Based** (capacity held until the work is completed or reassigned — the right model for asynchronous messaging, which outlives a tab). Since API 65.0 this is two settings that must agree: the org gate `OmniChannelSettings.enableOmniStatusCapModel` and the per-channel `ServiceChannel.capacityModel`. Both, and the capacity numbers on Presence Configurations, belong to `admin/omni-channel-routing-setup`.

---

## Questions to Ask Before Configuring

Ask these before opening Setup. Each one maps to a behaviour in `references/gotchas.md`; an agent that skips them produces a channel that deploys cleanly and serves nobody.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which channel are we actually building — web/in-app chat, SMS, WhatsApp, or a partner channel?" | `messagingChannelType` lists `WhatsApp`, `Facebook`, `Text` and more, but the guide says third-party channels don't use this metadata type (gotchas #6) | The right value (`EmbeddedMessaging` or `Custom`) — or the finding that this skill is the wrong path |
| "Which Experience site or website does the widget live on, and does it exist yet?" | `EmbeddedServiceConfig.site` is Required; there is no site-less web deployment | The site's developer name and its place ahead of this work in the deploy order |
| "Which queue owns a session that the routing flow can't place, and who is in it?" | `sessionHandlerQueue` is Required and doubles as the flow's fallback; the failure is a fallback nobody can accept from (gotchas #5) | A named queue with a routing configuration and at least one available agent |
| "List every origin the widget loads from — production, staging, UAT, preview — with scheme and port." | A non-allowlisted origin gets HTTP 404, not a CORS error, so the symptom lies about the cause (gotchas #1) | The exact CORS and CSP entry list, and whether one wildcard pattern covers them |
| "Which resources does the host page need to load — scripts, frames, images, fonts, styles?" | Every CSP directive defaults to false, and a directive-free trusted site grants nothing (gotchas #8) | The `isApplicableTo*Src` set, chosen rather than defaulted |
| "Who links the conversation to a Contact, and on which record?" | `MessagingSession.EndUserContactId` is read-only; the writeable field is on `MessagingEndUser` (gotchas #3) | An owner and a target object for the identity automation, before agents see anonymous chats |
| "What does the customer hear when we're closed, when they go quiet, and when the agent leaves?" | Each is a separate `automatedResponses` type; `responseTimeoutInMins` is bounded at 5–60 | The auto-response set and languages, instead of silence on three real paths |

What a proper configuration adds over just creating a channel: the widget loads on every environment rather than only production, every session reaches a queue that can accept it, conversations attach to a person, and the deployment survives a wildcard retrieve instead of vanishing from the change set.

---

## Core Concepts

### MIAW vs Legacy Live Agent / Snap-ins

Messaging for In-App and Web (MIAW) is the current Salesforce platform for real-time and asynchronous web chat. It supersedes both legacy Live Agent (classic) and the Snap-ins SDK. Key differences:

- MIAW uses the **Messaging Session** object instead of `LiveChatTranscript`. Custom reports and integrations built on `LiveChatTranscript` do not apply to MIAW sessions.
- MIAW supports **asynchronous messaging**: customers can close the browser and resume the conversation later, matching the behavior of SMS and WhatsApp channels. Legacy Live Agent terminates the session on browser close.
- MIAW deployments are `EmbeddedServiceConfig` records with `deploymentFeature` set to `EmbeddedMessaging`; the legacy Chat value on the same enum is `LiveAgent`. Only `EmbeddedMessaging` deployments carry the `embeddedServiceMessagingChannel` block that binds a Messaging Channel, so a deployment built with the wrong value has no channel to surface sessions from.
- The Snap-ins SDK (used for mobile app chat) is a separate product and is not covered by this skill.

### Messaging Channel and Embedded Service Deployment

Every MIAW implementation requires two linked records:

1. **Messaging Channel** (Setup > Messaging > Messaging Channels) — defines the channel name, routing configuration, pre-chat fields, and off-hours behavior. The API name of this record is used in the deployment snippet.
2. **Embedded Service Deployment** (Setup > Embedded Service Deployments) — generates the JavaScript snippet deployed to the website. The deployment references the Messaging Channel through `embeddedServiceMessagingChannel/messagingChannel`, and names the Experience site through the Required `site` field. **UNVERIFIED (2026-09-05): the Metadata API guide shows one channel reference per deployment but does not state whether several deployments may share one channel; confirm in the org before designing a shared-channel, multi-branding layout.** Each host origin needs its own CORS and CSP registration regardless.

Pre-chat is split across the two records: the **parameters** are declared on the Messaging Channel (`standardParameters`, limited to Email, FirstName, LastName and Subject; `customParameters` for everything else), while the **form** that renders them — `embeddedServiceForms` and its fields — lives on the Embedded Service Deployment. A form field's `messagingChannelParameterType` must match the parameter kind it points at. Collecting an email does not link a Contact; that identity write goes to `MessagingEndUser.ContactId`, not to the session.

### CORS and CSP Trusted Sites

The chat widget loads cross-origin resources from Salesforce CDN endpoints. Two separate allow-lists must be updated for every domain where the widget is embedded:

- **CORS Trusted Sites** (Setup > CORS) — permits the browser to make cross-origin API calls to the Salesforce org. Without this, the widget initialization call is blocked by the browser with a CORS error and the chat button never appears.
- **CSP Trusted Sites** (Setup > CSP Trusted Sites) — controls which external sources the Lightning container allows. Required for the widget script tag to load at all.

Both entries carry a scheme and hostname (e.g. `https://www.example.com`). **Both accept a wildcard**, with different rules: `CorsWhitelistOrigin.urlPattern` supports `*` only in front of a second-level domain (`https://*.example.com` is valid, `https://support.*.com` is not), and `CspTrustedSite.endpointUrl` accepts `*.example.com`. The CSP record additionally grants nothing until at least one directive is set — see `references/gotchas.md` #8. Forgetting one of the pair, or registering production and missing preview/staging hosts, is the most common cause of widget failures outside production.

### Omni-Channel Routing for Messaging Sessions

MIAW sessions route through Omni-Channel, not through a separate chat routing engine. Two routing approaches are available:

- **Queue-Based Routing**: A Messaging Channel is associated with an Omni-Channel Queue. Sessions enter the queue and are assigned to the first available agent with the matching Presence Status and sufficient capacity. This is the simplest path and is appropriate for orgs without complex routing requirements.
- **Flow-Based Routing (Omni-Channel Flow)**: An Omni-Channel Flow (type: Messaging Session) intercepts each new session and can route conditionally — for example, routing to language-specific queues, checking business hours, or escalating to a different skill level. Required when routing logic cannot be expressed by a single queue assignment.

A fallback queue must always be configured on the Messaging Channel. If the Omni-Channel Flow fails or no agents are available, sessions fall to the fallback queue rather than dropping silently.

### Status-Based Capacity Model

Salesforce recommends **Status-Based capacity** for MIAW orgs. Under this model:

- Each agent Presence Configuration defines a numeric capacity (e.g., 5 messaging sessions).
- The platform tracks open Messaging Sessions against that capacity.
- When an agent marks a session resolved or transfers it, capacity is immediately released.

The older Tab-Based model releases capacity when the console work tab closes, which is unreliable for asynchronous messaging that outlives a tab. There are **two switches**: the org-level gate `OmniChannelSettings.enableOmniStatusCapModel`, and — from API version 65.0 — a per-channel `ServiceChannel.capacityModel` of `STATUS_BASED` or `TAB_BASED`. Both must agree. Capacity numbers themselves live on Presence Configurations, which belong to `admin/omni-channel-routing-setup`.

---

## Common Patterns

### Pattern: Greenfield MIAW Deployment with Queue Routing

**When to use:** New orgs or orgs migrating from legacy Live Agent that need a straightforward chat channel without complex conditional routing.

**How it works:**
1. Enable Messaging for In-App and Web in Messaging Settings.
2. Create a Messaging Channel: `masterLabel`, `messagingChannelType` `EmbeddedMessaging`, `sessionHandlerType` `Queue`, and `sessionHandlerQueue` naming the queue. Add the `automatedResponses` set for the initial and agent-end paths.
3. Declare pre-chat parameters on the channel — `standardParameters` for First Name, Last Name and Subject, `customParameters` for anything else.
4. Create the Embedded Service Deployment: `site`, `deploymentFeature` `EmbeddedMessaging`, `deploymentType` `Web`, the full `embeddedServiceMessagingChannel` block, the `embeddedServiceForms` pre-chat form matching step 3, and `branding` naming a `BrandingSet`.
5. Add CORS and CSP Trusted Site entries for the target domain.
6. Copy the deployment code snippet and paste into the website `<head>` or tag manager.
7. Test in a sandbox using a second browser session as the customer.

**Why not the alternative:** Skipping the Messaging Channel / Embedded Service Deployment separation and attempting to reuse a legacy Live Agent Chat deployment produces a deployment that routes to `LiveChatTranscript`, not `MessagingSession`, breaking all MIAW-native features.

### Pattern: Flow-Based Routing with Business-Hours Fallback

**When to use:** Orgs with multiple agent skill groups, time-zone-aware routing, or off-hours deflection to a bot or knowledge article.

**How it works:**
1. Create an Omni-Channel Flow (type: Messaging Session).
2. In the flow, use a Get Records element to check Business Hours.
3. Branch: during hours, route to the appropriate queue based on a pre-chat field (e.g., language or product line); outside hours, send an auto-response message and end the session or queue to a low-priority fallback queue.
4. On the Messaging Channel, set `sessionHandlerType` to `Flow`, `sessionHandlerFlow` to the flow's API name, and `sessionHandlerQueue` to the queue that catches whatever the flow cannot place — that queue is the fallback, and it is Required.
5. Map each pre-chat parameter to the flow with `actionParameterMappings/actionParameterName` set to the flow's API name; an unmapped parameter never reaches the routing logic.
6. Test the routing logic in sandbox across each branch and at least one out-of-hours run, then confirm with the `MessagingSession` query in `references/metadata-examples.md`.

**Why not the alternative:** Implementing business-hours logic in Apex triggers on `MessagingSession` is possible but fragile — it fires after routing has already begun and can leave sessions in inconsistent states.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-language support team, no conditional routing | Queue-Based Routing | Simpler to configure and maintain; sufficient for most SMB deployments |
| Multi-language or multi-skill routing required | Omni-Channel Flow routing | Flows support conditional branching; queues cannot conditionally route |
| New org, no existing chat infrastructure | MIAW with `STATUS_BASED` capacity on the messaging service channel | Async sessions outlive a console tab, which is exactly what `TAB_BASED` keys on |
| Migrating from legacy Live Agent | Create new MIAW channel; run in parallel during cutover | Reusing Live Agent deployments causes transcript and routing conflicts |
| Pre-chat answers must reach routing logic | Declare the parameter on the channel and map it with `actionParameterMappings` | An unmapped parameter is stored but invisible to the flow |
| The conversation must attach to a Contact | Write `MessagingEndUser.ContactId` from a flow or trigger | `MessagingSession.EndUserContactId` is not writeable |
| Agents handle both phone and messaging | Status-Based capacity model | Tab-Based is unreliable for voice + async messaging concurrency |

---

## Recommended Workflow

1. **Read the shapes before opening Setup.** Open `references/metadata-examples.md` for the five types this skill owns (`MessagingChannel`, `EmbeddedServiceConfig`, `BrandingSet`, `CorsWhitelistOrigin`, `CspTrustedSite`), their required fields, and the deploy order. Answer the Questions to Ask table above; each unanswered row becomes a gotcha later.
2. **Confirm the two prerequisites this package depends on but does not own.** The Experience site or website named by `EmbeddedServiceConfig.site` must exist (`admin/experience-cloud-site-setup`), and the queue named by `sessionHandlerQueue` must exist with a routing configuration and members (`admin/omni-channel-routing-setup`). Retrieve both into the working project so the checker can resolve the pointers.
3. **Author the Messaging Channel.** Set `messagingChannelType` to `EmbeddedMessaging`, pick `sessionHandlerType`, and fill `sessionHandlerQueue` — it is Required and it is the fallback when `sessionHandlerFlow` is set. Declare pre-chat parameters (`standardParameters` / `customParameters`) and the `automatedResponses` set for the initial, inactive and agent-end paths.
4. **Author the Embedded Service deployment.** Set `site`, `deploymentType` `Web`, `deploymentFeature` `EmbeddedMessaging`, and the whole `embeddedServiceMessagingChannel` block — every field in it is Required. Build the pre-chat form under `embeddedServiceForms`, matching each `formField` to a parameter declared in step 3. Point `branding` at a `BrandingSet`, never at an `EmbeddedServiceBranding`.
5. **Register every origin as a CORS + CSP pair.** One `CorsWhitelistOrigin` and one `CspTrustedSite` per host, production and non-production, with the CSP directives explicitly set rather than defaulted. Name each `EmbeddedServiceConfig` explicitly in `package.xml` — the type does not support the `*` wildcard.
6. **Gate it locally, then deploy.** Run `python3 scripts/check_messaging_and_chat_setup.py --manifest-dir <retrieved-tree>` and clear every ERROR; the checks cover required fields, enum values, routing-pointer resolution, pre-chat form shape rules, directive-free CSP records and legacy Chat metadata mixed in. Then `sf project deploy validate` before `sf project deploy start`.
7. **Verify with data, not with the widget.** Run a test conversation, then the `MessagingSession` and `MessagingEndUser` queries in `references/metadata-examples.md` § Verify after deploy. Work the Review Checklist below and record which pre-chat parameters actually arrived and whether a `MessagingEndUser.ContactId` was written.

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `messagingChannelType` is `EmbeddedMessaging` (or `Custom` for Bring Your Own Channel), not a third-party value the metadata type does not provision
- [ ] `sessionHandlerType` matches what is actually populated: `Flow` with a `sessionHandlerFlow`, or `Queue` with none
- [ ] `sessionHandlerQueue` names a real queue that has a routing configuration and at least one agent who can go available on the messaging service channel
- [ ] `EmbeddedServiceConfig.site` resolves, and `deploymentFeature` is `EmbeddedMessaging` with `deploymentType` `Web`
- [ ] The whole `embeddedServiceMessagingChannel` block is present — every field in it is Required
- [ ] Every pre-chat form field maps to a parameter declared on the channel, with a matching `messagingChannelParameterType`
- [ ] Hidden pre-chat fields have `displayOrder` `-1`, `isRequired` `false`, and a `Custom` parameter type
- [ ] `automatedResponses` cover the initial, inactive and agent-end paths, with `responseTimeoutInMins` inside 5–60
- [ ] Every widget host has both a `CorsWhitelistOrigin` and a `CspTrustedSite`, production and non-production
- [ ] Each `CspTrustedSite` sets the directives it needs explicitly and uses `Communities` or `All` context for an Experience Cloud host
- [ ] Branding is a `BrandingSet` referenced by `EmbeddedServiceConfig.branding`, not an `EmbeddedServiceBranding` record
- [ ] `package.xml` names each `EmbeddedServiceConfig` explicitly rather than using `*`
- [ ] `python3 scripts/check_messaging_and_chat_setup.py --manifest-dir <tree>` reports no ERROR
- [ ] A test conversation produces a `MessagingSession` with `ChannelType = 'EmbeddedMessaging'` that reaches `Ended`, and a `MessagingEndUser` with the expected `ContactId`

## Salesforce-Specific Gotchas

Ten non-obvious platform behaviours, each with a source line, are in `references/gotchas.md`. The five that most often decide whether a first deployment works:

1. **A non-allowlisted origin returns HTTP 404, not a CORS error** — so the network tab blames the URL in the snippet while the real fault is a missing `CorsWhitelistOrigin`. CORS does accept a wildcard, but only immediately before a second-level domain.
2. **`EmbeddedServiceConfig` does not support the `*` wildcard in `package.xml`** — a wildcard manifest retrieves the channel and the trusted sites and silently omits the deployment, with no error.
3. **`MessagingSession.EndUserContactId` is read-only** — automation that tries to stamp a Contact on the session cannot succeed; the writeable field is `MessagingEndUser.ContactId`.
4. **MIAW branding uses `BrandingSet`** — `EmbeddedServiceBranding` "works only with the legacy chat products", so branding deploys against it succeed and change nothing.
5. **Every `CspTrustedSite` directive defaults to `false`** — an active trusted site with no `isApplicableTo*` field set grants nothing, and API 59.0+ now rejects that shape while older records survive.

## Output Artifacts

| Artifact | Description |
|---|---|
| `MessagingChannel` XML | Channel type, routing (`sessionHandlerType` / `sessionHandlerFlow` / `sessionHandlerQueue`), `embeddedConfig`, auto-responses, pre-chat parameters |
| `EmbeddedServiceConfig` XML | The web deployment: `site`, `deploymentFeature`, `branding`, the messaging-channel binding, and the pre-chat form |
| `BrandingSet` XML | Colours for the MIAW chat window, referenced by `EmbeddedServiceConfig.branding` |
| `CorsWhitelistOrigin` entries | One per widget host; without it the org answers 404 |
| `CspTrustedSite` entries | One per widget host, with the needed directives explicitly set |
| Deployment code snippet | Copied from the Embedded Service Deployment record in Setup |
| Checker run output | `scripts/check_messaging_and_chat_setup.py --manifest-dir <tree>`, no ERROR |
| Verification query results | `MessagingSession` and `MessagingEndUser` rows from a test conversation |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Authoring or deploying the channel, deployment, branding set and trusted sites — required fields, enum values, deploy order, package.xml, and the verification SOQL |
| `references/gotchas.md` | Something deployed cleanly and does not work, or before committing to a shape you have not deployed before |
| `references/examples.md` | Walking a greenfield build or a flow-routed build end to end, and for the CORS/CSP anti-pattern |
| `references/well-architected.md` | Justifying the routing, capacity and channel-granularity choices in a design review |
| `references/llm-anti-patterns.md` | Reviewing AI-generated messaging configuration before it reaches an org |
| `templates/messaging-and-chat-setup-template.md` | Recording context, decisions and sign-off for one deployment |

---

## Related Skills

- admin/omni-channel-routing-setup — Service channels, presence statuses and configurations, queue routing configurations: everything the queue named in `sessionHandlerQueue` depends on
- admin/experience-cloud-site-setup — The Experience site or website that `EmbeddedServiceConfig.site` must name
- admin/service-console-configuration — The console the agent actually answers in, once sessions route
- admin/business-hours-and-holidays — The Business Hours record referenced by `embeddedServiceMessagingChannel/businessHours` and by off-hours routing logic
- agentforce/agent-channel-deployment — When an Agentforce agent, not a human queue, handles the conversation
- architect/multi-channel-service-architecture — Architectural guidance when messaging is one of several concurrent channels
