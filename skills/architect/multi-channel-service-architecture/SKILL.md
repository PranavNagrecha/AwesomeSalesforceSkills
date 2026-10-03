---
name: multi-channel-service-architecture
description: "Use when designing a unified multi-channel service strategy spanning phone (Service Cloud Voice), email (Email-to-Case), chat (Messaging for In-App/Web), social, and SMS with Omni-Channel routing. Triggers: channel prioritization, unified routing across channels, service channel migration, multi-channel capacity planning. NOT for end-to-end contact centre design - use architect/service-cloud-architecture. NOT for enabling Omni-Channel and creating Service Channels - use admin/omni-channel-routing-setup."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "how do I route cases from phone, email, chat, and social through a single queue"
  - "migrating from Live Agent to Messaging for In-App and Web"
  - "designing channel prioritization so high-priority channels get answered first"
  - "unified agent experience across phone, chat, email, and social channels"
  - "multi-channel service strategy for phone email chat and social routing"
  - "set capacity so agents can handle several chats but nothing else while on a call"
  - "make phone calls route to agents before messaging and email"
tags:
  - multi-channel-service-architecture
  - omni-channel
  - service-cloud-voice
  - email-to-case
  - messaging-for-in-app-web
  - channel-prioritization
  - unified-routing
inputs:
  - "List of service channels the org needs to support (phone, email, chat, social, SMS)"
  - "Current channel configuration and any legacy channels in use (e.g., Live Agent)"
  - "Expected volume per channel and SLA requirements"
  - "Agent staffing model and skill distribution"
outputs:
  - "Channel architecture diagram mapping each channel to its Salesforce feature"
  - "Omni-Channel routing configuration with per-channel capacity weights"
  - "Channel migration plan for legacy channels (Live Agent to Messaging)"
  - "Unified case timeline design showing cross-channel interaction history"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Multi Channel Service Architecture

This skill activates when a practitioner needs to design or evaluate a unified service strategy that spans multiple customer contact channels within Salesforce. It covers channel selection, Omni-Channel routing configuration across channels, capacity weight assignment, channel migration from legacy features, and ensuring a unified case timeline. The focus is on cross-channel architectural decisions, not individual channel setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify all active and planned channels.** Enumerate every channel the org currently uses and any planned additions. Check whether legacy chat (Live Agent) is still active: the Object Reference states "the legacy chat product is in maintenance-only mode", so legacy deployments should be migrated to Messaging for In-App and Web (UNVERIFIED (2026-10-03): the earlier "GA in Spring '24" date was not confirmed).
- **Understand that channel capacity is not uniform.** The most common wrong assumption is that all channels consume equal agent capacity. In Omni-Channel, each routing configuration sets how much capacity a work item consumes, and each agent's total comes from the presence configuration. A voice call must consume 100% of an agent's capacity; a messaging session may consume 25-33%, allowing several concurrent conversations.
- **Know the platform boundaries.** Each channel has distinct governor limits and licensing requirements. Service Cloud Voice runs on Amazon Connect provisioned through Salesforce, on Partner Telephony, or on a bring-your-own contact center (Metadata API, ConversationVendorInfo `vendorType`). Messaging for In-App/Web requires Digital Engagement licenses (UNVERIFIED (2026-10-03): licence names from earlier material). Email-to-Case handles mail over its daily limit by a setting (`overEmailLimitAction`: Bounce, Discard, or Requeue); the per-email 25 MB size limit is UNVERIFIED (2026-10-03). SMS via Messaging requires a phone number provisioned through the Messaging setup.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which telephony model will Voice use: Amazon Connect through Salesforce, Partner Telephony, or a bring-your-own contact center?" | Each model provisions differently and per org (Gotcha 8) | A recorded vendor model and a per-org provisioning plan | Licences and sandboxes planned before contracts, not after |
| "How much capacity does each work type consume, and may an agent take digital work while on a call?" | Capacity is set on routing and presence configurations, and a voice call takes 100% (Gotchas 4, 5) | A capacity table per routing configuration, from observed handle times | Blended agents staffed for the concurrency the platform allows |
| "When is work finished for capacity purposes: when the tab closes or when the status says done?" | Tab-based capacity frees agents before work is complete (Gotcha 6) | A capacity model per service channel, with status mappings for case work | Agents are not over-assigned on long-running cases |
| "Which channel's work must reach agents first?" | Cross-channel priority is the routing configuration's `routingPriority`, lower first (Gotcha 7) | Priority numbers per routing configuration | The service policy is enforced by routing, not by habit |
| "Which presence statuses do agents need, and which channels does each include?" | A status grants work from every channel on it (Gotcha 3) | A small set of channel-combination statuses | Agents receive only the work they signed up for |
| "What should happen to email over the daily limit or from unauthorized senders?" | Settings can discard mail silently (Gotcha 2) | `overEmailLimitAction` and `unauthorizedSenderAction` chosen deliberately | No invisible loss of customer email |

