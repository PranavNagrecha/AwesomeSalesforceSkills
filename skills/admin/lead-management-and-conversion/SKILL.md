---
name: lead-management-and-conversion
description: "Configuring Salesforce lead management and conversion in Setup: lead settings, web-to-lead, conversion field mapping, lead queues, auto-response rules, lead processes. Trigger keywords: web-to-lead, lead conversion, lead field mapping, lead settings, lead process, lead queue, lead auto-response. NOT for Apex that controls what conversion creates - use apex/lead-conversion-customization. NOT for lead assignment rule logic - use admin/assignment-rules. NOT for duplicate rule configuration - use admin/duplicate-management. Also covers: LeadConvertSettings objectMapping XML, LeadConfigSettings, LeadStatus StandardValueSet converted flag, lead process BusinessProcess, Database.convertLead bulk conversion limits."
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
  - "converted lead did not update the phone number on the existing contact"
  - "opportunity created by lead conversion has the wrong record type"
  - "too many DML statements error when mass converting leads in Apex"
  - "deploy LeadConvertSettings objectMapping between sandbox and production"
  - "cannot convert a lead owned by a queue"
  - "why is the picklist default value blank on records created by lead conversion"
  - "can a lead status picklist have more than one converted value"
  - "cannot edit a converted lead record"
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
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Lead Management and Conversion

This skill activates when an admin needs to configure the full Salesforce lead lifecycle — from initial web capture through lead settings, routing, auto-response, field mapping, and conversion into Contacts, Accounts, and Opportunities. It covers the structural and configuration layer, not the assignment rule entry logic (see `assignment-rules` for that).

---

## Before Starting

Gather this context before working on lead management:

- **What is the expected web-to-lead volume?** Salesforce enforces a hard limit of 500 web-to-lead submissions per 24-hour rolling period per org. Exceeding this limit silently discards leads. Enterprise orgs with high inbound volume must plan for this constraint.
- **Which custom Lead fields must survive conversion?** Unmapped custom fields are silently dropped when a Lead converts. Identify every custom field that must carry over to Contact, Account, or Opportunity before beginning.
- **Is there an existing Lead process?** A Lead process is a `BusinessProcess` on Lead that defines which Status picklist values a record type exposes. At least one Status value must carry `converted = true`, and more than one may — `LeadStatus.IsConverted` is documented as "Multiple lead status values can represent a converted lead" (Object Reference, LeadStatus). Confirm the current process, and which of its values are converted values, before enabling conversion.
- **Will auto-response emails be used?** Auto-response rules only fire when an assignment rule also fires on the same record. If no assignment rule is active or no rule entry matches, auto-response emails are silently skipped.

---

## Questions to Ask Before Configuring

Ask these before opening Setup. Each one traces to a gotcha that is invisible until production, and an
LLM that skips them produces a conversion path that reports success and loses data.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which custom Lead fields must exist on the Contact, Account, or Opportunity afterwards — and which are deliberately Lead-only?" | Unmapped custom fields are dropped with no error (Gotcha 1); undocumented omissions get re-investigated every year | The `objectMapping` rows for `settings/LeadConvert.settings-meta.xml`, plus a written not-mapped list |
| "How often do reps convert into an *existing* Account or Contact rather than creating new ones?" | Merge into an existing record fills only empty fields; newer Lead data is discarded (Gotcha 7) | A decision on whether an after-conversion enrichment step is needed, or the gap is accepted |
| "Does this org use record types on Lead, Account, Contact, or Opportunity, and does conversion change the owner?" | The *new owner's* default record type shapes the created records; the *converting user's* constrains Lead Source (Gotcha 8) | A profile × record-type matrix, and a decision on `doesPreserveLeadStatus` |
| "Do any leads sit in a queue when they get converted?" | Accounts and Contacts cannot be owned by a queue, so an owner must be supplied explicitly (Gotcha 10) | `allowOwnerChange = true`, and an owner-resolution rule for any automated conversion |
| "Will anything convert leads in bulk — a backfill, a Flow on a data load, a mass-convert button?" | `Database.convertLead` spends a DML *statement*, capped at 150 per transaction, with 100 objects per call (Gotcha 11) | A chunked service with `allOrNone = false` instead of a per-record loop |
| "Which validation rules or required fields on Account, Contact, Opportunity, or Task must hold at conversion?" | Conversion does not enforce them until Require Validation for Converted Leads is on, and turning it on can break working conversions (Gotcha 6) | A deliberate on/off decision plus a sandbox regression run before release |
| "Is Web-to-Lead in scope, and is there an active Block duplicate rule on Lead?" | A Block rule that matches a submission discards it silently (Gotcha 4) | A `duplicateRuleFilter` exempting the Web-to-Lead user, or a switch to Allow + alert |

