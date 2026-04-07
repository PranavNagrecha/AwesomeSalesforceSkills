---
name: fsc-referral-management
description: "Use this skill when configuring or troubleshooting FSC Referral Management: setting up referral types via ReferralRecordTypeMapping custom metadata, routing referrals through Lead Assignment Rules keyed on the Expressed Interest picklist, tracking Referrer Score, or enabling partner referral visibility in Experience Cloud. Trigger keywords: referral routing, FSC referral types, ReferralRecordTypeMapping, Expressed Interest picklist, partner referral Contact, Referrer Score Experience Cloud. NOT for standard Salesforce Lead management outside FSC, Einstein Referral Scoring (retiring feature), or Marketing Cloud referral campaigns."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "referral routing not working in Financial Services Cloud after adding a new queue or business line"
  - "how to configure FSC referral types and map them to Lead record types using custom metadata"
  - "Referrer Score not visible for external partner on Experience Cloud community page"
  - "ReferralRecordTypeMapping custom metadata setup — what records are required and why"
  - "difference between Einstein Referral Scoring and Intelligent Need-Based Referrals in FSC"
  - "partner referral crediting Contact instead of User — is that correct behavior in FSC"
tags:
  - fsc-referral-management
  - financial-services-cloud
  - referral-routing
  - lead-assignment
  - referrer-score
  - experience-cloud
  - fsc-admin
inputs:
  - "FSC org with Referral Management enabled (Financial Services Cloud license required)"
  - "Existing Lead record types representing referral categories (e.g. Mortgage, Wealth Management, Insurance)"
  - "Lead Assignment Rules configured per the org routing model"
  - "Experience Cloud site configuration if external partner referrals are in scope"
  - "List of referral types and target queues required per business line"
outputs:
  - "Configured ReferralRecordTypeMapping__mdt entries for each referral type"
  - "Lead Assignment Rule entries keyed on Expressed Interest picklist values"
  - "ReferrerScore__c field enabled on Experience Cloud pages for partner visibility"
  - "Routing validation confirming each referral type assigns correctly end-to-end"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# FSC Referral Management

Use this skill when configuring FSC Referral Management: defining referral types via `ReferralRecordTypeMapping__mdt` custom metadata, routing referrals through Lead Assignment Rules keyed on the `Expressed Interest` picklist, understanding Referrer Score behavior, and enabling partner referral visibility in Experience Cloud. It activates whenever a practitioner needs to wire together the Lead-based referral data model, the custom metadata registry, the picklist-driven routing logic, and downstream queues or partner portals.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has Financial Services Cloud provisioned and Referral Management is enabled in FSC Settings (Setup > Financial Services Cloud Settings > Referral Management toggle).
- Identify all referral types the business requires. Each must map to both a Lead record type and a `ReferralRecordTypeMapping__mdt` entry — both are required for routing to function.
- Confirm whether external partners submit referrals via an Experience Cloud site. If so, Referrer Score visibility requires explicit layout or component configuration that is off by default.
- The most common wrong assumption: adding a new queue is sufficient for routing. It is not. The queue must be referenced in an active `ReferralRecordTypeMapping__mdt` entry or routing silently ignores it with no error.
- Do not treat Einstein Referral Scoring as an active feature to configure. It was announced for retirement; Intelligent Need-Based Referrals is the supported scoring capability.

---

## Core Concepts

### The Extended Lead Object

FSC Referral Management does not introduce a separate object. It extends the standard Lead object with 11 custom fields that carry referral-specific data:

- `ExpressedInterest__c` — picklist; the primary routing key for Lead Assignment Rules
- `ReferredBy__c` — lookup to User (internal referrer) or Contact (external partner referrer)
- `ReferrerScore__c` — integer 0–100 reflecting the referrer's historical conversion rate
- `ReferralType__c` — controlled by the record type selected at creation
- `ReferralDate__c`, `ReferralStatus__c`, `ReferralChannel__c`, and four additional contextual fields

Because referrals are Leads, all standard Lead capabilities apply without modification: duplicate rules, validation rules, workflow, Flow, reports, and list views all work as expected. However, referral-specific field visibility and page layouts must be managed per record type, and the referral features are only active when Referral Management is enabled in FSC Settings.

### ReferralRecordTypeMapping Custom Metadata

`ReferralRecordTypeMapping__mdt` is the authoritative registry that tells FSC which Lead record types are valid referral types. Every referral category the business uses must have an active entry. Each metadata record binds together the Lead record type developer name, a display label, and a target queue or owner. The platform reads this metadata at referral creation time to:

1. Confirm the record type is a valid referral type
2. Apply default routing prior to evaluating Assignment Rules
3. Expose the referral type in the FSC referral UI

**Critical behavior:** if a Lead record type is used in a referral but has no active `ReferralRecordTypeMapping__mdt` entry, the platform creates the Lead record silently and performs no assignment — no error, no notification. The referral appears successfully created while routing has completely failed. This is the most common silent production failure in FSC referral configurations.

### Lead Assignment Rule Routing via Expressed Interest

Once a referral type is registered in the metadata, fine-grained routing is controlled by standard Lead Assignment Rules. The `Expressed Interest` picklist is the primary routing key: each Assignment Rule entry filters on one or more picklist values (e.g. "Retirement Planning", "Home Loan", "Auto Loan") and directs the Lead to the appropriate queue or user.

Design implications:
- Routing changes do not require a metadata deployment — only Assignment Rule record updates
- All standard Lead Assignment Rule criteria are available (field values, formula criteria)
- A referral with an `Expressed Interest` value that matches no active rule entry lands in the default Lead owner or remains unassigned
- The Assignment Rule must be active and set as the default rule; having a rule that is not the active default has no effect

### Referrer Score

Referrer Score (`ReferrerScore__c`) is a platform-calculated integer 0–100 representing a referrer's historical conversion rate — how often their submitted referrals result in closed deals. It is read-only from an admin perspective; the platform updates it based on closed referral history.

Key behaviors by referrer type:
- **Internal referrers (employees/advisors):** `ReferredBy__c` is a User lookup; score is visible in standard Lead views without additional configuration
- **External partner referrers:** `ReferredBy__c` points to a Contact record (not User). This is by design — FSC credits the partner's Contact, not a User. `ReferrerScore__c` is not included in default Experience Cloud page layouts and must be explicitly added to the community page layout or a custom LWC

Referrer Score is part of FSC's Intelligent Need-Based Referrals feature, which is the active and supported capability. Do not conflate this with Einstein Referral Scoring, which was a separately-licensed, separately-configured feature that has been announced for retirement.

---

## Common Patterns

### Pattern: Registering a New Referral Type End-to-End

**When to use:** A new business line (e.g. Small Business Lending) needs to accept referrals through FSC Referral Management for the first time.

**How it works:**
1. Create or confirm a Lead record type named (e.g.) `SmallBusinessLending` with appropriate page layout.
2. Add the required picklist values to `Lead.ExpressedInterest__c` that will drive routing for this business line (e.g. "SBA Loan", "Business Line of Credit").
3. Create a `ReferralRecordTypeMapping__mdt` record: set the Lead record type developer name, label, and the target queue.
4. Create Lead Assignment Rule entries filtering on the new `Expressed Interest` values, routing to the Small Business Lending queue.
5. Deploy the custom metadata and picklist values together. Assignment Rule updates can follow in production.
6. Test by creating a referral with each new `Expressed Interest` value and confirming queue assignment via the Lead Assignment Log on the record.

**Why not the alternative:** Skipping the `ReferralRecordTypeMapping__mdt` entry (step 3) causes routing to silently fail. The referral is created and no error surfaces, but no queue assignment occurs. There is no indicator on the record that routing was skipped.

### Pattern: Enabling Partner Referrer Score Visibility in Experience Cloud

**When to use:** External partners or financial advisors submit referrals through an Experience Cloud site and need to see their own Referrer Score.

**How it works:**
1. Confirm that partner referral records use a Contact-based `ReferredBy__c` lookup. This is platform-default for partner referrals; do not change it.
2. In Experience Builder, navigate to the Lead or Referral detail page used by partner users.
3. Add `ReferrerScore__c` to the visible fields on the page layout or the custom component. If using an aura/LWC component, add the field to the component's field list explicitly.
4. Set field-level security: grant Read access to `ReferrerScore__c` for the Experience Cloud community profile (not just the internal admin profile).
5. Test by logging in as a partner community user and verifying the score is visible on their submitted referral records.

