---
name: subscriber-data-management
description: "Use this skill when configuring or troubleshooting Marketing Cloud subscriber identity, opt-in/opt-out status, list membership, suppression, or deduplication behavior. Triggers include: setting up Subscriber Key, diagnosing duplicate sends, handling global unsubscribes, configuring Auto-Suppression Lists, or auditing subscriber status across Business Units. NOT for CRM contact management in Sales/Service Cloud, not for SFMC audience segmentation via Data Extensions alone, and not for Email Studio content authoring."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - subscriber-data-management
  - marketing-cloud
  - subscriber-key
  - contact-key
  - all-subscribers
  - opt-out
  - suppression
  - deduplication
  - publication-list
inputs:
  - "Marketing Cloud Business Unit configuration details (single BU or Enterprise 2.0)"
  - "Current Subscriber Key strategy (email-based vs. CRM ID-based)"
  - "CRM system in use (Sales Cloud, Service Cloud, or external)"
  - "Compliance requirements (CAN-SPAM, GDPR, CASL)"
  - "Send volume and subscriber population size"
outputs:
  - "Subscriber Key design decision with rationale"
  - "Suppression list configuration recommendations"
  - "Publication list opt-in/opt-out handling plan"
  - "Deduplication strategy for sendable Data Extensions"
  - "Subscriber status remediation steps (Held, Bounced, Unsubscribed)"
dependencies: []
triggers:
  - "subscriber key strategy needs to be set up or changed"
  - "duplicate sends going to same subscriber from different data extensions"
  - "global unsubscribe not being honored across all sends"
  - "configuring Auto-Suppression Lists to exclude addresses"
  - "auditing subscriber status for Held or Bounced subscribers"
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Subscriber Data Management

This skill activates when a practitioner needs to design or troubleshoot how Marketing Cloud identifies, tracks, and manages subscriber records — including Subscriber Key strategy, unsubscribe authority, list membership, suppression, and deduplication behavior at send time. It covers the full lifecycle from initial subscriber identity setup through status management and cross-BU considerations.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What is the current Subscriber Key value in use?** Determine whether the org uses email address or a CRM ID (Contact/Lead 18-character ID). This single decision affects all downstream deduplication, migration complexity, and bounce tracking.
- **Is this a single Business Unit or Enterprise 2.0 (parent + child BUs)?** Subscriber identity does not merge across BUs in Enterprise 2.0 — each BU maintains its own All Subscribers list. Cross-BU suppression requires explicit configuration.
- **Has Marketing Cloud Connect been enabled?** If a CRM is connected, the Subscriber Key must align with the Contact/Lead ID to prevent cross-system identity fragmentation.
- **What compliance regime applies?** Global unsubscribes in Marketing Cloud are permanent at the BU level and cannot be overridden programmatically. Understand the legal opt-out requirements before designing any list management flow.

---

## Core Concepts

### Subscriber Key (Contact Key)

Subscriber Key is the primary unique identifier for a subscriber across all Marketing Cloud channels (Email, Mobile, Journey Builder, Advertising). It is set at contact creation and cannot be changed without engaging Salesforce Support — there is no self-service migration path.

**Critical rule:** Use the 18-character Salesforce CRM Contact or Lead ID as Subscriber Key, not the email address. Using email as Subscriber Key causes phantom duplication when a contact changes their email address: the old email remains as a separate subscriber record while the new email creates a new one, splitting send history and unsubscribe status across two records.

Subscriber Key is case-sensitive and must be unique per Business Unit. A single physical person can have multiple Subscriber Key records if they appear under different keys — Marketing Cloud does not automatically merge them.

### All Subscribers List and Unsubscribe Authority

The All Subscribers list is the master unsubscribe authority for every Business Unit. A global unsubscribe recorded on the All Subscribers list permanently suppresses the subscriber from all sends in that BU, regardless of their active status on any publication list.

This hierarchy is absolute: a subscriber who globally unsubscribes cannot be re-opted-in by adding them to an active publication list. The global unsubscribe can only be cleared by manually reactivating the subscriber record in the All Subscribers list, a process that must be accompanied by documented proof of fresh opt-in consent to satisfy compliance requirements.

Status values and their meanings:
- **Active** — subscriber can receive sends
- **Unsubscribed** — opted out from a specific publication list (does not block other lists)
- **Bounced** — soft bounce; system retries are possible depending on send classification
- **Held** — hard bounce; subscriber is permanently suppressed until manually reactivated or cleared via API after bounce investigation

### Deduplication at Send Time