What a proper configuration adds over just clicking Convert: every field the business relies on is
either mapped or explicitly documented as not mapped, the created records land on the record types and
owners someone actually chose, bulk conversion survives its own governor limits, and the compliance
rules that are supposed to hold at conversion demonstrably do.

---

## Core Concepts

### Lead Settings

Lead Settings (Setup > Lead Settings) control three org-wide behaviors. The deployable half of that
page is `LeadConfigSettings` — `settings/LeadConfig.settings-meta.xml`, package.xml member
`LeadConfig`, API 47.0+ (Metadata API Guide, `LeadConfigSettings`). The Default Lead Owner is *not* in
that type and is not exposed by the Metadata API at all; it is a per-org Setup value that must be set
by hand in every sandbox and in production.

1. **Default Lead Owner** — The user or queue that owns a lead when no assignment rule is active or no rule entry matches. If this field is blank or the referenced user is inactive, unmatched web-to-lead submissions are discarded silently.
2. **Notify Default Lead Owner** — When checked, the default owner receives an email when they receive a lead through the assignment fallback. Not needed if the owner is a queue.
3. **Require Validation for Converted Leads** — `shouldLeadConvertRequireValidation` in
   `LeadConfigSettings`. While it is off, conversion does **not** enforce validation rules or
   universally required custom fields on the Account, Contact, Opportunity, or Task records it
   creates, and Salesforce ignores lookup filters when converting leads. Turning it on enforces all
   three on the conversion path, so conversions that previously succeeded can start failing. Apex
   triggers fire during conversion either way. See `references/gotchas.md` Gotcha 6 for the
   enablement path and its two regression risks.

   UNVERIFIED (2026-09-05): the two authorities disagree on the default. This skill's Help-sourced
   text (v1.1.0) says the checkbox ships unchecked; the Metadata API Guide's `LeadConfigSettings`
   field table says `shouldLeadConvertRequireValidation` has "Default value is true". Neither doc
   available here resolves which applies to a brand-new org versus a Metadata API deploy that omits
   the element. Read the current value out of the target org rather than assuming either default:
   `sf project retrieve start --metadata "Settings:LeadConfig"`.

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
- **One source field can map to only one target field per object.** A Lead custom field can map to one Contact field, one Account field, and one Opportunity field — three mappings total. This is the `objectMapping` structure of `LeadConvertSettings`: up to three `objectMapping` blocks (one each for Account, Contact, Opportunity), each holding `mappingFields` pairs of `inputField` / `outputField`, with `inputObject` always `Lead` (Metadata API Guide, `LeadConvertSettings`). See `references/metadata-examples.md` §1.
- **Custom field default values do not fire.** "Default values are not used for lead conversion, importing, or merging records" (Object Reference, Default Values in Custom Fields). Standard *picklist* defaults do apply; custom field defaults do not. Gotcha 9.

### Lead Process and Converted Status

A Lead process is a `BusinessProcess` component on the Lead object — a subset of the Lead Status
picklist values, attached to a Record Type. The process controls which status values are shown to
users working that record type's records. **At least one** Lead Status value must have the
**Converted** flag (`converted` on the `StandardValue`, `IsConverted` on the queryable `LeadStatus`
object). More than one may: "Multiple lead status values can represent a converted lead" (Object
Reference, `LeadStatus.IsConverted`), which is how orgs distinguish self-sourced from partner-sourced
conversions on the same picklist.

Two corrections to a common mental model:

- **Setting Status to a converted value does not convert the lead.** "You can't convert a lead via the
  API by changing Status to one of the converted lead status values" (Object Reference, Lead Status
  Picklist). Conversion is a distinct operation — the Convert dialog in the UI, or
  `Database.convertLead()` in Apex, which "is available only as a method on the Database class; it is
  not available as a DML statement" (Apex Developer Guide, Converting Leads). A Flow or trigger that
  "converts" a lead by writing Status has changed a picklist and nothing else.
- **Never hardcode the converted status label.** The documented pattern is to query it:
  `SELECT ApiName FROM LeadStatus WHERE IsConverted = true` (Apex Developer Guide, Converting Leads,
  step 5). Labels get renamed; the query does not break.

