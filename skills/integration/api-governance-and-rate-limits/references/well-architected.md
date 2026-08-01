# Well-Architected Notes — API Governance and Rate Limits

**Reliability:** the 24-hour allocation is a shared, exhaustible resource with no
per-consumer isolation, so one consumer's change is every consumer's outage. The
governance controls that matter are attribution (a Connected App and user per consumer)
and admission control (refuse to start a job that cannot fit in measured headroom).
Retrying a spent daily allocation consumes the allocation it is waiting for.

**Operational Excellence:** read the org's published meter rather than deriving an
estimate. `/limits` reports `Max` and `Remaining` and is documented as accurate within
five minutes of consumption, so thresholds belong at 70% and 85%, not 99%. Attribution
cannot be reconstructed after the fact — it has to exist before the incident.

## Official Sources Used

- Salesforce Platform API limits — daily API request allocations by edition, the concurrent long-running request allocation (25 production/sandbox, 5 Developer Edition and Trial), and the REQUEST_LIMIT_EXCEEDED exception code — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm
- /limits REST resource — Max and Remaining semantics, and "Tabulated limits returned by the API are accurate within five minutes of resource consumption" — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_limits.htm
- REST API Developer Guide — request and response headers, including the API usage header — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest_headers.htm
- Bulk API 2.0 Developer Guide — the volume path that stops consumption scaling with row count — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/
- EventLogFile object reference — the ApiTotalUsage event type used for per-consumer attribution — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm
