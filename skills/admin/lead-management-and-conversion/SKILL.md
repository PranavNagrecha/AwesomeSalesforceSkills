---
name: lead-management-and-conversion
description: "Configuring Salesforce lead management and conversion: lead settings, web-to-lead, conversion field mapping, lead queues, auto-response rules, lead processes. Use when setting up lead capture, routing, or conversion for Sales Cloud. Trigger keywords: web-to-lead, lead conversion, lead field mapping, lead settings, lead process, lead queue, lead auto-response. NOT for lead assignment rule logic (use assignment-rules). NOT for duplicate rule configuration (use data-quality-and-governance)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - leads
  - lead-conversion
  - web-to-lead
  - lead-mapping
  - sales-cloud
  - lead-queues
triggers:
  - "how do I set up web-to-lead to capture leads from our website into Salesforce"
  - "custom fields on leads are not showing up on the contact after lead conversion"
  - "lead auto-response email is not being sent after web-to-lead submission"
  - "how does lead conversion field mapping work in Salesforce"
  - "web-to-lead is hitting the 500 daily limit and rejecting new submissions"
  - "how do I map lead fields to contact account and opportunity on conversion"
  - "lead is converted but the custom field data is missing on the resulting opportunity"
inputs:
  - "Whether web-to-lead capture is needed and the expected daily submission volume"
  - "Custom Lead fields that must survive conversion to Contact, Account, or Opportunity"
  - "Lead status picklist values and which value marks a record as converted"
  - "Whether auto-response emails should be sent to submitting leads"
  - "Lead routing targets: specific users, queues, or territory-based rules"
outputs:
  - "Configured web-to-lead form HTML with correct org ID and return URL"
  - "Lead field mapping configuration ensuring custom fields survive conversion"
  - "Lead process with correct status values and a designated converted status"
  - "Auto-response rule that fires reliably alongside assignment rules"
  - "Lead Settings configuration guidance (default owner, notification, conversion options)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Lead Management and Conversion

This skill activates when an admin needs to configure the full Salesforce lead lifecycle — from initial web capture through lead settings, routing, auto-response, field mapping, and conversion into Contacts, Accounts, and Opportunities. It covers the structural and configuration layer, not the assignment rule entry logic (see `assignment-rules` for that).

---

## Before Starting

Gather this context before working on lead management:

- **What is the expected web-to-lead volume?** Salesforce enforces a hard limit of 500 web-to-lead submissions per 24-hour rolling period per org. Exceeding this limit silently discards leads. Enterprise orgs with high inbound volume must plan for this constraint.
- **Which custom Lead fields must survive conversion?** Unmapped custom fields are silently dropped when a Lead converts. Identify every custom field that must carry over to Contact, Account, or Opportunity before beginning.
- **Is there an existing Lead process?** A Lead process defines which Status picklist values are available. Only one picklist value can be marked as the converted status. Confirm the current process or create a new one before enabling conversion.
- **Will auto-response emails be used?** Auto-response rules only fire when an assignment rule also fires on the same record. If no assignment rule is active or no rule entry matches, auto-response emails are silently skipped.

---

## Core Concepts

### Lead Settings

Lead Settings (Setup > Lead Settings) control three org-wide behaviors:

1. **Default Lead Owner** — The user or queue that owns a lead when no assignment rule is active or no rule entry matches. If this field is blank or the referenced user is inactive, unmatched web-to-lead submissions are discarded silently.
2. **Notify Default Lead Owner** — When checked, the default owner receives an email when they receive a lead through the assignment fallback. Not needed if the owner is a queue.
3. **Require Validation and Triggers from Lead Convert** — When checked, standard validation rules and Apex triggers run during conversion. When unchecked, conversion bypasses them. The default is unchecked. Enable this only intentionally — disabling it means business rules protecting Contact or Account data do not run during the conversion path.

### Web-to-Lead

Web-to-Lead generates an HTML form that submits lead data directly to Salesforce via a POST to `https://webto.salesforce.com/servlet/servlet.WebToLead`. Key platform constraints:

- **500 submissions per day (hard limit)** — This is a rolling 24-hour limit per org, not a calendar day. When the limit is reached, submissions return a generic error page and the lead is not created. reCAPTCHA v2 prevents automated spam bots from consuming this limit, but it is not enabled by default — you must check the CAPTCHA option when generating the form.
- **Default Web-to-Lead Creator user** — All web-to-lead submissions are owned by this system user initially before the assignment rule transfers ownership. If your org has a duplicate matching rule, this system user is typically included in the rule's bypass criteria. If it is not excluded, and a duplicate is found, the submission is silently rejected with no notification to the submitter or admin.
- **Return URL** — The `retURL` hidden field controls where the browser redirects after a successful submission. A missing or incorrect return URL causes a Salesforce-branded confirmation page that may confuse submitters.

