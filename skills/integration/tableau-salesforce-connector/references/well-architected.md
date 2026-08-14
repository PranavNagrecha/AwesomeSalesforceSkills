# Well-Architected Notes — Tableau ↔ Salesforce Connector

## Relevant Pillars

- **Performance** — The connector is extract-based, so dashboard performance is
  decoupled from Salesforce query performance entirely: users read a Hyper
  extract, not the org. What Salesforce performance *does* govern is refresh
  duration and whether a refresh finishes inside its window. The optimisation
  target is therefore extract size and refresh frequency, not dashboard query
  tuning — a distinction that sends teams down the wrong path when a dashboard
  "feels slow" and the actual problem is a 4-hour refresh.

- **Scalability** — The scaling constraint is the org's 24-hour API allocation
  and the concurrent long-running request pool, both of which the reporting
  estate shares with every integration in the org. Each new workbook is a
  standing draw on a shared budget. Governance that treats workbook publication
  as free is the thing that eventually breaks an unrelated middleware job.

- **Security** — The extract inherits the connecting user's sharing and
  field-level security *at extract time* and then freezes it. Someone who loses
  access in Salesforce on Tuesday still sees Tuesday's rows in the dashboard
  until the next refresh, and Tableau's own permissions decide who opens the
  workbook. Salesforce sharing is not the access control for Tableau content; it
  only bounds what entered the extract.

## Architectural Tradeoffs

**Extract freshness vs API budget.** These are the same dial. Every increase in
refresh frequency is a proportional increase in API consumption, and the
allocation is fixed by edition and licence count. The honest design conversation
is "how stale may this be", answered in minutes, with the API cost of each answer
priced. "As fresh as possible" is not an answer; it is a deferred decision.

**Connector vs Data Cloud as the query layer.** The CRM connector is direct and
extract-only, with restricted joins (left and inner, equality only) and no
formula fields. Data Cloud adds a layer to build and operate, and in exchange
gives cross-source joins, governed semantics in one place, and a query path that
does not draw on the CRM org's API allocation. The connector is right for a
handful of Salesforce-only workbooks; the extra layer earns its keep once
Salesforce data has to be joined to anything else, or once the workbook count
makes per-workbook extract governance unmanageable.

**Tableau vs Salesforce-native reporting.** Salesforce reports inherit sharing
live, need no refresh, and cost no API calls. Tableau gives visualisation depth
and cross-source analysis, and costs a licence, a refresh pipeline, and a second
access-control model to keep aligned. Migrating a report to Tableau because it is
"nicer" trades away live sharing enforcement for presentation — sometimes worth
it, never free.

**Where formula logic lives.** Formula fields do not survive into the extract, so
each one becomes a choice: re-implement in Tableau (fast, and now the definition
exists twice and will diverge) or materialise into a stored Salesforce field
(one definition, at the cost of storage and an automation to maintain it). Pick
per field on how many consumers the metric has, and record the decision — this is
the most common source of "the two systems disagree" tickets in this domain.

## Anti-Patterns

1. **Designing around a live connection.** The Salesforce CRM connector is
   extract-only. A live mode written into an architecture document cannot be
   built and is usually discovered after the dashboards exist.
2. **Connecting as a cloned System Administrator.** The extract inherits that
   user's visibility, turning every workbook into an org-wide export and making
   refresh traffic indistinguishable from admin activity in API usage reports.
3. **Publishing workbooks without a refresh budget.** Refresh cost is invisible at
   publication time and lands on a shared allocation, so the failure surfaces on
   an unrelated integration.
4. **Assuming Salesforce sharing governs dashboard access.** It bounds extract
   contents at refresh time; Tableau permissions decide who reads the result.

## Official Sources Used

- Tableau Help — Salesforce CRM connector — https://help.tableau.com/current/pro/desktop/en-us/examples_salesforce.htm — confirms "Tableau Desktop, Tableau Server, and Tableau Cloud are limited to extracts when using the Salesforce CRM connector"; that "Only left and inner joins are supported" and Salesforce connections "do not support non-equi joins and must use the equality operator (=)"; that "text fields that are greater than 4096 characters and calculated fields will not be included in the extract"; that "The Force.com API restricts queries to 10,000 total characters"; that incremental refresh results are "limited to the previous 30 days"; and the five APIs the connector requires (SOAP API, REST API for metadata, Bulk API, REST API for non-Bulk objects, Replication SOAP APIs) (verified 2026-08-14)
- Tableau Help — Create Workbooks with Salesforce Data — https://help.tableau.com/current/online/en-us/to_connect_salesforce.htm — confirms "API access requires Salesforce Professional Edition or higher", that the Tableau Cloud connection requires the "Site Administrator Creator site role", and that extracts do not refresh automatically without a configured schedule (verified 2026-08-14)
- Tableau Help — Configure a Tableau View Lightning Web Component — https://help.tableau.com/current/online/en-us/lwc_tableau_view.htm — confirms the component embeds on "App, Home, and Record pages, as well as Experience Cloud pages", that "The following fields make it possible to dynamically filter on up to two fields", that "The URL must be for a view, not a workbook", and that "You must enter field names as they are defined in the data source" (verified 2026-08-14)
- Tableau Help — Embed Tableau Views into Salesforce — https://help.tableau.com/current/pro/desktop/en-us/embed_ex_lwc.htm — confirms that "These methods of filtering only work on Lightning record pages. Filtering is not available for Home pages or App pages", that the component "only supports SAML as the SSO method", and that "The SAML IdP used for Tableau authentication must be either the Salesforce IdP or the same IdP that is used for your Salesforce instance" (verified 2026-08-14)
- Salesforce Developer Limits and Allocations — API Request Limits and Allocations — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm — confirms the 24-hour allocations by edition (15,000 Developer Edition; 100,000 base plus per-licence for Enterprise/Professional and Unlimited/Performance; 5,000,000 full sandbox), the concurrent limit of 25 for production orgs and sandboxes on requests lasting 20 seconds or longer, and that exceeding it returns the `REQUEST_LIMIT_EXCEEDED` exception code (verified 2026-08-14)

- Metadata API Developer Guide — PermissionSet — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_permissionset.htm — confirms "In API version 30.0 and later, permissions for required fields can't be retrieved or deployed", which is why the least-privilege permission set in `examples.md` carries no `fieldPermissions` entry for `Opportunity.StageName` (verified 2026-08-14)

**Not verified, deliberately omitted:** CSP Trusted Sites entries and
`X-Frame-Options` requirements for the Tableau embed. The embed pages read above
do not state them, and the Salesforce-side setup article is on
`help.salesforce.com`, which could not be read directly. Confirm against the
current Setup documentation before writing them into a runbook.