What proper configuration adds over "just turning on channels": one routing model across channels, capacity that matches how agents actually work, and no channel that loses work silently.

---

## Core Concepts

### Channel-to-Feature Mapping

Every service channel maps to a specific Salesforce feature with its own setup path, licensing, and routing object. All can create or attach to `Case` records, and all can route through Omni-Channel for unified agent assignment.

| Channel | Salesforce feature | Routing object | Licensing notes |
|---|---|---|---|
| Phone | Service Cloud Voice (Amazon Connect through Salesforce, Partner Telephony, or bring-your-own contact center) | `VoiceCall` | Voice licence plus the chosen telephony model's provisioning |
| Email | Email-to-Case (on-demand or org-wide) | `Case` (created directly) | On-demand needs no install; org-wide relays through your mail server |
| Chat | Messaging for In-App/Web (replaces legacy chat, which is in maintenance-only mode) | `MessagingSession` | Digital Engagement license (UNVERIFIED (2026-10-03)) |
| Social | Social Customer Service (Social Studio is retiring) | `SocialPost` → `Case` | Social Customer Service entitlement |
| SMS | Messaging | `MessagingSession` | Digital Engagement license + provisioned phone number |

### Omni-Channel as the Unified Routing Layer

Omni-Channel is the single routing engine that distributes work items from all channels to agents. Each channel publishes work through a Service Channel object that defines the Salesforce object type (Case, MessagingSession, VoiceCall) and, from API 65.0, the capacity model (tab-based or status-based). Capacity consumption is set on the routing configuration. Routing configurations determine whether work is pushed to agents via queue-based routing or skills-based routing (`isAttributeBased`), with Enhanced Omni-Channel adding features such as paused capacity (UNVERIFIED (2026-10-03): the earlier "as of Spring '25" date was not confirmed). The critical architectural decision is choosing a single routing strategy that works across all channels rather than configuring each channel independently.

### Capacity Weights and Agent Utilization

Capacity weights (or percentages) on the routing configuration control how much of an agent's bandwidth a single work item consumes. An agent's total capacity is set in their presence configuration (e.g., 100 units). A phone call must take the full capacity, a messaging session might weigh 25 (up to 4 concurrent conversations), and an email case 10 (parallel handling with other digital work). Getting these weights wrong leads to either agent underutilization or overload. Weights must be tuned based on observed handle times and adjusted per channel.

### Unified Case Timeline

A core architectural goal of multi-channel service is a single case timeline that shows all interactions regardless of originating channel. When a customer calls, then follows up by email, then starts a chat — the agent should see the full history on the Case record. This requires that all channels create or relate to the same Case. Service Cloud Voice creates VoiceCall records linked to Cases. Messaging sessions attach to Cases. Email-to-Case creates Cases directly. The unified timeline surfaces in the Case Feed, but only if the data model correctly links each channel's interaction object to the Case.

---

## Common Patterns

### Hub-and-Spoke Channel Architecture

**When to use:** Greenfield multi-channel deployment or major service redesign where all channels need to be planned together.

**How it works:**

1. Define Case as the central hub object for all channels.
2. Configure each channel feature to create or link to Cases: Email-to-Case creates Cases automatically; Service Cloud Voice creates VoiceCall records linked to Cases; Messaging creates MessagingSession records linked to Cases.
3. Create a single set of Omni-Channel queues organized by skill or topic (not by channel). Example: "Billing Support" queue receives billing cases regardless of whether they arrived via phone, email, or chat.
4. Assign capacity weights per Service Channel reflecting real agent bandwidth consumption.
5. Build a single Lightning console app with tabs/components for all channel types — softphone panel for Voice, Messaging component for chat, Case Feed for email.

**Why not the alternative:** Channel-specific queues (one queue for phone, another for chat) create silos. An agent in the "phone queue" sits idle while the "chat queue" overflows, even though the agent could handle chats.

### Phased Channel Migration (Live Agent to Messaging)

**When to use:** Existing org uses legacy Live Agent and needs to migrate to Messaging for In-App/Web without disrupting active service.

**How it works:**

1. Deploy Messaging for In-App/Web in a sandbox. Configure the Embedded Service deployment with the new Messaging channel rather than the legacy Live Agent snap-in.
2. Stand up the new Messaging channel alongside Live Agent in production — both can run concurrently during migration.
3. Migrate site-by-site or page-by-page: replace the Live Agent chat button/snap-in code with the new Messaging deployment code.
4. Monitor routing: Messaging sessions route through Omni-Channel the same way Live Agent did, but the Service Channel object is different (`MessagingSession` vs `LiveChatTranscript`). Update routing rules and capacity weights accordingly.
5. Once all entry points are migrated, disable the Live Agent feature.

