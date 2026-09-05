# Gotchas — Lead Management and Conversion

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Unmapped Custom Lead Fields Are Silently Dropped on Conversion

**What happens:** When a Lead is converted, Salesforce creates or merges into a Contact, an Account, and optionally an Opportunity. Only fields explicitly mapped in Object Manager > Lead > Fields & Relationships > Map Lead Fields are transferred. Any custom field not mapped is silently ignored — no error, no warning in the UI, no entry in debug logs. The data remains on the original Lead record (which is preserved with `IsConverted = true`) but never reaches the target object.

**When it occurs:** Every Lead conversion where unmapped custom fields hold values. Most commonly discovered after the first production conversion wave when sales reps report missing qualification data on new Contacts and Opportunities.

**How to avoid:** Before adding any custom field to Lead in production, immediately create the corresponding field on the target object and map it. Treat "create field" and "map field" as a single atomic step. Include a field mapping audit in every change set or deployment checklist that touches Lead custom fields.

---

## Gotcha 2: Auto-Response Rules Only Fire When an Assignment Rule Also Fires

**What happens:** An auto-response rule is configured with correct criteria and a valid email template, but no confirmation email is ever sent to lead submitters. The rule shows no errors. Salesforce simply skips auto-response rule evaluation when no active assignment rule fires on the same record.

**When it occurs:** Whenever an assignment rule is missing, deactivated, or has no matching entry for the incoming lead. This most commonly surfaces after an org admin deactivates an assignment rule (intending to rebuild it), or after a rule entry order change causes some leads to fall through without matching any entry. It also affects orgs that have never set up assignment rules at all and assumed auto-response would work independently.

**How to avoid:** Always verify an active assignment rule with a catch-all entry exists before relying on auto-response rules. When troubleshooting missing auto-response emails, the first check should be: "Did the assignment rule fire on this Lead?" Check the Lead's Assignment Rule field (if visible) or audit via debug logs.

---

## Gotcha 3: Web-to-Lead Daily Limit Is 500 Per Org, Rolling 24 Hours (Not Calendar Day)

**What happens:** Once 500 web-to-lead submissions are received within any rolling 24-hour window, subsequent submissions return an error page and are not created as Leads. The limit counter does not reset at midnight — it is a rolling window. An attack or campaign spike at 3 PM that consumes all 500 submissions will not clear until 3 PM the following day.

**When it occurs:** During email campaigns, paid ad launches, or bot attacks that drive high form submission volume. Orgs with reCAPTCHA disabled are particularly vulnerable because automated bots can exhaust the limit in seconds.

**How to avoid:** Enable reCAPTCHA when generating the web-to-lead form in Setup. For orgs expecting sustained high volume (near or above 500/day), supplement web-to-lead with the Salesforce API (REST or SOAP) — API-based lead insertion has no equivalent daily limit. Set up a report subscription or Scheduled Flow to alert admins when daily lead creation volume exceeds 400 so they can respond before the limit is hit.

---

## Gotcha 4: Duplicate Matching Rules Silently Reject Web-to-Lead Submissions

**What happens:** If a duplicate matching rule is active and matches an incoming web-to-lead submission to an existing Lead or Contact record, Salesforce blocks the submission silently. The submitter sees the `retURL` confirmation page as though the form was accepted, but no Lead is created in the org and no admin notification is sent.

**When it occurs:** When an org has an active duplicate rule with the Action set to "Block" (not "Allow") and the Default Web-to-Lead Creator user is not excluded from the rule's bypass conditions. This is most common in orgs that enable duplicate management broadly without accounting for the web-to-lead system user context.

**How to avoid:** Review active duplicate matching rules for the Lead object. For each rule where Action = Block: confirm that the "Bypass Sharing" or profile-based bypass includes the Default Web-to-Lead Creator system user, or switch the action to "Allow" with "Alert" so that duplicate submissions are flagged but still created.

---

## Gotcha 5: Picklist Value Mismatches on Field Mapping Cause Silent Transfer Failure

**What happens:** A Lead picklist field is mapped to a Contact or Opportunity picklist field. On conversion, if the Lead's current picklist value does not exist as a valid picklist value on the target object's field, the value is silently dropped — the target field is left blank rather than throwing a conversion error.

**When it occurs:** When the source and target picklist fields diverge over time (values added to Lead but not to the target field, or values renamed). Also common when a Lead picklist field is mapped to a target field of a different data type (e.g., Lead text field mapped to Contact picklist).

**How to avoid:** Keep picklist value sets synchronized between Lead and target object fields when field mapping is in use. Use Global Value Sets (Setup > Picklist Value Sets) for picklist fields that are shared across Lead and its conversion targets — this ensures values stay in sync automatically. After any picklist value addition or rename on a mapped Lead field, immediately apply the same change to the target field.

---

## Gotcha 6: Validation Rules on Account, Contact, Opportunity, and Task Do Not Fire During Lead Conversion by Default

