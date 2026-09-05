# Well-Architected Notes — Lead Management and Conversion

## Relevant Pillars

- **Operational Excellence** — Lead management is a critical operational pipeline. Silent data loss (unmapped fields), silent submission drops (duplicate blocking, daily limit), and silent auto-response failures all degrade pipeline quality invisibly. Well-architected lead management makes failures visible and configures monitoring to catch them before they affect revenue.
- **Security** — Web-to-lead exposes a public endpoint that any actor on the internet can POST to. Without reCAPTCHA, the endpoint is trivially abused to exhaust the daily submission limit or inject malicious data. Lead field data captured from external forms must be treated as untrusted input — validation rules and field constraints on Lead fields are the first line of defense.
- **Reliability** — The lead pipeline must reliably deliver submitted leads to the correct owner. Assignment rule failures, default-owner misconfiguration, and auto-response dependency on assignment rules are all reliability failure modes that result in leads falling through the cracks undetected.

## Architectural Tradeoffs

**Web-to-lead vs. API-based lead insertion:** Web-to-lead is declarative, requires no development, and is sufficient for orgs under ~400 leads per day. Above that threshold, or when the business requires real-time duplicate checking feedback to the submitter, API-based insertion (REST or SOAP) is the correct pattern — it bypasses the 500/day limit and allows the caller to handle duplicate responses programmatically.

**Silent failures vs. explicit alerting:** Salesforce's default behavior for web-to-lead is to silently discard rejected submissions (duplicate blocks, limit exceeded). Operational excellence requires layering explicit monitoring on top — report subscriptions for daily lead count, duplicate rule alerts set to "Allow" rather than "Block", and admin notifications for assignment rule failures.

**Declarative mapping vs. an after-conversion enrichment step:** `LeadConvertSettings` mappings are free, deployable, and visible in Setup — but they only ever fill *empty* fields on an existing Account or Contact ("only empty fields in the target object are overwritten", Apex Developer Guide, Convert Leads Considerations). Any org where reps routinely convert into existing records has a hard ceiling on what mapping alone can achieve. The tradeoff is between accepting that ceiling and documenting it, or adding an after-conversion update keyed on `ConvertedContactId`, which buys freshness at the cost of a code artefact that has to be maintained and tested. Choosing without naming the ceiling is how orgs end up believing the mapping refreshes data it never touches.

**Global Value Sets for mapped picklist fields:** Using Global Value Sets on picklists that span Lead and conversion target objects trades minor setup complexity for guaranteed picklist value consistency. The alternative — managing two parallel picklist definitions — reliably drifts over time and causes silent field mapping failures.

## Anti-Patterns

1. **Treating web-to-lead as "set and forget"** — Web-to-lead forms have no built-in monitoring, rate alerts, or error surfacing. Orgs that generate the form once and never revisit it will eventually hit the daily limit, have duplicate rules silently block submissions, or have assignment rules deactivate and lose auto-response emails — all without any immediate signal. Operational excellence requires scheduled monitoring reports and admin alert automation layered on top.

2. **Adding Lead custom fields without immediately mapping them** — The pattern of "we'll map the fields later" invariably leads to converted records with missing data. Every Lead custom field should be mapped at the same time it is deployed to production. Treat the mapping step as part of the field deployment, not a post-deployment task.

3. **Relying on auto-response rules without verifying assignment rule dependency** — Auto-response rules appear to be independent configuration objects in Setup, which leads admins to assume they evaluate independently. The dependency on assignment rules firing first is not surfaced in the UI. Treating auto-response as always-on will result in silent email failures when assignment rules change.

## Official Sources Used

Guide sections actually consulted for this skill, with the claim each one supports.

