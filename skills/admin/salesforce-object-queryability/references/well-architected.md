# Well-Architected Notes — Salesforce Object Queryability

## Relevant Pillars

- **Reliability** — Classifying query failures into the six real modes (instead of a single "not queryable") is what lets an agent be retryable, recoverable, and honest. Silent failures are the #1 source of "looks complete but isn't" reports in live-org agents.
- **Operational Excellence** — Runbooks for each failure mode save hours of debugging. A classified error tells the next engineer exactly which remediation to apply.
- **Security** — `INSUFFICIENT_ACCESS_OR_READONLY` is a security control working correctly; swallowing it masks a meaningful signal.

## Architectural Tradeoffs

### Diagnose vs retry-and-hope

| Approach | When |
|---|---|
| Classify → remediate | Any query running more than once; any multi-dimension probe; any CI job |
| Retry-and-hope | Exactly never in probes. Fine in transient external-API clients with 5xx handling. |

### Data API vs Tooling API routing

Some objects live on one, some on the other, some on both. A probe that hard-codes one endpoint fails opaquely on the other. Design: probe recipes declare `endpoint: data` or `endpoint: tooling` per query, and the runner honors it.

### Caching describe calls

A single `describe` per sObject per run is fine. A describe per query is wasteful (they count against API limits). A probe that issues 9 queries across 7 sObjects should do 7 describes (cached), not 9.

## Anti-Patterns

1. **Generic "not queryable" as an error class** — hides six different remediations. Fix: six-mode classification.

2. **Silent try/except around query code** — the ExampleOrg incident's root cause. Fix: catch specific, classify, log, propagate.

3. **Hallucinated object names from pattern-matching** — `PermissionSetGroupAssignment` doesn't exist. Fix: validate against `/sobjects/` describe before every new-object query.

4. **Treating empty result as failure** — `{"totalSize": 0}` is a success. Fix: distinguish at the envelope layer.

5. **Hard-coded API version** — v62 today, v65 tomorrow. Fix: read from `sf` config or the `/services/data/` listing.

## Official Sources Used

- **REST API Developer Guide** — *Describe Global* (`/services/data/vXX.X/sobjects/`) and its example payload, which carries `queryable`, `keyPrefix`, `createable` and the describe URLs for every object in one call (supports "read `queryable` from the listing, not from a per-object describe" and the caching tradeoff above). PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- **REST API Developer Guide** — *Status Codes and Error Responses*: the 400/403/404/409/500/503 table, the `NOT_FOUND` worked example for a misspelled object name, and `REQUEST_LIMIT_EXCEEDED` on 403 (supports the "classify on the status line, not the code string" anti-pattern and the transient-vs-permanent split).
- **REST API Developer Guide** — *Supported Editions for API Access* and *API User Permissions*: API access on by default in Enterprise, Performance, Unlimited and Developer Edition, a Professional Edition add-on, `API_DISABLED_FOR_ORG` otherwise, and the API Enabled user permission (supports treating org-level API access as the first probe rather than a per-object verdict).
- **Object Reference for the Salesforce Platform** — the *Supported Calls* and *Special Access Rules* conventions: objects whose supported calls omit `query()` (`OpenActivity`, `NoteAndAttachment`, `AttachedContentDocument`, `FeedTrackedChange`), and the permission each setup object names (`AsyncApexJob`/`ApexTestResult` → View Setup and Configuration, `AuthSession` → Manage Users, `OauthToken` → Customize Application). Supports the "presence in the listing is not a promise of `query()`" rule and the permission-set remediation. PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Apex Developer Guide** — *Accessing All sObjects* (`Schema.getGlobalDescribe` keys namespace-prefixed from API 28.0; Chatter sObjects returned from an installed managed package even when Chatter is off) and *Dynamic SOQL* (`AccessLevel.USER_MODE` from API 55.0). Supports the Apex probe in `references/metadata-examples.md` and the namespace-vs-missing distinction. PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Reference Guide** — `Schema.DescribeSObjectResult.isQueryable()`, `.isAccessible()` and its API 54.0 versioned behaviour change for custom settings and custom metadata types (supports the "a low-pinned probe class reports access the user does not have" gotcha).
- **Metadata API Developer Guide** — `PermissionSet` / `PermissionSetUserPermission`: the `userPermissions` element shape, the required `enabled` boolean, the `ViewSetup` and `ApiEnabled` sample values, and the note that retrieving permission sets requires retrieving the components they reference (supports the deployable fragment and its `package.xml`). PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Salesforce Developer Limits and Allocations Quick Reference** — Apex governor limits (100 sync / 200 async SOQL queries, 50,000 rows, 10,000 ms sync CPU) and the SOAP `describeSObjects()` cap of 100 objects returned (supports the probe-batch sizing rule).
- **Salesforce Architects — Well-Architected Framework**: https://architect.salesforce.com/ (supports the Reliability and Operational Excellence framing of classified-vs-collapsed failure reporting).