If the Lead Status picklist has no value with Converted set, the conversion wizard will not be
available. If a Lead process omits every converted status from its subset, users on that record type
cannot complete conversion from the UI.

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
| Conversion triggers validation rules causing errors | Review Lead Settings > "Require Validation for Converted Leads" | Deliberately enable or disable based on business requirements |
| Need scored lead routing (Einstein) | Use Einstein Prediction Builder or Flow-based point scoring | Native lead scoring is not built in; these are the two declarative approaches |
| Converting more than ~100 leads in one transaction | Chunk into `List<Database.LeadConvert>` of 100, call `Database.convertLead(chunk, false)` per chunk | Each call spends one of the 150 DML statements; the guide caps a call at 100 objects |
| Reps convert into existing Accounts/Contacts and expect newer Lead data to win | Add an explicit after-conversion update keyed on `ConvertedContactId` | Merge fills empty target fields only; existing values are never overwritten |
| Two conversion outcomes must be reportable separately (self-sourced vs partner) | Add a second Lead Status value with `converted = true` | Multiple status values may represent a converted lead |
| Conversion must never create an Opportunity | `opportunityCreationOptions = NotVisible` (dialog) or `setDoNotCreateOpportunity(true)` (Apex) | Two different switches; `doesSelectNoOpportunityOnConvertLead` overlaps — pick one and document it |

---

## Recommended Workflow

1. **Retrieve the current conversion metadata before editing anything.** `sf project retrieve start
   --metadata "Settings:LeadConvert" --metadata "Settings:LeadConfig" --metadata
   "StandardValueSet:LeadStatus" --metadata "CustomObject:Lead"`. `StandardValueSet` deploys
   deactivate any value omitted from the file, so authoring `LeadStatus` from scratch silently kills
   picklist values. `references/metadata-examples.md` §3.

2. **Answer the seven questions above and build the field inventory.** For every custom Lead field,
   record its target object, the target field's API name, and its type — or record it as deliberately
   not mapped. Type must match: Text→Text, Number→Number, Picklist→Picklist with identical API values
   (Gotcha 5). This inventory *is* the `objectMapping` blocks.

3. **Write the metadata.** `settings/LeadConvert.settings-meta.xml` for the mappings
   (`metadata-examples.md` §1), `settings/LeadConfig.settings-meta.xml` for
   `shouldLeadConvertRequireValidation` / `doesPreserveLeadStatus` (§2),
   `standardValueSets/LeadStatus.standardValueSet-meta.xml` for the converted flags (§3), and the
   `businessProcesses` block inside `objects/Lead/Lead.object-meta.xml` (§4). Deploy them as one
   manifest — the target `CustomField` entries must exist before `LeadConvert` can reference them
   (§7).

4. **Run the checker against the manifest directory.**
   `python3 skills/admin/lead-management-and-conversion/scripts/check_lead_management_and_conversion.py
   --manifest-dir force-app/main/default`. It resolves every `objectMapping` field pair against the
   `CustomField` files in the manifest, checks type compatibility where both sides are present,
   verifies a converted `LeadStatus` value exists, and flags Apex that calls `convertLead` inside a
   loop or without partial-success handling.

5. **Deploy to a sandbox and convert three deliberately awkward leads.** One queue-owned (Gotcha 10),
   one merging into an existing Account with populated fields (Gotcha 7), one owned by a user whose
   default record type differs from the converting user's (Gotcha 8). The single happy-path test that
   most people run passes in all three broken configurations.

6. **Verify with SOQL, not by eyeballing the record page.** Run the three queries in
   `metadata-examples.md` §8. Query 3 is the gate: a Lead with a populated source field whose
   `ConvertedContact.<target>` is null is a mapping that did not take.

7. **Configure the intake path last, if Web-to-Lead is in scope.** Generate the form with reCAPTCHA
   enabled, set a real `retURL`, confirm an active assignment rule with a catch-all entry exists
   *before* the auto-response rule (Gotcha 2), and add a `duplicateRuleFilter` exempting the
   Web-to-Lead user from any Block duplicate rule (`metadata-examples.md` §5). Then work the Review
   Checklist below.

## Review Checklist

Run through these before marking lead management configuration complete:

- [ ] Default Lead Owner in Lead Settings is an active user or queue
- [ ] Web-to-Lead form has reCAPTCHA enabled if public-facing
- [ ] `retURL` in web-to-lead form points to a meaningful thank-you page (not Salesforce.com)
- [ ] Every custom Lead field that must survive conversion is mapped in Object Manager > Lead > Map Lead Fields
- [ ] Target fields for conversion mapping use matching data types (Text-to-Text, Picklist-to-Picklist with identical API values)
- [ ] At least one Lead Status value has the Converted flag set, and every Lead process subset includes one of them
- [ ] `shouldLeadConvertRequireValidation` reflects a deliberate decision read out of the target org (not assumed); if any compliance rule on Account, Contact, Opportunity, or Task must hold at conversion, it is on
- [ ] Auto-response rule exists only where an active assignment rule is also configured
- [ ] Web-to-lead tested end-to-end from non-Salesforce IP with expected Lead created
- [ ] Test Lead converted in sandbox; Contact, Account, and Opportunity field values verified
- [ ] Daily lead volume monitoring in place if web-to-lead volume approaches 500/day
- [ ] A queue-owned lead has been converted successfully in sandbox (an owner is supplied, or `allowOwnerChange` is `true`)
- [ ] A merge-into-existing-Account conversion has been tested, and any field the business expects to be refreshed has an explicit after-conversion step
- [ ] Record-type defaults checked for every profile that converts and every profile that receives ownership; `doesPreserveLeadStatus` set deliberately
- [ ] No target field relies on a custom-field default value to be populated at conversion
- [ ] Any Apex or invocable conversion path chunks at 100 and passes `allOrNone = false`
- [ ] The converted status is resolved by `SELECT ApiName FROM LeadStatus WHERE IsConverted = true`, never hardcoded
- [ ] `python3 scripts/check_lead_management_and_conversion.py --manifest-dir <dir>` reports no issues

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Unmapped custom fields are silently dropped on conversion** — No error, no warning. Any Lead custom field not mapped in Object Manager > Lead > Map Lead Fields simply does not transfer. This is the leading cause of post-conversion data loss in Sales Cloud implementations.
2. **Auto-response rules require assignment rules to fire** — If no active assignment rule exists, or no rule entry matches the incoming lead, auto-response emails are not sent — even if the auto-response criteria match perfectly. This coupling causes silent email failures after routine assignment rule changes.
3. **Web-to-Lead duplicate matching silently rejects submissions** — A Block-action duplicate rule that matches an incoming submission discards it. The submitter sees a confirmation page and no Lead is created. Scope the rule away from the Web-to-Lead user with a `duplicateRuleFilter` on the `User` table; `securityOption` is not a user exemption.
4. **500/day is a rolling limit, not midnight-reset** — The web-to-lead limit is a 24-hour rolling window, not a calendar day. Blocking that begins at 3 PM does not clear at midnight — it clears 24 hours after the first submission in the burst.
5. **Merging into an existing record fills blanks only** — Newer Lead values never overwrite populated Account or Contact fields. `setOverwriteLeadSource` is the sole documented exception, and it covers one field.
6. **The new owner's record type drives the created records** — Not the Lead's. The converting user's record type separately constrains which Lead Source values appear in the dialog.
7. **Custom field default values are skipped at conversion** — Standard picklist defaults apply; custom field defaults do not.
8. **`convertLead` spends a DML statement, not a row** — A per-lead loop dies at 151 leads. The documented ceiling is 100 `LeadConvert` objects per call.
9. **Converted leads are read-only** — Backfilling a flag onto them needs View and Edit Converted Leads; write remediation state to the target record instead.

Full detail, with source lines, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Web-to-Lead HTML form | Generated form with correct org ID, reCAPTCHA, hidden fields, and retURL |
| `settings/LeadConvert.settings-meta.xml` | Deployable `objectMapping` blocks ensuring custom fields survive conversion |
| Lead process definition | `businessProcesses` block on Lead whose subset includes at least one converted status value |
| Auto-response rule | Criteria-based email rule paired with an active assignment rule |
| Lead Settings documentation | Recorded Default Lead Owner (Setup-only, not deployable) plus the deployed `LeadConfigSettings` values |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable XML — `LeadConvertSettings` mappings, `LeadConfigSettings`, `LeadStatus` values, the lead process, the duplicate-rule exemption, the bulk Apex service, package.xml and the verification SOQL |
| `references/gotchas.md` | Conversion "worked" but the data is wrong, missing, or on the wrong record type — twelve platform behaviours with sources |
| `references/examples.md` | You want a worked end-to-end scenario: Web-to-Lead form, a mapping fix with backfill, an auto-response rule that actually fires |
| `references/well-architected.md` | Justifying Web-to-Lead vs API intake, or writing the monitoring that makes silent failures visible |
| `references/llm-anti-patterns.md` | Reviewing AI-generated lead guidance before it reaches an org |

---

## Related Skills

- admin/assignment-rules — the routing logic that decides which user or queue receives each lead; auto-response rules do not fire without it
- admin/duplicate-management — matching and duplicate rules on Lead, including the Block-action behaviour that silently drops Web-to-Lead submissions
- apex/lead-conversion-customization — trigger and Apex control over what conversion creates, beyond the declarative mapping
- admin/standard-object-quirks — edge cases in `Database.convertLead()` usage and field-preservation patterns
- data/data-quality-and-governance — the org-wide data quality programme that conversion feeds
- data/lead-data-import-and-dedup — loading leads at volume and deduplicating them before they reach the conversion path
- admin/queues-and-public-groups — the queues leads sit in, and why a queue-owned lead needs an explicit owner at conversion