- Metadata API Developer Guide, `LeadConvertSettings` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the `objectMapping` / `mappingFields` / `inputField` / `outputField` structure, `allowOwnerChange`, the `VisibleOptional` / `VisibleRequired` / `NotVisible` enum, and the three-blocks-maximum rule — `references/metadata-examples.md` §1)
- Metadata API Developer Guide, `LeadConfigSettings` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`shouldLeadConvertRequireValidation`, `doesPreserveLeadStatus` and its record-type status-swap behaviour, `doesSelectNoOpportunityOnConvertLead`, `relateEmailsToContactOnConvert` — SKILL.md Lead Settings, Gotcha 8, `metadata-examples.md` §2)
- Metadata API Developer Guide, `StandardValueSet` / `StandardValue` / `CustomValue` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the `converted` flag being relevant only to Lead Status; omitted values are deactivated on deploy; new values are not added to record types automatically — `metadata-examples.md` §3)
- Metadata API Developer Guide, `BusinessProcess` and `DuplicateRule` / `DuplicateRuleFilter` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the lead-process XML shape and its "not an access control mechanism" warning; the `<table>User</table>` filter item that scopes a duplicate rule, and `securityOption` being about sharing on the matched record rather than user exemption — `metadata-examples.md` §4–§5, Gotcha 4)
- Object Reference for the Salesforce Platform, `Lead` and `LeadStatus` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf ("Multiple lead status values can represent a converted lead"; "You can't convert a lead via the API by changing Status"; converted leads are read-only and need View and Edit Converted Leads to update; the converted-state field list — SKILL.md Lead Process and Converted Status, Gotcha 12)
- Object Reference, Default Values in Custom Fields — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf ("Default values are not used for lead conversion, importing, or merging records" — Gotcha 9)
- Apex Developer Guide, Converting Leads and Convert Leads Considerations — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (merge fills empty fields only; record-type defaults come from the new owner and the converting user; queue-owned leads need an explicit owner; `convertLead` exists only as a Database method; query `LeadStatus` for the converted status — Gotchas 7, 8, 10, 11)
- Apex Reference Guide, `Database.LeadConvert`, `Database.LeadConvertResult`, `Database.convertLead` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/ (the setter contract and defaults, the `allOrNone` semantics, and the "maximum of 100 LeadConvert objects" recommendation — `metadata-examples.md` §6, Gotcha 11)
- Salesforce App Limits Cheat Sheet — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf (`Database.convertLead` counts against the 150 DML *statements* per transaction, not the 10,000-row limit — Gotcha 11)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (pillar framing for this file)

Sources carried forward from v1.1.0, used for the Web-to-Lead and validation-enforcement material that
these PDFs do not cover. help.salesforce.com is not fetchable from the authoring environment, so these
were not re-verified on 2026-09-05:

- Salesforce Help: Lead Conversion Field Mapping — https://help.salesforce.com/s/articleView?id=sf.customize_leadconv.htm (Setup navigation path for Map Lead Fields)
- Salesforce Help: Web-to-Lead — https://help.salesforce.com/s/articleView?id=sf.setting_up_web-to-lead.htm (the 500-per-rolling-24-hours submission limit and reCAPTCHA option — Gotcha 3)
- Salesforce Help: Lead Auto-Response Rules — https://help.salesforce.com/s/articleView?id=sf.customize_leadautoresponse.htm (auto-response fires only alongside an assignment rule — Gotcha 2)
- Salesforce Help: Considerations for Converting Leads — https://help.salesforce.com/s/articleView?id=sales.leads_notes.htm&type=5 (lookup filters ignored while Require Validation is off; triggers fire either way — Gotcha 6)
- Salesforce Help: Validation rule not firing when converting Leads — https://help.salesforce.com/s/articleView?id=000386058&type=1 (Gotcha 6)
- Salesforce Help: Enable Use Apex Lead Convert for Validation Rules — https://help.salesforce.com/s/articleView?id=000386851&type=1 (the Support activation request and the mapping-loss regression risk — Gotcha 6)
- Salesforce Help: Resolving Common Lead Conversion Errors in Salesforce — https://help.salesforce.com/s/articleView?id=000383660&type=1 (`REQUIRED_FIELD_MISSING`, `FIELD_FILTER_VALIDATION_EXCEPTION` — Gotcha 6)
