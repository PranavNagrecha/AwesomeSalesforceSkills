# Well-Architected Notes — Lead Management and Conversion

## Relevant Pillars

- **Operational Excellence** — Lead management is a critical operational pipeline. Silent data loss (unmapped fields), silent submission drops (duplicate blocking, daily limit), and silent auto-response failures all degrade pipeline quality invisibly. Well-architected lead management makes failures visible and configures monitoring to catch them before they affect revenue.
- **Security** — Web-to-lead exposes a public endpoint that any actor on the internet can POST to. Without reCAPTCHA, the endpoint is trivially abused to exhaust the daily submission limit or inject malicious data. Lead field data captured from external forms must be treated as untrusted input — validation rules and field constraints on Lead fields are the first line of defense.
- **Reliability** — The lead pipeline must reliably deliver submitted leads to the correct owner. Assignment rule failures, default-owner misconfiguration, and auto-response dependency on assignment rules are all reliability failure modes that result in leads falling through the cracks undetected.

## Architectural Tradeoffs

**Web-to-lead vs. API-based lead insertion:** Web-to-lead is declarative, requires no development, and is sufficient for orgs under ~400 leads per day. Above that threshold, or when the business requires real-time duplicate checking feedback to the submitter, API-based insertion (REST or SOAP) is the correct pattern — it bypasses the 500/day limit and allows the caller to handle duplicate responses programmatically.

**Silent failures vs. explicit alerting:** Salesforce's default behavior for web-to-lead is to silently discard rejected submissions (duplicate blocks, limit exceeded). Operational excellence requires layering explicit monitoring on top — report subscriptions for daily lead count, duplicate rule alerts set to "Allow" rather than "Block", and admin notifications for assignment rule failures.

**Global Value Sets for mapped picklist fields:** Using Global Value Sets on picklists that span Lead and conversion target objects trades minor setup complexity for guaranteed picklist value consistency. The alternative — managing two parallel picklist definitions — reliably drifts over time and causes silent field mapping failures.

## Anti-Patterns

1. **Treating web-to-lead as "set and forget"** — Web-to-lead forms have no built-in monitoring, rate alerts, or error surfacing. Orgs that generate the form once and never revisit it will eventually hit the daily limit, have duplicate rules silently block submissions, or have assignment rules deactivate and lose auto-response emails — all without any immediate signal. Operational excellence requires scheduled monitoring reports and admin alert automation layered on top.

2. **Adding Lead custom fields without immediately mapping them** — The pattern of "we'll map the fields later" invariably leads to converted records with missing data. Every Lead custom field should be mapped at the same time it is deployed to production. Treat the mapping step as part of the field deployment, not a post-deployment task.

3. **Relying on auto-response rules without verifying assignment rule dependency** — Auto-response rules appear to be independent configuration objects in Setup, which leads admins to assume they evaluate independently. The dependency on assignment rules firing first is not surfaced in the UI. Treating auto-response as always-on will result in silent email failures when assignment rules change.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Lead Conversion Field Mapping — https://help.salesforce.com/s/articleView?id=sf.customize_leadconv.htm
- Salesforce Help: Web-to-Lead — https://help.salesforce.com/s/articleView?id=sf.setting_up_web-to-lead.htm
- Salesforce Help: Lead Auto-Response Rules — https://help.salesforce.com/s/articleView?id=sf.customize_leadautoresponse.htm
