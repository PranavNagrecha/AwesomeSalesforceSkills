# Gotchas — Multi-Org Strategy

---

## 1. Salesforce-to-Salesforce Does Not Scale — It Consumes API Limits on Both Orgs Simultaneously

Salesforce-to-Salesforce uses SOAP API calls under the hood. Every record that is published from one org and subscribed in another generates at least one API call against the target org's daily limit — and often additional calls to acknowledge receipt. At low volumes (a few hundred records per day) this is invisible. At enterprise volumes (tens of thousands of records), S2S becomes a significant API budget drain on both orgs.

The deeper problem: S2S offers no native retry logic, no dead-letter queue, and no visibility into in-flight failures beyond the S2S connection log in Setup. When the target org's API limit is exhausted, S2S silently drops records rather than queuing them for retry.

**What to do instead:** Replace S2S with REST API + Named Credentials (for low/medium volume) or Bulk API 2.0 (for high volume). Both provide explicit error handling, idempotency via external ID upserts, and full observability through standard API monitoring.

---

## 2. Cross-Org Formula Fields and Rollup Summaries Are Impossible Natively

A common design mistake in multi-org architectures is assuming that Salesforce's declarative formula and rollup summary features can span org boundaries. They cannot. Formula fields can only reference fields on the same record or related records within the same org. Roll-up summary fields (and the related COUNT, SUM, MIN, MAX operations) work only within a single org's object relationship graph.

This means that any calculation that requires data from two orgs — for example, "total contract value across all orgs for this customer" — must be implemented as:

1. A scheduled Apex batch job that queries the remote org via REST API, performs the aggregation in Apex, and writes the result back to the local org as a standard field, or
2. An external analytics tool (CRM Analytics, Tableau) that reads from both orgs and aggregates in the reporting layer.

Neither option is declarative. Both require maintenance, error handling for failed callouts, and careful governor limit design. Factor this complexity into the build and support cost estimate for any multi-org reporting requirement.

---

## 3. Governor Limits Are Independent Per Org — Cross-Org Calls Consume Limits on Both Sides

Each Salesforce org has its own independent governor limit budget. A REST API callout from Org A to Org B consumes:

- **Org A (calling org):** One Apex callout (toward the 100 callout per transaction limit), one HTTP request timeout slot, and SOQL limits if the calling Apex queries data before making the callout.
- **Org B (receiving org):** One inbound API request (toward the org's daily API call limit), SOQL limits for the query that fulfills the request, and DML limits if the callout triggers a record write.

A design that fits comfortably within one org's limits may fail silently when two orgs interact at scale. The most common failure mode is an Apex batch job in Org A that makes one callout per record chunk — seemingly within the 100-callout limit per transaction — but the job processes enough batches to exhaust Org B's daily API limit before the job completes.

**What to do:** Model the governor limit consumption on both sides before committing to a cross-org integration pattern. For high-volume sync, use Bulk API 2.0 which uses a job-based model rather than per-record SOAP/REST calls. Monitor API usage in both orgs and set API usage alerts.

---

## 4. User Deactivation Must Be Performed Independently in Every Org — There Is No Native Sync

When an employee leaves the company, their Salesforce user record must be deactivated in every production org they have access to. There is no native mechanism in Salesforce to propagate a deactivation from one org to another. A user who is deactivated in the primary org but remains active in a spoke org retains full access to that spoke org — including any data in it.

This is a security risk, not just an operational nuisance. In regulated industries, orphaned active user accounts in spoke orgs can constitute a compliance violation.

**What to do:** Implement identity lifecycle management via an external IdP (Okta, Azure AD) with SCIM provisioning configured for each org. When HR deactivates the IdP account, SCIM pushes the deactivation to every connected Salesforce org automatically. Do not rely on a manual checklist for multi-org offboarding — it will eventually be missed.

---

## 5. External Objects (Salesforce Connect) Count Against SOQL Limits — One External Query Per Invocation

Salesforce Connect's External Objects look like standard Salesforce objects in the UI and can be used in SOQL queries, list views, and Lightning pages. This can create a false sense that they behave like cached local data. They do not.

Every access to an External Object record generates a live OData request to the remote system (or remote Salesforce org acting as the OData endpoint). In an Apex context, each External Object SOQL query counts as one external SOQL call within the single invocation limit. If a page displays a list of 50 External Object records and a user opens each one, each open triggers a new OData request. If Apex processes a collection of External Object records in a loop, each iteration may trigger a separate external call.

Additionally, External Object queries do not participate in Salesforce's query plan optimization the same way native SOQL does. Complex WHERE clauses on External Objects may result in full table scans on the remote system.

**What to do:** Use External Objects for low-volume, on-demand cross-org lookups (a single record displayed in a detail page, a reference field on a form). Do not use External Objects in bulk Apex processing, trigger logic, or any context where the number of records retrieved is unbounded. For bulk or batch scenarios, replicate the data into the local org via Bulk API 2.0 instead.

---

## 6. Hard-Coded Org IDs Break Across Environments and Cannot Be Deployed

Every Salesforce org has a unique 18-character Organization ID. When developers hard-code an org ID into Apex, a Flow, or a Custom Setting to route a callout to a specific target org, that value is environment-specific. The org ID of a sandbox is different from the org ID of production. The org ID of the EU spoke org is different from the org ID of the US hub org.

Hard-coded org IDs embedded in code or configuration create deployment failures when code is promoted across environments and silent misdirected callouts when a wrong environment is targeted. They are also a code review smell — a reviewer cannot easily distinguish a legitimate constant from a stale ID from a development org.

**What to do:** Store target org identifiers — including base URLs, org IDs if needed, and any environment-specific routing values — in Named Credentials or Custom Metadata Types. Named Credentials are the correct home for authentication configuration including endpoint URLs. Custom Metadata Types are deployable across environments with environment-specific values, making them suitable for org-specific routing configuration that is not authentication-related.

---

## 7. Salesforce Connect External Data Sources Require a Dedicated Integration User With Specific Permissions in the Target Org

When the Salesforce Connect OData adapter is used to surface data from a remote Salesforce org as External Objects, the OData requests are executed as a specific integration user in the target org. That user must have:

- API access enabled
- Read permission on all objects and fields exposed via the OData endpoint
- A valid active license (Integration User license or higher)

If the integration user is deactivated, the OData adapter fails silently from the end-user perspective — External Object queries return no rows or a generic error, with no obvious indication in the calling org that the root cause is a deactivated user in the target org.

**What to do:** Dedicate a named integration user in each target org for each external data source. Do not use a personal user account. Monitor the integration user's active status as part of org health monitoring. Include the integration user in the SCIM provisioning flow from your IdP, but configure it so that deactivation requires an explicit manual override — this prevents the integration user from being auto-deactivated when a departing employee coincidentally has the same username pattern.
