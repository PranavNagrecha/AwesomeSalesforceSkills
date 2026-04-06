---
name: multi-channel-service-architecture
description: "Use when designing a unified multi-channel service strategy spanning phone (Service Cloud Voice), email (Email-to-Case), chat (Messaging for In-App/Web), social, and SMS with Omni-Channel routing. Triggers: channel prioritization, unified routing across channels, service channel migration, multi-channel capacity planning. NOT for individual channel setup or configuration — see service-cloud-architecture for single-channel implementation details."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Multi Channel Service Architecture

This skill activates when a practitioner needs to design or evaluate a unified service strategy that spans multiple customer contact channels within Salesforce. It covers channel selection, Omni-Channel routing configuration across channels, capacity weight assignment, channel migration from legacy features, and ensuring a unified case timeline. The focus is on cross-channel architectural decisions, not individual channel setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify all active and planned channels.** Enumerate every channel the org currently uses and any planned additions. Check whether legacy channels like Live Agent are still active — Messaging for In-App/Web replaced Live Agent as GA in Spring '24 and legacy deployments should be migrated.
- **Understand that channel capacity is not uniform.** The most common wrong assumption is that all channels consume equal agent capacity. In Omni-Channel, each Service Channel has its own capacity weight — a phone call typically consumes 100% of an agent's capacity while a chat may consume only 25-33%, allowing agents to handle multiple chats simultaneously.
- **Know the platform boundaries.** Each channel has distinct governor limits and licensing requirements. Service Cloud Voice requires an Amazon Connect instance and Voice licenses. Messaging for In-App/Web requires Digital Engagement licenses. Email-to-Case (on-demand) has a 25 MB email size limit and processes up to a configurable number of emails per cycle. SMS via Messaging requires a phone number provisioned through the Messaging setup.

---

## Core Concepts

### Channel-to-Feature Mapping

Every service channel maps to a specific Salesforce feature with its own setup path, licensing, and routing mechanism. Phone maps to Service Cloud Voice (powered by Amazon Connect). Email maps to Email-to-Case, available in two variants: on-demand (no software installation, emails forwarded to a Salesforce-generated address) and org-wide (email relay through your email server). Chat maps to Messaging for In-App/Web, which replaced the legacy Live Agent feature. Social maps to Social Customer Service (Social Studio is retiring). SMS maps to Messaging with a provisioned phone number. All of these channels can create or attach to Case records, and all can route through Omni-Channel for unified agent assignment.

### Omni-Channel as the Unified Routing Layer

Omni-Channel is the single routing engine that distributes work items from all channels to agents. Each channel publishes work through a Service Channel object that defines the Salesforce object type (Case, MessagingSession, VoiceCall) and a capacity weight. Routing configurations determine whether work is pushed to agents via queue-based routing, skills-based routing, or (as of Spring '25) Enhanced Omni-Channel with attribute-based routing. The critical architectural decision is choosing a single routing strategy that works across all channels rather than configuring each channel independently.

### Capacity Weights and Agent Utilization

Capacity weights control how much of an agent's bandwidth a single work item consumes. An agent's total capacity is set in their Presence Configuration (e.g., 100 units). A phone call might have a weight of 100 (fully consuming the agent), a chat session a weight of 25 (allowing up to 4 simultaneous chats), and an email case a weight of 10 (allowing parallel handling with other work). Getting these weights wrong leads to either agent underutilization or overload. Weights must be tuned based on observed handle times and adjusted per channel.

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
| High call volume, need deflection | Add Messaging and SMS as lower-cost channels with self-service bot as front door | Phone calls have capacity weight of 100; chats and SMS allow concurrency, reducing cost per contact |
| Social media complaints escalating | Social Customer Service with auto-case creation routed through Omni-Channel | Captures social interactions on Case timeline; Social Studio is retiring so use Social Customer Service directly |
| Email-to-Case choosing on-demand vs org-wide | On-demand for most orgs; org-wide only if you need email relay through your own server | On-demand requires no software installation, handles most use cases, and is simpler to maintain |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing a multi-channel service architecture:

1. **Inventory current channels and volumes.** List every channel in use today, the Salesforce feature backing it, monthly volume per channel, and average handle time. Flag any legacy features (Live Agent, Social Studio) that need migration.
2. **Define channel strategy and priority.** Decide which channels the org will support, which are primary vs. deflection targets, and the desired customer journey (e.g., chatbot-first with escalation to agent, phone reserved for complex issues).
3. **Design the Omni-Channel routing model.** Choose queue-based, skills-based, or attribute-based routing. Map each channel's Service Channel object. Define queues organized by topic or skill, not by channel. Assign capacity weights per channel based on observed handle times.
4. **Configure each channel feature.** Set up Email-to-Case, Messaging for In-App/Web, Service Cloud Voice, Social Customer Service, and SMS Messaging. Ensure each creates or links to Cases as the central object.
5. **Build the unified agent console.** Create a Lightning console app with the Service Cloud Voice softphone, Messaging panel, Case Feed for email, and a unified Case timeline showing all channel interactions.
6. **Plan channel migrations.** If migrating from Live Agent to Messaging, follow the phased migration pattern: run both concurrently, migrate entry points incrementally, validate routing, then decommission legacy.
7. **Validate with load scenarios.** Test with realistic multi-channel volume: simulate concurrent phone calls, chats, and email cases. Verify that capacity weights prevent agent overload and that routing distributes work correctly across the agent pool.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All channels map to a current (non-legacy) Salesforce feature — no Live Agent or Social Studio references in new designs
- [ ] Omni-Channel routing is configured with a single strategy (not mixed queue-based and skills-based) across all channels
- [ ] Capacity weights are assigned per Service Channel and reflect real agent handle-time data, not defaults
- [ ] Every channel creates or links interactions to the Case object for unified timeline visibility
- [ ] Agent console app includes components for all active channels (softphone, Messaging, Case Feed)
- [ ] Email-to-Case variant (on-demand vs org-wide) is explicitly chosen and documented
- [ ] Channel migration plan exists for any legacy features still in production

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Messaging for In-App/Web is not a drop-in Live Agent replacement** — The data model is different. Live Agent uses `LiveChatTranscript`; Messaging uses `MessagingSession`. Reports, automations, and routing rules referencing the old objects will break. All downstream dependencies must be audited during migration.
2. **Email-to-Case on-demand silently drops emails over 25 MB** — Emails exceeding the size limit are not bounced; they are simply not processed. Customers get no error. Monitor the unprocessed email queue and set up alerts for dropped emails.
3. **Service Cloud Voice capacity weight defaults to 100 but can be changed** — If you forget to set the VoiceCall Service Channel capacity weight and your agents have a capacity of 100, a single phone call will block all other work items. This is intentional for phone-only agents but breaks multi-channel agents who should receive chats while on a call in some models.
4. **Omni-Channel presence status is global across all channels** — An agent cannot be "Available" for chat but "Offline" for phone using a single status. You must create multiple Presence Statuses mapped to different Service Channel sets if you need per-channel availability control.

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

- Messaging for In-App and Web Overview — https://help.salesforce.com/s/articleView?id=sf.livemessage_overview.htm
- Service Cloud Voice Overview — https://help.salesforce.com/s/articleView?id=sf.voice_about.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