### Lead Conversion Field Mapping

When a Lead is converted, Salesforce creates (or merges into) a Contact, an Account, and optionally an Opportunity. The conversion copies field values from Lead to the target object — but only for fields that are explicitly mapped in **Object Manager > Lead > Fields & Relationships > Map Lead Fields**.

Critical behaviors:

- **Unmapped custom fields are silently dropped.** There is no error, no warning, and no audit trail. Field data that is not mapped is simply not transferred. This is the single most common source of post-conversion data loss.
- **Data type mismatches cause silent failure.** A Lead text field mapped to a Contact picklist will not produce an error — it will silently fail to transfer the value if the text does not match a valid picklist option.
- **Standard fields have default mappings.** Standard Lead fields (First Name, Last Name, Phone, Email, Company, etc.) are pre-mapped to their Contact and Account equivalents. These default mappings cannot be removed, only supplemented.
- **One source field can map to only one target field per object.** A Lead custom field can map to one Contact field, one Account field, and one Opportunity field — three mappings total.

### Lead Process and Converted Status

A Lead process is a subset of the Lead Status picklist values assigned to a Record Type. The process controls which status values are shown to users working that record type's records. Exactly one Lead Status value must have the **Converted** checkbox enabled. When a user or process sets the lead to that status value, Salesforce triggers the conversion wizard (or the `Database.convertLead()` API method).

If the Lead Status picklist has no value with Converted checked, the conversion wizard will not be available. If a Lead process removes the converted status from its subset, users on that record type cannot complete conversion from the UI.

### Auto-Response Rules

Auto-response rules send an email to the lead submitter when a lead is captured via Web-to-Lead. The rule evaluates criteria against the incoming lead and selects an email template to send.

**Critical constraint:** Auto-response rules only fire when an active assignment rule also fires on the same record. If no assignment rule is active, or no rule entry matches the incoming lead, the auto-response rule is skipped — even if the auto-response criteria match. This coupling is undocumented in most places and is the primary reason auto-response emails silently stop working after assignment rule changes.

---

## Common Patterns

### Pattern: Capture Web Leads with reCAPTCHA and Daily-Limit Protection

**When to use:** Org uses Web-to-Lead as the primary inbound channel and must prevent spam bots from exhausting the 500/day limit.

**How it works:**
1. Setup > Web-to-Lead. Check "Enable reCAPTCHA" to add a CAPTCHA challenge to the generated form. Generate the form.
2. Add the required hidden fields to the form: `oid` (org ID), `retURL`, and any custom fields mapped from Lead.
3. Set a concrete `retURL` pointing to a thank-you page on your domain — not `https://www.salesforce.com`.
4. Test submission from a non-Salesforce IP. Confirm the Lead appears in the org and that the Default Lead Owner or assignment rule target receives it.
5. Set up a daily alert (via a Scheduled Flow or report subscription) on lead creation count to warn before the 500 limit is approached.

**Why not skip CAPTCHA:** Without CAPTCHA, a bot submitting 500 requests can exhaust the daily limit in seconds, blocking all legitimate submissions for the rest of the 24-hour window.

### Pattern: Zero Data Loss Lead Conversion Field Mapping

**When to use:** The org has custom Lead fields (source, campaign details, qualification scores) that must be available on Contact, Opportunity, or Account after conversion.

**How it works:**
1. Inventory every custom field on the Lead object. For each field, determine the target object (Contact, Account, Opportunity) and whether a corresponding custom field exists there.
2. Create matching custom fields on target objects if they do not exist. Match the data type exactly — Text-to-Text, Number-to-Number, Picklist-to-Picklist with identical API values.
3. Navigate to Object Manager > Lead > Fields & Relationships > Map Lead Fields. Map each custom Lead field to its target field(s).
4. Run a conversion of a test Lead in a sandbox and verify field values appear on all three resulting records.
5. Document unmapped fields explicitly — some Lead fields (marketing attribution, prospect scoring) intentionally do not map to CRM objects. Document the decision so future admins do not re-investigate the "missing" data.

