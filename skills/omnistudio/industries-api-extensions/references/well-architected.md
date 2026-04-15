# Well-Architected Notes — Industries API Extensions

## Relevant Pillars

- **Trusted** — Industry API extensions enforce business-rule guarantees (atomic policy issuance, E&U transition validation) that standard REST CRUD cannot provide. Using the correct API layer is a prerequisite for data integrity and compliance. Direct DML bypasses these controls and creates an audit and regulatory risk.
- **Adaptable** — The TM Forum Open API standard gives Communications Cloud integrations an industry-standard interface that can be consumed by any BSS/OSS system implementing the TM Forum specification. This decouples the integration from Salesforce-specific internal structures. However, the Salesforce implementation is ID-driven rather than name-driven, which requires adapter logic at the seam.
- **Resilient** — Industry Connect APIs return structured, transactional error responses rather than partial-success states. Designing error handling to consume the structured error body (not fallback record inspection) is essential for correct retry and escalation behavior.
- **Efficient** — Each industry Connect API call performs multiple sObject operations in a single HTTP round-trip (policy + coverages, asset status + audit record). Replacing multi-step Apex DML sequences with a single Connect API call reduces governor-limit consumption and integration latency.

## Architectural Tradeoffs

**Industry Connect API vs Direct DML: Compliance and Consistency vs Simplicity**

Industry Connect APIs introduce an additional HTTP call and a dependency on the industry API endpoint being available and correctly versioned. Direct DML is simpler to write and test against a standard Developer Edition org. However, the compliance risk of direct DML on industry objects is not optional: Insurance Cloud and E&U Cloud objects have referential integrity requirements and regulatory audit requirements that the Connect API layer enforces and direct DML does not. The tradeoff is not a balance — for lifecycle operations, the Connect API is the only correct choice.

**Direct Access vs MuleSoft Gateway (Communications Cloud): Forward Compatibility vs Existing Investment**

Organizations that built Communications Cloud integrations via the MuleSoft gateway made a reasonable choice at the time it was the documented path. The Winter '27 deprecation requires a migration regardless of the existing investment. The correct architectural position now is to plan and execute Direct Access migration, not to defer it. The migration is primarily a URL and authentication reconfiguration; the TM Forum request/response schema itself does not change.

**Service Process API vs Integration Procedure Direct Call: Versioning and Stability vs Performance**

Service Process Studio APIs provide a versioned, named contract for process execution. Calling an Integration Procedure directly (via the OmniStudio Integration Procedure REST endpoint) couples the consumer to the IP's internal parameter naming. Service Process APIs are the preferred pattern for cross-system process invocation because the process API name is a stable contract identifier.

## Anti-Patterns

1. **Direct DML for industry object lifecycle operations** — Writing `insert InsurancePolicy` or `PATCH /sobjects/ServicePoint__c/{id}` for status changes is the most common anti-pattern. It bypasses transaction guarantees, skips computed field calculations (Insurance), and omits required audit records (E&U). The correct pattern is always the vertical-specific Connect API endpoint.

2. **Name-based product resolution in TM Forum payloads** — Passing product names or external catalog codes in TM Forum API request bodies results in silent no-matches or 404 errors. All TM Forum entity references in Communications Cloud must use Salesforce record IDs. There is no name-to-ID resolution in the TM Forum API implementation.

3. **Retaining MuleSoft gateway dependency past Winter '27** — Continuing to route Communications Cloud TM Forum API calls through the deprecated MuleSoft gateway creates a time-bomb that fails silently as a network connectivity error rather than a Salesforce API error. Migrating to Direct Access is the only forward-compatible architectural choice.

## Official Sources Used

- Insurance Policy Business APIs — Insurance Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.insurance_developer_guide.meta/insurance_developer_guide/insurance_policy_business_api_overview.htm
- Communications Cloud TM Forum API Overview — https://help.salesforce.com/s/articleView?id=ind.comms_industries_get_started.htm&type=5
- TMF679 Resource Mappings (Communications Cloud) — https://help.salesforce.com/s/articleView?id=ind.comms_tmf679_resource_mapping.htm&type=5
- Update Asset Status API — Energy and Utilities Cloud Developer Guide — https://help.salesforce.com/s/articleView?id=ind.energy_industry_apis.htm&type=5
- Service Process Studio Connect APIs — Salesforce Industries Reference — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/service_process_studio_connect_apis.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Integration Patterns — Salesforce Architects — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
