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

- Salesforce Developer — REST API Error Codes: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm
- Salesforce Developer — Tooling API Guide: https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/
- Salesforce Developer — sObject Describe: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_sobject_describe.htm
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/
