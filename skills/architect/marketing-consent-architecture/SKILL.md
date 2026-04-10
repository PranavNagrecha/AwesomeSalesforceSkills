---
name: marketing-consent-architecture
description: "Consent management architecture across Marketing Cloud and CRM: data model design, cross-system sync patterns, and compliance design for GDPR/CCPA. Trigger keywords: consent data model, ContactPointConsent, ContactPointTypeConsent, Individual object, CRM system of record, MC consent sync, opt-in opt-out architecture, data use purpose, lawful basis. NOT for individual consent setup steps or configuring a single publication list."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how do I design consent management across Marketing Cloud and Salesforce CRM so both systems stay in sync"
  - "we need GDPR and CCPA opt-in tracking per channel and per purpose — what objects and patterns should we use"
  - "our marketing team says MC unsubscribes are not reflected in the CRM contact record and compliance is worried"
  - "should the CRM or Marketing Cloud be the system of record for subscriber consent preferences"
  - "explain the Individual, ContactPointTypeConsent, and ContactPointConsent objects and how they relate"
tags:
  - consent
  - marketing-consent
  - contact-point-consent
  - individual-object
  - data-use-purpose
  - gdpr
  - ccpa
  - marketing-cloud
  - crm-integration
  - compliance-architecture
inputs:
  - "Current state of consent data: where it lives, which system owns it, how it flows"
  - "Channels in scope (email, SMS, phone, push) and their Marketing Cloud equivalents"
  - "Regulatory requirements (GDPR, CCPA, CAN-SPAM) applicable to the org"
  - "Whether Marketing Cloud Consent Management integration is already configured"
  - "Existing CRM objects used for contact preferences (custom fields vs. platform objects)"
outputs:
  - "Recommended consent data model using Individual, ContactPointTypeConsent, ContactPointConsent"
  - "Sync pattern specifying which system is authoritative and how updates flow at send time"
  - "Data Use Purpose configuration guidance for per-purpose lawful basis tracking"
  - "Gap analysis between current state and compliant target architecture"
  - "Decision table for consent read behavior at send execution"
dependencies:
  - consent-management-marketing
  - gdpr-data-privacy
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Marketing Consent Architecture

This skill activates when a practitioner needs to design or evaluate the cross-system consent management architecture spanning Salesforce CRM and Marketing Cloud Engagement — covering the canonical data model, sync strategy, and compliance design. It does not cover step-by-step setup of individual publication lists or subscriber preference centers.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether Marketing Cloud Consent Management integration is enabled in the connected org. Without it, MC does not read CRM consent at send time — this is the most common architectural gap.
- Identify which channels are in scope: email, SMS, phone, and push each map to distinct ContactPointTypeConsent records with their own channel values.
- Clarify the regulatory regimes (GDPR requires opt-in with documented lawful basis; CCPA requires opt-out capability and "do not sell" signals). These determine whether ContactPointTypeConsent Data Use Purpose fields must be populated.
- Determine whether the org has custom consent fields on Contact/Lead today, and whether a migration or parallel-run period is required.

---

## Core Concepts

### The Salesforce Consent Data Model

The platform consent data model uses three standard objects working together:

**Individual** is the privacy pivot object. Every Contact and Lead can be linked to an Individual record (via the `IndividualId` lookup). Individual stores high-level data privacy preferences: `HasOptedOutOfEmail`, `HasOptedOutOfFax`, `HasOptedOutProcessing`, `HasOptedOutProfiling`, `HasOptedOutSolicit`, `HasOptedOutTracking`. These are coarse-grained, boolean flags — they represent the broadest opt-out state for the person, not channel- or purpose-specific consent.

**ContactPointTypeConsent** stores consent at the channel type level. It is linked to an Individual and has a `ContactPointType` picklist (Email, Phone, Fax, Web, Social, EngagementChannel, etc.) plus a `PrivacyConsentStatus` (OptIn, OptOut, NotSeen, Seen). Critically, it also carries a `DataUsePurpose` lookup, which is where lawful basis and purpose-specific consent is modeled. A single Individual can have multiple ContactPointTypeConsent records — one per channel per purpose combination. This object is the correct place to record GDPR lawful basis and CCPA "do not sell" purpose distinctions.

**ContactPointConsent** stores consent at the level of a specific contact point instance — e.g., a particular email address or phone number — rather than the channel type in general. It links to a ContactPoint (ContactPointEmail, ContactPointPhone, etc.) and carries its own `PrivacyConsentStatus` and `DataUsePurpose`. Use this when a person has multiple email addresses and the opt-out applies to one address, not their entire email channel.

The hierarchy: Individual (person) → ContactPointTypeConsent (channel + purpose) → ContactPointConsent (specific address/number).

### MC All Subscribers and the HasOptedOutOfEmail Gap

