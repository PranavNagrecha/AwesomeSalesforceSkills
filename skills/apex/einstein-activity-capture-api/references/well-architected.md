# Well-Architected Notes — Einstein Activity Capture API

## Relevant Pillars

- **Security** — EAC data includes synced private email content. Any Apex code that reads `ActivityMetric` or `UnifiedActivity` must apply `with sharing` to respect Salesforce sharing rules. Developers must not expose EAC email content or engagement metrics to users who do not own or have access to the related Contact or Lead. Profile-level permission for `View All Data` should not be used as a substitute for proper sharing enforcement.
- **Reliability** — EAC data availability is conditional: it requires active connected accounts, the EAC feature being enabled, and data in the supported query objects. Code that assumes EAC data is always present will fail silently (empty SOQL results) in degraded conditions. Defensive null-checks and zero-default aggregations are required for reliability.
- **Operational Excellence** — EAC storage model differences (standard vs Write-Back) create a fork in operational assumptions. Teams must document which model the code was written for, so that future releases or EAC feature upgrades (e.g., moving to Write-Back) do not silently break existing integrations.
- **Performance** — `ActivityMetric` can accumulate many rows per contact over time (one row per day per metric type). Queries without an `ActivityDate` filter will scan the full history and consume significant SOQL row limits. Always filter by date range and consider using `@AuraEnabled(cacheable=true)` for UI-bound reads.

## Architectural Tradeoffs

**Aggregate counts vs individual records:** `ActivityMetric` provides aggregate daily counts and is the lowest-friction EAC read surface. It does not allow access to email subject lines, body, or individual event details. If the use case requires individual record detail, the org must have EAC Write-Back or `UnifiedActivity` access — which introduces EAC edition requirements and additional setup. Teams should decide this tradeoff before building the data model.

**Periodic batch reads vs trigger-driven reactions:** EAC does not support trigger-driven reactions to synced activity. Architectures that need to respond to new activity (e.g., updating a "last engaged" date) must use scheduled batch jobs or scheduled flows rather than event-driven patterns. This introduces latency — typically minutes to an hour depending on sync frequency — that must be acceptable to the business use case.

**Custom UI vs native Activity Timeline:** The native Activity Timeline surfaces EAC data without any developer code. Custom Apex + LWC solutions add maintenance cost and must work within the documented SOQL constraints. Prefer the native timeline for display-only needs; use custom Apex only when business logic needs to compute on EAC data or feed it into other processes.

## Anti-Patterns

1. **Querying Task/Event/EmailMessage for EAC data without confirming Write-Back** — In standard EAC orgs this produces silent zero-row results, giving developers a false impression that EAC is broken or misconfigured. Always confirm the EAC storage model before choosing the query surface.
2. **Designing trigger-based EAC pipelines** — EAC syncs do not fire Apex triggers on standard objects. Building architecture that assumes a trigger will catch new EAC-synced emails or meetings will produce a system that silently does nothing. Use scheduled patterns instead.
3. **Ignoring EAC data absence in aggregate calculations** — Computing engagement scores or KPIs using `ActivityMetric` without handling the case where a contact has zero rows (no connected account, EAC not enabled) produces misleading zeroes that look like disengagement rather than missing data. Distinguish between "zero engagement measured" and "no EAC data available."

## Official Sources Used

- Einstein Activity Capture documentation — https://help.salesforce.com/s/articleView?id=sf.einstein_sales_eac.htm
- ActivityMetric Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_activitymetric.htm
- UnifiedActivity Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_unifiedactivity.htm
- EACSettings Metadata API — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_eacsettings.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