**What happens:** Conversion creates Account, Contact, Opportunity, and Task records, but by default that path does not enforce validation rules or universally required custom fields on those objects. Salesforce's *Considerations for Converting Leads* states that when the **Require Validation for Converted Leads** checkbox on the Lead Settings page is disabled, "Salesforce ignores lookup filters when converting leads." A rule set that looks complete therefore has an unmarked hole at the single highest-value moment in the sales process — no error, no warning, and the resulting records are indistinguishable from compliant ones.

**When it occurs:** In every org that has never touched Lead Settings — the checkbox ships unchecked. It typically surfaces during a data-quality or compliance audit, when the records violating an "always enforced" rule turn out to have all been created by lead conversion.

**How to avoid:** Setup > Feature Settings > Marketing > Lead Settings (Classic: Setup > Customize > Leads > Lead Settings) > Edit > check **Require Validation for Converted Leads** > Save. If the checkbox is not on the page, the org first needs the **Use Apex Lead Convert** permission, which requires a System Administrator to raise an activation request with Salesforce Support. Two things to regression-test in a sandbox before releasing the change:

1. Enabling it also switches on required-field settings and — per Salesforce's *Enable Use Apex Lead Convert for Validation Rules* article — Workflow Rules and Process Builder for the conversion path, so conversions that previously succeeded can start failing. Apex triggers are not part of this switch: *Considerations for Converting Leads* states plainly that during lead conversion, triggers fire. Validation failures surface as bold red text below the Converted Status picklist; required-field failures surface as `REQUIRED_FIELD_MISSING` and lookup-filter failures as `FIELD_FILTER_VALIDATION_EXCEPTION`.
2. Enabling it can remove previously configured conversion field mappings — Salesforce's guidance is to document the existing mappings before the activation is applied. Re-verify Object Manager > Lead > Fields & Relationships > Map Lead Fields immediately afterward, or Gotcha 1 fires on every conversion from that point on.

---

## Gotcha 7: Merging Into an Existing Account or Contact Only Fills Empty Fields — Never Overwrites

**What happens:** When conversion merges a Lead into an existing Account or Contact (the rep picks
"Choose existing account" in the dialog, or Apex calls `setAccountId` / `setContactId`), the Apex
Developer Guide is unambiguous: "If data is merged into existing account and contact objects, only
empty fields in the target object are overwritten — existing data (including IDs) are not
overwritten" (apexdev.txt L8353–8356). A Lead carrying a corrected phone number, a new title, or a
fresh mailing address contributes none of it if the target already has a value. The conversion
reports success. The stale data stays.

**When it occurs:** On every merge-into-existing conversion, which is the majority of conversions in
any org with an established Account base. It is invisible because the mapping is configured
correctly — the mapping fired, the target simply refused the write.

**How to avoid:** Treat merge-into-existing as an enrichment gap, not a data transfer. The one
documented exception is `LeadSource` on the target Contact: `setOverwriteLeadSource(true)` (which
also requires `setContactId`) overwrites that single field and nothing else
(apexrefguide.txt L149379–149384). For any other field that must reflect the newer Lead value, write
it in an after-conversion step keyed on `Lead.ConvertedContactId` / `ConvertedAccountId` rather than
expecting the mapping to do it. Say so explicitly in the design doc, because "the mapping is
configured" reads as "the data moves".

---

## Gotcha 8: The New Owner's Record Type — Not the Lead's — Decides What the Converted Records Look Like

**What happens:** Three separate defaults are resolved from a record type at conversion time, and none
of them is the Lead's own:

- "If the organization uses record types, the default record type of the new owner is assigned to
  records created during lead conversion" (apexdev.txt L8360–8361).
- "The default record type of the user converting the lead determines the lead source values
  available during conversion" (apexdev.txt L8361–8363) — so the *converting user*, not the owner,
  constrains the Lead Source picklist.
- Blank standard Lead picklist fields are filled with target defaults, and "if your organization uses
  record types, blank values are replaced with the default picklist values of the new record owner"
  (apexdev.txt L8364–8367).

On top of that, the Lead's own Status can change: with record types in play, "the lead status changes
to the lead status value of the new owner's record type during conversion" unless
`doesPreserveLeadStatus` is `true` (api_meta.txt L121037–121045).

**When it occurs:** Any org with Lead, Account, Contact or Opportunity record types where conversion
reassigns ownership — round-robin routing, queue-to-rep handoff, partner-sourced leads converted by an
ops user. The symptom is Opportunities landing on the wrong record type and Lead Source values a rep
swears they picked being absent from the dialog.

**How to avoid:** Map the record-type defaults of every profile that converts *and* every profile that
receives ownership, before go-live — the matrix, not a spot check. Set
`doesPreserveLeadStatus` to `true` in `settings/LeadConfig.settings-meta.xml`
(`metadata-examples.md` §2) unless the status swap is deliberate. If Lead Source values are missing
from the dialog, the fix is to add them to the converting user's default record type, not to the Lead
record type.

---

## Gotcha 9: Field Default Values Do Not Apply During Lead Conversion

**What happens:** A custom field on Account, Contact or Opportunity with a default value formula is
created **blank** by lead conversion. The Object Reference states it flatly: "Default values are not
used for lead conversion, importing, or merging records" (object_reference.txt L3214). This is a
different mechanism from the standard-picklist defaults in Gotcha 8, which *do* apply — custom field
defaults do not, standard picklist defaults do.

