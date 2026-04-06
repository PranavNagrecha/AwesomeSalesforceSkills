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