**Why not the alternative:** A big-bang cutover risks service disruption. Running both channels simultaneously lets you validate routing, capacity, and agent experience incrementally.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New org, no legacy channels | Hub-and-spoke with Messaging for In-App/Web, Email-to-Case (on-demand), and Service Cloud Voice | Modern stack, unified routing from day one, no migration debt |
| Existing Live Agent deployment | Phased migration to Messaging for In-App/Web | Live Agent is legacy; Messaging supports persistent conversations and asynchronous messaging |
| High call volume, need deflection | Add Messaging and SMS as lower-cost channels with self-service bot as front door | A voice call takes an agent's full capacity; messaging and SMS allow concurrency, reducing cost per contact |
| Social media complaints escalating | Social Customer Service with auto-case creation routed through Omni-Channel | Captures social interactions on Case timeline; Social Studio is retiring so use Social Customer Service directly |
| Email-to-Case choosing on-demand vs org-wide | On-demand for most orgs; org-wide only if you need email relay through your own server | On-demand requires no software installation, handles most use cases, and is simpler to maintain |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing a multi-channel service architecture:

1. **Inventory current channels and volumes.** List every channel in use today, the Salesforce feature backing it, monthly volume per channel, and average handle time. Flag any legacy features (Live Agent, Social Studio) that need migration.
2. **Define channel strategy and priority.** Decide which channels the org will support, which are primary vs. deflection targets, and the desired customer journey (e.g., chatbot-first with escalation to agent, phone reserved for complex issues).
3. **Design the Omni-Channel routing model.** Choose queue-based or skills-based routing. Map each channel's Service Channel object and capacity model. Define queues organized by topic or skill, not by channel. Set capacity and `routingPriority` per routing configuration from observed handle times (query in `references/examples.md`).
4. **Configure each channel feature.** Set up Email-to-Case, Messaging for In-App/Web, Service Cloud Voice, Social Customer Service, and SMS Messaging. Ensure each creates or links to Cases as the central object.
5. **Build the unified agent console.** Create a Lightning console app with the Service Cloud Voice softphone, Messaging panel, Case Feed for email, and a unified Case timeline showing all channel interactions.
6. **Plan channel migrations.** If migrating from Live Agent to Messaging, follow the phased migration pattern: run both concurrently, migrate entry points incrementally, validate routing, then decommission legacy.
7. **Validate with load scenarios.** Test with realistic multi-channel volume: simulate concurrent phone calls, chats, and email cases. Verify that capacity weights prevent agent overload and that routing distributes work correctly across the agent pool.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All channels map to a current (non-legacy) Salesforce feature — no Live Agent or Social Studio references in new designs
- [ ] Omni-Channel routing is configured with a single strategy (not mixed queue-based and skills-based) across all channels
- [ ] Capacity is set per routing configuration from real handle-time data; voice takes full capacity; each service channel's capacity model is chosen
- [ ] Every channel creates or links interactions to the Case object for unified timeline visibility
- [ ] Agent console app includes components for all active channels (softphone, Messaging, Case Feed)
- [ ] Email-to-Case variant (on-demand vs org-wide) is explicitly chosen and documented
- [ ] Channel migration plan exists for any legacy features still in production

---

## Salesforce-Specific Gotchas

Full detail and sources in `references/gotchas.md`. The short list, with one correction to earlier versions of this skill:

1. Messaging for In-App and Web uses `MessagingSession`, not `LiveChatTranscript`; legacy chat is in maintenance-only mode.
2. A voice call must consume 100% of an agent's capacity. The earlier statement that the voice weight "can be changed" so agents take chats during calls is withdrawn.
3. Capacity lives on the routing configuration and the presence configuration, not the service channel.
4. Tab-based capacity frees agents when the tab closes; status-based capacity holds until the work is done.
5. Cross-channel priority is `routingPriority` on the routing configuration, lower first.
6. Email over the daily limit is bounced, discarded, or requeued according to `overEmailLimitAction`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Channel architecture map | Matrix of channels, backing Salesforce features, Service Channel objects, capacity weights, and licensing requirements |
| Omni-Channel routing design | Document specifying routing strategy, queue structure, skills/attributes, and capacity configuration |
| Channel migration plan | Step-by-step plan for migrating legacy channels (Live Agent, Social Studio) to current equivalents |
| Agent console layout specification | Lightning App Builder page layout with components for all active channels and unified Case timeline |

---

## Related Skills

- service-cloud-architecture — Use for deep-dive into Service Cloud configuration including entitlements, milestones, and case management beyond channel architecture
- omni-channel-capacity-model — Use when fine-tuning capacity weights, agent utilization targets, and routing optimization within Omni-Channel
- einstein-bot-architecture — Use when adding chatbot deflection as a front door to Messaging or other digital channels

---

## Official Sources Used

- Metadata API Developer Guide and Object Reference, Version 67.0 (full list in `references/well-architected.md`)
- Messaging for In-App and Web Overview — https://help.salesforce.com/s/articleView?id=sf.livemessage_overview.htm
- Service Cloud Voice Overview — https://help.salesforce.com/s/articleView?id=sf.voice_about.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
