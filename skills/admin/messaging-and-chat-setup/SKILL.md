---
name: messaging-and-chat-setup
description: "Use this skill to configure Messaging for In-App and Web (MIAW) channels in Salesforce Service Cloud, including Messaging Channel setup, Embedded Service Deployments, CORS/CSP Trusted Sites, Omni-Channel routing via Queue or Flow, pre-chat fields, and Status-Based capacity models. NOT for Agentforce bot configuration, SMS/WhatsApp third-party channel setup, or legacy Live Agent (Snap-ins) implementations."
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
tags:
  - messaging
  - chat
  - MIAW
  - omni-channel
  - embedded-service
  - live-agent
  - service-cloud
inputs:
  - Org edition and Messaging for In-App and Web feature availability confirmation
  - List of widget domains where the chat button will be embedded
  - Omni-Channel routing strategy (Queue-based or Flow-based)
  - Agent capacity model preference (Tab-Based or Status-Based)
  - Pre-chat field requirements (fields to collect before session begins)
outputs:
  - Configured Messaging Channel record linked to an Embedded Service Deployment
  - CORS and CSP Trusted Sites entries for every widget domain
  - Omni-Channel Queue or Routing Flow for messaging session assignment
  - Pre-chat field configuration on the Messaging Channel
  - Presence Status and capacity settings for agents
  - Review checklist confirming deployment readiness
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Messaging and Chat Setup

This skill activates when a practitioner needs to set up or troubleshoot real-time or asynchronous chat channels in Salesforce Service Cloud using Messaging for In-App and Web (MIAW). It covers the full administrative configuration path from channel creation through Omni-Channel routing to agent capacity management.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has **Messaging for In-App and Web** enabled (Setup > Messaging Settings). This is separate from legacy Live Agent. MIAW requires its own permission set and feature flag.
- Identify every domain (hostname + protocol) where the chat widget will be embedded. Each domain needs both a CORS Trusted Site and a CSP Trusted Site entry — missing either causes the widget to silently fail.
- Determine whether routing will use a simple Queue assignment or a dynamic Omni-Channel Flow. Queue-based routing is simpler but Flow-based routing supports conditional logic such as language routing or business-hours fallback.
- Decide the capacity model upfront: **Tab-Based** (legacy, counts open tabs) or **Status-Based** (recommended for MIAW, counts active messaging sessions against a configurable capacity). Changing the model after go-live requires re-configuring all Presence Configurations.

---

## Core Concepts

### MIAW vs Legacy Live Agent / Snap-ins

Messaging for In-App and Web (MIAW) is the current Salesforce platform for real-time and asynchronous web chat. It supersedes both legacy Live Agent (classic) and the Snap-ins SDK. Key differences:

- MIAW uses the **Messaging Session** object instead of `LiveChatTranscript`. Custom reports and integrations built on `LiveChatTranscript` do not apply to MIAW sessions.
- MIAW supports **asynchronous messaging**: customers can close the browser and resume the conversation later, matching the behavior of SMS and WhatsApp channels. Legacy Live Agent terminates the session on browser close.
- MIAW deployments are configured via **Embedded Service Deployments** (Setup > Embedded Service Deployments) with channel type "Messaging for In-App and Web," not via the older "Chat" channel type. Using the wrong channel type during deployment creation produces a deployment that appears functional but does not surface MIAW sessions in the agent console.
- The Snap-ins SDK (used for mobile app chat) is a separate product and is not covered by this skill.

### Messaging Channel and Embedded Service Deployment

Every MIAW implementation requires two linked records:

1. **Messaging Channel** (Setup > Messaging > Messaging Channels) — defines the channel name, routing configuration, pre-chat fields, and off-hours behavior. The API name of this record is used in the deployment snippet.
2. **Embedded Service Deployment** (Setup > Embedded Service Deployments) — generates the JavaScript snippet deployed to the website. The deployment references the Messaging Channel. One channel can serve multiple deployments (e.g., different pages with different branding), but each deployment must be separately registered in CORS and CSP.