When a sendable Data Extension contains the same Subscriber Key multiple times, Marketing Cloud sends only one message per Subscriber Key per send job. This deduplication is automatic and happens at send time — it is not configurable. The record selected for send when duplicates exist is non-deterministic; do not rely on row order in the DE to control which attributes are used.

This deduplication applies within a single send job. It does not prevent the same subscriber from receiving multiple sends across different journeys or send jobs running concurrently.

### Publication Lists vs. Auto-Suppression Lists

Publication lists control opt-in state per list. A subscriber can be active on List A and unsubscribed from List B simultaneously. Unsubscribing from a publication list does not trigger a global unsubscribe — it only affects sends targeted at that list.

Auto-Suppression Lists are a separate mechanism: any email address matched on an Auto-Suppression List is automatically excluded from all sends in the Business Unit, regardless of subscriber status or publication list membership. Auto-Suppression Lists are address-based (not Subscriber Key-based) and apply at the moment of send, so adding an address to the list retroactively protects future sends without historical record changes.

---

## Common Patterns

### Pattern: CRM-ID-Based Subscriber Key Initialization

**When to use:** Initial Marketing Cloud setup or when designing the subscriber identity model before any contacts are loaded.

**How it works:**
1. Identify the 18-character Salesforce Contact or Lead ID that will be the canonical identity for each subscriber.
2. When loading contacts into Marketing Cloud (via API, Import Activity, or Marketing Cloud Connect), populate the `SubscriberKey` field with the CRM ID — not the email address.
3. Ensure all sendable Data Extensions include a `SubscriberKey` column that contains these IDs.
4. In Journey Builder entry events, map the CRM Contact ID to the journey `ContactKey` field.
5. Validate in All Subscribers that records appear with the CRM ID as key, not as email address.

**Why not email as key:** If an email address changes, the old subscriber key (the old email) persists in the system holding unsubscribe history and bounce records. The new email becomes a new subscriber key with no history. This splits the subscriber's compliance state across two records, creating legal risk (the new key has no unsubscribe record, so a globally unsubscribed contact could receive mail under their new email address if the old key's suppression does not propagate).

### Pattern: Suppression List Management for Compliance Lists

**When to use:** When an org must exclude a category of addresses from all sends (regulatory suppression, purchased list exclusion, or competitive domain blocking) without manually managing their publication list status.

**How it works:**
1. Navigate to Email Studio > Subscribers > Suppression Lists > Auto-Suppression.
2. Create a new Auto-Suppression List and give it a descriptive name tied to its purpose (e.g., "GDPR Right-to-Erasure Requests").
3. Import the suppressed addresses as a flat list (one email per line or CSV).
4. Associate the list with the applicable Send Classifications or with all sends in the BU.
5. Validate suppression is active by running a test send to an address on the list and confirming it is excluded from the send log.

**Why not publication list unsubscribe:** Publication list unsubscribes are per-list and do not automatically extend to new lists added in the future. Auto-Suppression Lists apply universally to new and existing sends, making them more reliable for regulatory or permanent exclusion requirements.

### Pattern: Held Subscriber Reactivation After Bounce Investigation

**When to use:** A subscriber has a Held status from a hard bounce but the address has been confirmed deliverable (inbox provider error, temporary issue, or address restored).