Marketing Cloud maintains its own subscriber list — All Subscribers — with a `HasOptedOutOfEmail` boolean on each subscriber record. This field captures unsubscribes triggered within MC (click-to-unsubscribe, SafeUnsubscribe, etc.). It does **not** automatically write back to any CRM object. Without explicit integration logic, an MC unsubscribe creates no ContactPointConsent record, does not flip the Individual's `HasOptedOutOfEmail`, and leaves the CRM record in a state that implies the contact is still contactable. This is a significant compliance gap: the CRM appears to have consent the subscriber has revoked.

The reverse is also true: updating a Contact's `HasOptedOutOfEmail` in CRM does not automatically suppress the MC subscriber unless the Consent Management integration or a custom sync process pushes that state.

### MC Consent Read at Send Time

When Marketing Cloud Consent Management integration is configured, MC queries the CRM consent data model at send execution time to determine whether a subscriber should receive a message. "At send time" means MC evaluates ContactPointTypeConsent (and optionally ContactPointConsent) records against the sending Publication List or Send Classification's configured Data Use Purpose. If no matching consent record exists, or if the status is OptOut, the subscriber is suppressed.

This is not the default behavior. MC does not automatically evaluate CRM consent without the integration being explicitly configured in the Marketing Cloud Connector settings. Orgs that have connected MC to CRM but not enabled Consent Management are still in the gap state described above.

---

## Common Patterns

### CRM as System of Record, MC Reads at Send Time

**When to use:** This is the recommended architecture for any org operating under GDPR or CCPA, or any org where the CRM contact record is the authoritative source of customer data.

**How it works:**
1. All consent preferences are written to CRM objects (Individual, ContactPointTypeConsent, ContactPointConsent) whenever they change — from any channel, including preference center submissions, web form captures, in-store captures, and CS-driven updates.
2. Marketing Cloud Consent Management integration is enabled. MC's connector is configured with one or more Data Use Purpose mappings that tie a sending context (journey, send classification) to a specific Data Use Purpose record in CRM.
3. At send time, MC queries the CRM consent objects via the integration. Subscribers with `PrivacyConsentStatus = OptOut` for the relevant channel and purpose are excluded from delivery.
4. When a subscriber unsubscribes via MC (click-to-unsubscribe or REST API), the integration writes that unsubscribe back to CRM as a ContactPointConsent or ContactPointTypeConsent record with `PrivacyConsentStatus = OptOut`.
5. The CRM record becomes the single audit trail for consent history.

**Why not the alternative:** Storing consent only in MC All Subscribers is not compliant for GDPR because there is no per-purpose lawful basis tracking, no audit trail of when consent was obtained or changed, and no single record of truth that can respond to a data subject access request.

### Dual-Write Pattern for Channel-Specific Preferences

**When to use:** When subscribers manage preferences across multiple channels (email, SMS, push) and need granular control — e.g., opt out of promotional email but keep transactional email.

**How it works:**
1. Create one ContactPointTypeConsent record per channel per Data Use Purpose per Individual. For example: Email + Marketing Purpose = OptIn; Email + Transactional Purpose = OptIn; SMS + Marketing Purpose = OptOut.
2. Each sending journey in MC is tagged with a specific Data Use Purpose. At send time, MC evaluates only the consent record matching that purpose.
3. Preference center updates write to the relevant ContactPointTypeConsent record, not to a single boolean on Contact.
4. Report on consent coverage by querying ContactPointTypeConsent grouped by DataUsePurpose and PrivacyConsentStatus.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| GDPR-regulated org with MC + CRM | CRM as system of record, MC Consent Management integration enabled, per-purpose ContactPointTypeConsent | GDPR requires documented lawful basis per purpose; CRM model supports this, MC All Subscribers boolean does not |
| CCPA-regulated org, "do not sell" requirement | ContactPointTypeConsent with a "Do Not Sell" Data Use Purpose, status = OptOut | CCPA requires honoring opt-out of sale of personal information; purpose-specific consent record provides audit trail |
| Unsubscribes only via MC, no CRM update needed | Not recommended for regulated use cases; if proceeding, ensure MC unsubscribe webhook or triggered flow writes back to CRM | Single source of truth in MC only is fragile; CRM may be used for other sends or service contacts |
| Multiple email addresses per person | Use ContactPointConsent linked to specific ContactPointEmail record | ContactPointTypeConsent opts out the whole channel; ContactPointConsent is address-specific |
| CRM has legacy custom consent fields on Contact | Run parallel: populate both custom fields and platform objects during transition; eventually deprecate custom fields | Platform objects support audit history, Data Use Purpose, and MC integration; custom fields do not |
| Marketing only, no GDPR/CCPA requirement | At minimum use Individual.HasOptedOutOfEmail for simple suppression; MC publication list opt-out for channel management | Lower compliance overhead is acceptable when regulations do not apply, but design for future migration |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing this architecture:

1. **Audit current state** — Identify where consent is stored today (Contact boolean fields, MC All Subscribers, custom objects, external system). Map each consent signal to its channel and any associated purpose or lawful basis. Flag any signals that are stored only in MC without a CRM counterpart.