**Why not the alternative:** Granting FLS access alone is not sufficient if the field is absent from the page layout or component — the field will not render. Both FLS and layout placement are required.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New referral type needed for a new business line | Create Lead record type + ReferralRecordTypeMapping__mdt entry + Assignment Rule entries | All three are required; missing either the metadata entry or the assignment rule causes silent failure or unassigned referrals |
| Partner referral Referrer Score not visible in community | Add ReferrerScore__c to Experience Builder page layout and set FLS Read for community profile | Score is on a Contact-linked record; FLS and layout placement are both required |
| Routing logic needs to change without a deployment | Update Lead Assignment Rule criteria only — no metadata deployment needed | Assignment Rules are non-metadata config; ReferralRecordTypeMapping entries still require deployment |
| Einstein Referral Scoring is requested | Redirect to Intelligent Need-Based Referrals; document that Einstein Referral Scoring is retiring | Einstein Referral Scoring is a retiring/retired feature; do not configure or reference as current capability |
| Referral created but assigned to no queue | Check ReferralRecordTypeMapping__mdt for an active entry matching the record type; then check Assignment Rules for matching Expressed Interest values | Silent routing failure is almost always caused by a missing metadata record or an unmatched picklist value |
| Referral routing behaves inconsistently by picklist value | Audit Expressed Interest picklist values against Assignment Rule criteria for exact string match | Assignment Rules use exact picklist value match; any label mismatch causes the rule to not fire |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm feature enablement** — Verify FSC is provisioned and Referral Management is enabled in Setup > Financial Services Cloud Settings. Confirm the expected Lead record types for each referral category exist in the org with appropriate page layouts.
2. **Audit ReferralRecordTypeMapping__mdt** — Inspect all `ReferralRecordTypeMapping__mdt` records. Confirm every referral type the business requires has an active entry with the correct Lead record type developer name and a valid target queue or user. Flag any Lead record type used for referrals that is missing an entry.
3. **Audit Expressed Interest picklist values** — Confirm all routing-relevant picklist values exist on `Lead.Expressed Interest`. Any value used as an Assignment Rule filter criterion must exist in the picklist metadata or the rule will never match.
4. **Audit Lead Assignment Rules** — For each active referral type, confirm at least one Assignment Rule entry filters on `Expressed Interest` and routes to the correct queue or owner. Identify gaps and unmatched values.
5. **Verify Referrer Score access** — If partner referrals are in scope, confirm `ReferrerScore__c` is on the Experience Builder page layout for the community referral detail page and that FLS grants Read access to the community profile.
6. **Test routing end-to-end** — Create a test referral for each referral type and `Expressed Interest` combination. Confirm Lead record type, queue assignment, and Referrer Score visibility are all correct. Use the Lead Assignment Log on each record to diagnose any misroutes.
7. **Deploy and document** — Deploy `ReferralRecordTypeMapping__mdt` changes and picklist metadata via change set or source-based deployment. Document the referral type registry, routing matrix, and any Experience Cloud layout changes in the project runbook.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every active referral type has a corresponding active ReferralRecordTypeMapping__mdt entry
- [ ] Every Expressed Interest picklist value used in Assignment Rule routing exists in Lead field metadata
- [ ] Lead Assignment Rules cover all active referral types with no routing gaps or unmatched values
- [ ] ReferrerScore__c is visible on Experience Cloud pages if partner referrals are in scope (layout + FLS)
- [ ] Einstein Referral Scoring is NOT referenced in any new configuration, documentation, or automation
- [ ] Test referrals for each referral type result in correct queue assignment (verified via Lead Assignment Log)
- [ ] Field-level security for all 11 referral custom fields is correctly set for all relevant internal and community profiles

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Missing ReferralRecordTypeMapping silently drops routing** — A Lead record type used for referrals with no active `ReferralRecordTypeMapping__mdt` entry causes the platform to create the referral but skip all queue assignment with no error or warning surfaced anywhere on the record or in logs.
2. **Einstein Referral Scoring is retiring** — Einstein Referral Scoring for FSC was a separately-licensed feature announced for retirement. It must not be configured as a new capability or documented as a current feature. Intelligent Need-Based Referrals is the supported path.
3. **Partner referrals credit Contact, not User** — When a partner submits a referral through Experience Cloud, `ReferredBy__c` points to the partner's Contact record, not a User. Referrer Score is attributed to that Contact. Assuming all referrers are Users breaks lookups and score attribution for external partner scenarios.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ReferralRecordTypeMapping__mdt records | Deployed custom metadata entries registering each referral type and its target queue |
| Lead Assignment Rule configuration | Routing rules keyed on Expressed Interest picklist values directing referrals to the correct queues or users |
| Experience Builder page layout update | Updated community referral detail page surfacing ReferrerScore__c for partner users |
| Referral routing test log | End-to-end test records confirming correct assignment per referral type and Expressed Interest value |

---

## Related Skills

- admin/financial-account-setup — When closed referrals result in new FSC financial accounts, this skill governs account setup
- admin/experience-cloud-setup — For configuring the Experience Cloud site used by partner referrers submitting and tracking referrals