**How it works:**
1. In All Subscribers, search for the subscriber by Subscriber Key or email address.
2. Confirm the bounce reason in the bounce log (available via Tracking or Data Views: `_Bounce`).
3. If the bounce was a false positive (address is valid), navigate to the subscriber record and change status from Held to Active.
4. Alternatively, use the REST API `PATCH /contacts/v1/contacts/{id}` with `{"status": "Active"}` for bulk reactivation.
5. Document the reason for reactivation and attach proof of deliverability confirmation for compliance audit trail.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New org, no subscribers loaded yet | Use 18-char CRM Contact/Lead ID as Subscriber Key from day one | Avoids migration debt; CRM IDs are stable and unique across system lifetime |
| Existing org uses email as Subscriber Key | Engage Salesforce Support for Subscriber Key migration before scaling sends | Self-service migration is not supported; support migration requires careful planning to preserve unsubscribe status |
| Need to exclude addresses from all BU sends permanently | Auto-Suppression List | Applies universally to future lists; publication list unsubscribe is per-list only |
| Contact opts out of one newsletter but wants others | Publication list unsubscribe (not global unsubscribe) | Preserves active status for other lists; global unsubscribe blocks all sends |
| Subscriber status is Held after hard bounce | Investigate bounce type, then manually reactivate in All Subscribers with documented justification | Held requires explicit reactivation; system will not auto-reactivate even if next send attempt would succeed |
| Enterprise 2.0 with multiple BUs needing shared suppression | Configure cross-BU suppression or manage centrally at parent BU | Each BU has its own All Subscribers list; suppression does not automatically propagate across BUs |
| Sendable DE contains duplicate Subscriber Keys | Accept platform deduplication (one send per key per job) | Platform handles this automatically; do not attempt to pre-deduplicate by dropping rows — attribute selection is non-deterministic |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Establish Subscriber Key strategy** — Confirm whether the org uses email or CRM ID as Subscriber Key. If email is in use and CRM IDs are available, flag the migration risk and engage Salesforce Support before proceeding with any subscriber data changes.
2. **Audit All Subscribers list** — Check the distribution of Active, Unsubscribed, Bounced, and Held statuses. Flag any Held subscribers that represent addresses confirmed deliverable, and initiate reactivation with documented evidence.
3. **Map unsubscribe requirements** — Determine whether opt-outs are per-list (publication list unsubscribe) or global (All Subscribers unsubscribe). Ensure no workflow attempts to override a global unsubscribe by adding the subscriber back to a publication list.
4. **Configure Auto-Suppression Lists** — For any regulatory exclusion lists, permanent suppression requirements, or domain-level blocks, create Auto-Suppression Lists and validate they are associated with the correct Send Classifications.
5. **Validate sendable Data Extension deduplication** — Confirm that sendable DEs use Subscriber Key as the primary key field. If sends target the same subscriber multiple times within a single send job, document that platform deduplication will reduce actual send count.
6. **Test send pipeline end-to-end** — Execute a test send against a small segment covering Active, Held, globally Unsubscribed, and Auto-Suppressed addresses. Verify only Active non-suppressed records receive the send.
7. **Document compliance state** — Confirm that the All Subscribers unsubscribe authority is not bypassed by any automation and that the send log (Data View: `_Sent`, `_Unsubscribe`) is accessible for audit.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Subscriber Key strategy confirmed and documented (CRM ID preferred over email address)
- [ ] All Subscribers list audited; Held subscribers reviewed and resolved with evidence
- [ ] Global unsubscribe records confirmed not overrideable by any active publication list or automation
- [ ] Auto-Suppression Lists configured for all permanent or regulatory exclusion categories
- [ ] Sendable Data Extension uses Subscriber Key as primary key; deduplication behavior understood
- [ ] Cross-BU subscriber status isolation acknowledged if Enterprise 2.0 is in use
- [ ] Compliance documentation in place (opt-in proof, unsubscribe audit trail accessible)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Email-as-Subscriber-Key creates ghost duplicates on address change** — When a subscriber changes their email address and the Subscriber Key is the email, the old key retains all history (including unsubscribes and bounces) while the new email creates a fresh subscriber key with no compliance history. This means a previously globally unsubscribed contact can receive mail again under their new email — a direct compliance violation.

2. **Global unsubscribe cannot be overridden by publication list active status** — A common mistake is adding a globally unsubscribed contact to an "active" publication list expecting them to receive sends. The All Subscribers global unsubscribe suppresses the send regardless of publication list membership. There is no configuration that overrides this at the BU level.

3. **Deduplication within a send job is non-deterministic for attribute selection** — When a Subscriber Key appears multiple times in a sendable DE, exactly one record is sent, but Marketing Cloud does not guarantee which row's attributes (e.g., First Name, personalization data) are used. Pre-processing to ensure only one canonical row per Subscriber Key in the DE is required if personalization accuracy matters.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Subscriber Key Design Decision | Documented choice of identifier type (CRM ID vs. email), rationale, and migration plan if applicable |
| Suppression List Configuration | Named Auto-Suppression Lists with purpose, associated Send Classifications, and validation test results |
| Subscriber Status Audit Report | Count and resolution plan for Held, Bounced, and Unsubscribed records in All Subscribers |
| Sendable DE Deduplication Review | Confirmation that DEs use Subscriber Key as primary key and that duplicate row behavior is documented |

---

## Related Skills

- `email-deliverability-strategy` — when subscriber status issues stem from systemic bounce rates or inbox placement problems requiring sender reputation remediation
- `journey-builder-administration` — when subscriber entry/exit rules in journeys interact with unsubscribe status or contact suppression
- `consent-management-marketing` — when opt-in/opt-out design must satisfy GDPR, CAN-SPAM, or CASL legal requirements beyond basic list management