**When it occurs:** Every conversion, in any org that leans on default values for required-ish fields
(`Region__c` defaulting to the user's region, `Source_System__c` defaulting to `'Salesforce'`,
tier/segment fields defaulting to a baseline). It typically surfaces as a downstream report or
automation that filters on the defaulted field and quietly excludes every converted record.

**How to avoid:** Never let a defaulted custom field be the only source of a value the business
depends on. Either map an equivalent Lead field to it in `LeadConvertSettings`
(`metadata-examples.md` §1) so conversion supplies the value explicitly, or set it in an after-insert
automation. Auditing for this is a one-query job: filter the target object for the defaulted field
`= null` and the record having a `Lead` with a matching `ConvertedAccountId` / `ConvertedContactId`.

---

## Gotcha 10: Converting a Queue-Owned Lead Fails Unless You Set an Owner Explicitly

**What happens:** Leads routed to a queue are owned by a `Group`, but "accounts and contacts can't be
owned by a queue" (apexdev.txt L8332–8334). The Apex Developer Guide's own conversion checklist makes
step 8 explicit: "when converting leads owned by a queue, the owner must be specified… Even if you are
specifying an existing account or contact, you must still specify an owner." Apex that omits
`setOwnerId` for a queue-owned lead errors; conversion code that works perfectly against
rep-owned test data breaks the first time it meets a real routed lead.

**When it occurs:** Any org where assignment rules route to queues — which is the normal design for
inbound Web-to-Lead and for SDR pools. It is invisible in unit tests, because a test that inserts a
Lead without an OwnerId gets the running user as owner.

**How to avoid:** In every bulk or automated conversion path, resolve an owner before building the
`Database.LeadConvert` (see the `newOwnerId` parameter in `metadata-examples.md` §6) and assert on it.
Seed at least one queue-owned Lead into the test fixture. In the Convert Lead dialog, this is why
`allowOwnerChange` in `LeadConvertSettings` should be `true` for orgs that route to queues — without
the Record Owner picker the rep has no way to supply one.

---

## Gotcha 11: `Database.convertLead` Burns a DML *Statement*, Not a DML Row — and 100 Is the Recommended Ceiling Per Call

**What happens:** Conversion is metered against the wrong limit from most people's intuition.
`Database.convertLead` is on the documented list of calls that "count against the number of DML
statements issued in a request" (salesforce_app_limits_cheatsheet.txt L140–142), and that limit is
**150 per transaction**, synchronous or asynchronous
(salesforce_app_limits_cheatsheet.txt L64). So a loop that converts one lead at a time dies at 151
leads regardless of how few rows each conversion touches. Separately, the Apex Reference Guide caps
the batch size from the other direction: "We recommend passing a maximum of 100 LeadConvert objects to
the convertLead method. Including more than 100 objects per call can result in Apex governor limit
errors" (apexrefguide.txt L205831–205833).

**When it occurs:** Backfills, mass-conversion buttons, invocable actions called from a
record-triggered Flow on a data load, and any `@InvocableMethod` written by copying the guide's
one-record `ConvertLeadAction` sample, which loops `Database.convertLead` per request
(apexdev.txt L5498–5502).

**How to avoid:** Build a `List<Database.LeadConvert>`, chunk it at 100, and call
`Database.convertLead(chunk, false)` once per chunk — that is 1 DML statement per 100 leads instead of
100. Use `allOrNone = false` so one bad lead does not roll back the batch, then iterate
`LeadConvertResult` and read `getErrors()` (`metadata-examples.md` §6). `convertLead` is available
only as a `Database` class method and never as a bare DML statement
(apexdev.txt L7589), so there is no statement form to fall back on.

---

## Gotcha 12: Converted Leads Are Read-Only, Which Breaks the Obvious Backfill Plan

**What happens:** "After a lead has been converted, it's read only. However, you can query converted
lead records. Only users with the View and Edit Converted Leads permission can update converted lead
records" (object_reference.txt L163919–163922). The natural remediation for Gotcha 1 — "we'll flip a
flag on the Leads we already fixed so we know which ones are done" — is a write to a read-only record
and fails for every user without that permission, including the integration user running the
Data Loader job.

**When it occurs:** During the cleanup that follows the discovery of an unmapped field. It also bites
reporting-side workarounds that try to stamp a batch id or a "remediated" checkbox onto converted
Leads, and any Flow or trigger that updates the Lead in an after-conversion path.

**How to avoid:** Query converted Leads freely — `IsConverted`, `ConvertedAccountId`,
`ConvertedContactId`, `ConvertedOpportunityId`, `ConvertedDate` and `Status` are all filterable
(object_reference.txt L163925–163930) — and write the remediation state to the **target** record, not
back to the Lead. If Leads genuinely must be updated, grant View and Edit Converted Leads deliberately
and to a named set of users, not to the profile at large: it also makes historical Leads editable,
which is a different risk from the one you were solving.