Pre-chat fields are configured directly on the Messaging Channel record, not on the Embedded Service Deployment. Fields collect customer information before the session is created and can map to Contact or Case fields.

### CORS and CSP Trusted Sites

The chat widget loads cross-origin resources from Salesforce CDN endpoints. Two separate allow-lists must be updated for every domain where the widget is embedded:

- **CORS Trusted Sites** (Setup > CORS) — permits the browser to make cross-origin API calls to the Salesforce org. Without this, the widget initialization call is blocked by the browser with a CORS error and the chat button never appears.
- **CSP Trusted Sites** (Setup > CSP Trusted Sites) — controls which external sources the Lightning container allows. Required for the widget script tag to load at all.

Both entries must include the exact scheme and hostname (e.g., `https://www.example.com`). Wildcard subdomains are supported in CSP but not in CORS. Forgetting one of the two — or adding only the primary domain and missing preview/staging subdomains — is the most common cause of widget failures in non-production environments.

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

The older Tab-Based model counts open browser tabs as capacity units, which is unreliable for asynchronous messaging (customers may re-open sessions from different devices). Status-Based is set at the org level in Omni-Channel Settings and applies to all channels; it cannot be selectively enabled for messaging only.

---

## Common Patterns

### Pattern: Greenfield MIAW Deployment with Queue Routing

**When to use:** New orgs or orgs migrating from legacy Live Agent that need a straightforward chat channel without complex conditional routing.

**How it works:**
1. Enable Messaging for In-App and Web in Messaging Settings.
2. Create a Messaging Channel: provide name, associate an Omni-Channel Queue, configure fallback queue and off-hours message.
3. Add pre-chat fields (e.g., First Name, Last Name, Subject) mapped to Contact/Case.
4. Create the Embedded Service Deployment referencing the Messaging Channel.
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
4. On the Messaging Channel record, set "Route With" to the Omni-Channel Flow and set a fallback queue for error scenarios.
5. Test the routing logic in sandbox by simulating different times and pre-chat values.