2. **Map channels and purposes to data model objects** — For each channel (Email, SMS, Phone) and each regulatory purpose (Marketing, Transactional, Analytics, Do Not Sell), determine whether ContactPointTypeConsent or ContactPointConsent is the right granularity. Create a mapping table: Individual → ContactPointTypeConsent records needed → ContactPointConsent records needed.

3. **Configure Data Use Purpose records** — In CRM, create Data Use Purpose records for each distinct lawful basis or processing purpose. Assign the appropriate `LegalBasis` (Consent, LegitimateInterest, ContractPerformance, LegalObligation, VitalInterest, PublicTask) and `LegalBasisSource`. These records are referenced by ContactPointTypeConsent.

4. **Enable Marketing Cloud Consent Management integration** — In the MC connector setup, enable Consent Management and map each MC Send Classification or Journey to the corresponding Data Use Purpose in CRM. Confirm that the integration is writing MC unsubscribes back to CRM consent objects.

5. **Build or validate the writeback path** — Ensure that every consent-capture surface (preference center, web form, CS workflow) writes to CRM consent objects as the primary store. If MC has a preference center or SafeUnsubscribe, confirm the writeback to CRM is active and test it end-to-end.

6. **Validate suppression at send time** — Send a test message to a subscriber whose CRM consent record is set to OptOut for the relevant purpose. Confirm MC suppresses the message. Confirm the suppress reason is logged.

7. **Document the consent audit trail** — Confirm that ContactPointConsent and ContactPointTypeConsent records include `CaptureDate`, `CaptureSource`, and `DataUsePurpose`. Run a sample data subject access report to verify the audit trail is complete enough to respond to a GDPR Article 15 request.

---

## Review Checklist

Run through these before marking architecture design complete:

- [ ] Individual records exist or are being created for all Contacts and Leads in scope
- [ ] ContactPointTypeConsent records exist for each channel + purpose combination in scope
- [ ] Data Use Purpose records are created with correct LegalBasis values
- [ ] Marketing Cloud Consent Management integration is enabled and mapped to Data Use Purposes
- [ ] MC unsubscribe writeback to CRM is tested and confirmed working
- [ ] ContactPointConsent is used where address-level (not channel-level) granularity is required
- [ ] CRM is the single system of record; no consent decisions are made from MC All Subscribers boolean alone
- [ ] Consent audit trail includes CaptureDate, CaptureSource, and DataUsePurpose on every record
- [ ] Data subject access request workflow can pull consent history from CRM objects

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **MC HasOptedOutOfEmail does not write back to CRM** — Unsubscribes processed within MC update the All Subscribers record only. The linked CRM Contact or Individual record is not updated unless the MC Consent Management integration writeback is explicitly configured and tested. Orgs frequently discover this gap during a GDPR audit when they find CRM shows opt-in for contacts who unsubscribed in MC months earlier.

2. **MC Consent Management integration is not automatic after connecting MC to CRM** — Connecting MC to a Salesforce org via the Marketing Cloud Connect package establishes a data sync, but does not enable Consent Management. Consent Management is a separate feature that must be turned on in the connector setup and explicitly mapped to Data Use Purpose records. An org can be fully connected yet have zero consent reads at send time.

3. **Individual.HasOptedOutOfEmail is not the same as ContactPointTypeConsent OptOut** — The Individual boolean is coarse-grained and affects all email sends regardless of purpose. ContactPointTypeConsent with a specific DataUsePurpose is purpose-scoped. If you populate only the Individual boolean, you cannot distinguish between a marketing opt-out and a transactional opt-out — which matters for GDPR Article 6(1)(b) (contract performance) sends that may still be lawful even when marketing consent is withdrawn.

4. **ContactPointConsent vs. ContactPointTypeConsent confusion causes over-suppression** — If ContactPointConsent (address-level) is used where ContactPointTypeConsent (channel-level) is intended, suppression may be incomplete: opting out one email address does not suppress a second address for the same person. Conversely, using ContactPointTypeConsent where address-level granularity is needed will suppress all emails to that person, not just the opted-out address.

5. **Data Use Purpose LegalBasis field is required for GDPR compliance but not enforced by the platform** — The platform does not prevent saving a ContactPointTypeConsent record without a populated DataUsePurpose or without a LegalBasis on that purpose. Orgs frequently skip this during initial rollout and later find their consent records are incomplete for regulatory audit purposes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Consent data model diagram | Mapping of Individual, ContactPointTypeConsent, ContactPointConsent, and DataUsePurpose records for the org's channels and purposes |
| Data Use Purpose record list | Table of purposes with LegalBasis, LegalBasisSource, and owning team |
| Sync pattern specification | Document defining which system owns each consent signal, writeback triggers, and failure handling |
| MC integration configuration checklist | Step-by-step checklist for enabling and validating Consent Management in MC connector |

---

## Related Skills

- `consent-management-marketing` — individual consent setup steps in Marketing Cloud (publication lists, preference center, SafeUnsubscribe) — use alongside this skill for implementation detail
- `gdpr-data-privacy` — broader GDPR data privacy design including data subject rights, retention, and data processing agreements