**Why this matters:** Salesforce does not warn you when a field is unmapped. The data disappears silently at conversion time and cannot be recovered without re-examining the original Lead record (which remains in the database as IsConverted = true).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| High-volume web lead capture (near 500/day) | Enable reCAPTCHA on web-to-lead form; monitor daily count | Bots can exhaust the limit in minutes without CAPTCHA |
| Custom Lead fields must survive conversion | Map every field in Object Manager > Lead > Map Lead Fields | Unmapped fields are silently dropped at conversion |
| Lead data type differs from target field type | Create matching target field with same data type | Type mismatch causes silent transfer failure |
| Auto-response emails not firing | Confirm active assignment rule exists and has a matching entry | Auto-response only fires when assignment rule also fires |
| Lead routing not working for API-created leads | Add `Sforce-Auto-Assign: true` header or use `DMLOptions.assignmentRuleHeader` | Assignment rules do not run automatically for API DML |
| Conversion triggers validation rules causing errors | Review Lead Settings > "Require Validation and Triggers from Lead Convert" | Deliberately enable or disable based on business requirements |
| Need scored lead routing (Einstein) | Use Einstein Prediction Builder or Flow-based point scoring | Native lead scoring is not built in; these are the two declarative approaches |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Gather context** — Confirm org edition, expected web-to-lead volume, custom field inventory on Lead, and which status value is the converted status.
2. **Audit Lead Settings** — Verify Default Lead Owner is an active user or queue. Check whether validation and triggers should run during conversion.
3. **Configure web-to-lead** — Enable reCAPTCHA, generate the form, set a proper retURL, and test end-to-end from a non-Salesforce IP address.
4. **Map conversion fields** — Open Object Manager > Lead > Fields & Relationships > Map Lead Fields. Map every custom field that must survive conversion. Verify data types match on source and target.
5. **Configure auto-response rule** — Ensure an active assignment rule exists before creating auto-response rules. Test by submitting a web-to-lead form and confirming the response email arrives.
6. **Validate with conversion test** — Convert a test Lead in sandbox. Confirm Contact, Account, and Opportunity all carry expected field values. Check for silent data loss.
7. **Review checklist and run checker script** — Run `check_lead_management.py` against the metadata export and review the checklist below.

---

## Review Checklist

Run through these before marking lead management configuration complete:

- [ ] Default Lead Owner in Lead Settings is an active user or queue
- [ ] Web-to-Lead form has reCAPTCHA enabled if public-facing
- [ ] `retURL` in web-to-lead form points to a meaningful thank-you page (not Salesforce.com)
- [ ] Every custom Lead field that must survive conversion is mapped in Object Manager > Lead > Map Lead Fields
- [ ] Target fields for conversion mapping use matching data types (Text-to-Text, Picklist-to-Picklist with identical API values)
- [ ] Exactly one Lead Status value has the Converted checkbox enabled
- [ ] Auto-response rule exists only where an active assignment rule is also configured
- [ ] Web-to-lead tested end-to-end from non-Salesforce IP with expected Lead created
- [ ] Test Lead converted in sandbox; Contact, Account, and Opportunity field values verified
- [ ] Daily lead volume monitoring in place if web-to-lead volume approaches 500/day

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Unmapped custom fields are silently dropped on conversion** — No error, no warning. Any Lead custom field not mapped in Object Manager > Lead > Map Lead Fields simply does not transfer. This is the leading cause of post-conversion data loss in Sales Cloud implementations.
2. **Auto-response rules require assignment rules to fire** — If no active assignment rule exists, or no rule entry matches the incoming lead, auto-response emails are not sent — even if the auto-response criteria match perfectly. This coupling causes silent email failures after routine assignment rule changes.
3. **Web-to-Lead duplicate matching silently rejects submissions** — If a duplicate matching rule matches the incoming submission to an existing record, and the Default Web-to-Lead Creator user is not excluded from the matching rule's bypass conditions, the submission is silently discarded. The submitter sees a confirmation page but no Lead is created.
4. **500/day is a rolling limit, not midnight-reset** — The web-to-lead limit is a 24-hour rolling window, not a calendar day. Blocking that begins at 3 PM does not clear at midnight — it clears 24 hours after the first submission in the burst.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Web-to-Lead HTML form | Generated form with correct org ID, reCAPTCHA, hidden fields, and retURL |
| Lead field mapping configuration | Object Manager configuration ensuring custom fields survive conversion |
| Lead process definition | Status picklist subset with one value marked as the converted status |
| Auto-response rule | Criteria-based email rule paired with an active assignment rule |
| Lead Settings documentation | Recorded configuration of Default Lead Owner and conversion trigger settings |

---

## Related Skills

- assignment-rules — configure the routing logic that determines which user or queue receives each lead; required for auto-response rules to fire
- data-quality-and-governance — configure duplicate matching rules that apply to leads including web-to-lead submissions
- standard-object-quirks — covers edge cases in Database.convertLead() API usage and field preservation patterns for Apex-driven conversion