**Why not the alternative:** Implementing business-hours logic in Apex triggers on `MessagingSession` is possible but fragile — it fires after routing has already begun and can leave sessions in inconsistent states.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-language support team, no conditional routing | Queue-Based Routing | Simpler to configure and maintain; sufficient for most SMB deployments |
| Multi-language or multi-skill routing required | Omni-Channel Flow routing | Flows support conditional branching; queues cannot conditionally route |
| New org, no existing chat infrastructure | MIAW with Status-Based capacity | Modern stack; asynchronous session support; recommended by Salesforce |
| Migrating from legacy Live Agent | Create new MIAW channel; run in parallel during cutover | Reusing Live Agent deployments causes transcript and routing conflicts |
| Pre-chat data must map to Case fields | Configure pre-chat fields on Messaging Channel | Native mapping; avoids custom Flow or Apex workarounds |
| Agents handle both phone and messaging | Status-Based capacity model | Tab-Based is unreliable for voice + async messaging concurrency |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites**: Confirm Messaging for In-App and Web is enabled in Setup > Messaging Settings. Confirm Omni-Channel is enabled. Identify the target domains for the widget and the routing strategy.
2. **Create the Messaging Channel**: Navigate to Setup > Messaging > Messaging Channels > New. Set channel type to "Messaging for In-App and Web." Assign a routing queue (or plan to assign an Omni-Channel Flow). Configure the fallback queue and off-hours auto-response text. Add pre-chat fields as needed.
3. **Create the Embedded Service Deployment**: Navigate to Setup > Embedded Service Deployments > New. Select "Messaging for In-App and Web" as the type. Reference the Messaging Channel created in step 2. Configure branding (colors, avatar) and save.
4. **Register CORS and CSP Trusted Sites**: For each widget domain, add a CORS entry (Setup > CORS > New) and a CSP Trusted Site entry (Setup > CSP Trusted Sites > New). Include all environments: production, staging, and any preview domains.
5. **Configure Omni-Channel capacity**: Navigate to Setup > Omni-Channel Settings and confirm Status-Based capacity is enabled. Open the relevant Presence Configuration and set the messaging session capacity for agents.
6. **Deploy and test**: Copy the code snippet from the Embedded Service Deployment record. Paste into the website's `<head>`. In a sandbox, open the site in one browser as the customer and initiate a chat. In another session, log in as an agent with the matching Presence Status. Confirm the session routes and appears in the Agent Console.
7. **Review and sign off**: Run the review checklist below. Confirm all domains are registered, routing is tested, and pre-chat field mapping is verified against a sample Messaging Session record.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Messaging for In-App and Web feature is enabled in Messaging Settings
- [ ] Messaging Channel record exists with correct routing queue or Omni-Channel Flow and a fallback queue
- [ ] Pre-chat fields are configured and mapped to the correct Contact or Case fields
- [ ] Embedded Service Deployment references the correct Messaging Channel
- [ ] CORS Trusted Site entry exists for every widget domain (production and non-production)
- [ ] CSP Trusted Site entry exists for every widget domain (production and non-production)
- [ ] Status-Based capacity model is enabled and Presence Configuration has messaging capacity set
- [ ] End-to-end test in sandbox confirms session creation, routing to queue, and agent pickup
- [ ] Off-hours auto-response message is configured and tested outside business hours

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CORS and CSP are both required — omitting either silently breaks the widget** — Adding a CORS Trusted Site without a matching CSP Trusted Site (or vice versa) causes the widget to fail with no visible error to the customer. The browser console shows a blocked request, but this is invisible to admins unless they check DevTools. Always add both entries together for every domain.
2. **Legacy Live Agent deployments cannot be repurposed for MIAW** — If an org has an existing "Chat" Embedded Service Deployment, it cannot be converted to a MIAW deployment. A net-new Embedded Service Deployment of type "Messaging for In-App and Web" must be created. Attempts to swap the channel type after creation are not supported.
3. **Messaging Channel pre-chat fields do not auto-match Contact by email** — Pre-chat fields collect data but do not automatically find or link an existing Contact record. A linked Omni-Channel Flow or an Apex trigger on `MessagingSession` is required to perform the Contact lookup and populate the `ContactId` field on the session.
4. **Status-Based capacity is an org-wide switch** — Enabling Status-Based capacity affects all Omni-Channel channels, not just messaging. Orgs that have Live Agent or Voice configured with Tab-Based assumptions will need Presence Configurations reviewed before switching.
5. **Fallback queue is mandatory — missing it drops sessions silently** — If the Omni-Channel Flow fails or throws an error and no fallback queue is configured on the Messaging Channel, the session is created but never assigned to an agent. There is no error surface in the UI; the customer sees the session as "waiting" indefinitely.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Messaging Channel record | The channel definition including routing, pre-chat fields, and off-hours configuration |
| Embedded Service Deployment record + code snippet | The deployment configuration and JavaScript snippet to embed on the website |
| CORS Trusted Sites entries | Per-domain allow-list entries enabling cross-origin API calls |
| CSP Trusted Sites entries | Per-domain content security policy entries enabling widget script loading |
| Presence Configuration | Agent capacity configuration specifying maximum concurrent messaging sessions |
| Omni-Channel Flow (optional) | Flow routing logic for conditional session assignment |

---

## Related Skills

- admin/omni-channel-capacity-model — Configure Tab-Based vs Status-Based capacity, Presence Statuses, and Presence Configurations in depth
- admin/sales-engagement-cadences — Separate skill for outbound engagement channels; not applicable to inbound chat
- architect/multi-channel-service-architecture — Architectural guidance when messaging is one of several concurrent channels (voice, email, social)
