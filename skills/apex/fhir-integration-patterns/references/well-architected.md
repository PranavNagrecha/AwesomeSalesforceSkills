# Well-Architected Notes: FHIR Integration Patterns

## Relevant Pillars

- **Security**: FHIR integrations carry PHI. Healthcare API clients authorize through an external client app with custom scopes per resource and method (for example `user_condition_read`), not wildcard SMART scopes. Middleware CDS Hooks services must authenticate the EHR. Portal users get the FHIR R4 for Experience Cloud Sites permission set only when they need clinical records.
- **Reliability**: Middleware is on the critical path; the Health Cloud guide requires a middleware solution to convert HL7 and FHIR messages. Dead-letter queues, retries for transient failures, 424 handling for dependent Bundle entries, and alerting on pipeline health keep clinical data flowing. Codes are not validated by Salesforce, so validation belongs in middleware.
- **Performance**: The Healthcare API guide expects about 3 seconds per call, recommends at most five concurrent requests, and caps Bundles at 30 entries (up to 10 reads or searches). High-volume backfills should batch accordingly or load the Clinical Data Model objects through the standard bulk APIs.

## Architectural Tradeoffs

**MuleSoft Direct Integration apps vs custom middleware:** Salesforce publishes MuleSoft apps for EMR synchronization, HL7 v2 event ingestion, CDS Hooks, bulk FHIR data, C-CDA ingestion, and prior authorization. They shorten delivery when a MuleSoft instance is available. Custom middleware (including Apex normalizers such as the example in `code-examples.md`) gives more control but must implement every mapping rule from the guide's tables.

**Clinical Data Model writes vs Healthcare API:** Writing sObjects gives full control over Salesforce-specific fields and bulk loading; the Healthcare API offers a FHIR R4 REST surface for external FHIR clients with its own scopes and limits.

**Real-time vs batch sync:** Event-driven sync keeps data current but depends on EHR availability; scheduled reconciliation tolerates downtime but adds latency. Most designs use both.

## Anti-Patterns

1. **Treating Salesforce as a CDS Hooks service**: CDS Hooks is delivered through a MuleSoft integration.
2. **Sending raw FHIR without normalization**: CodeableConcepts cap at 15 codings, complex types are flattened, Condition.code is required, and some elements are unsupported.
3. **Writing packaged HC24 EHR objects**: new customers can't create records in packaged EHR objects that have standard counterparts.

## Official Sources Used

- Agentforce Health (Health Cloud) Developer Guide, Summer '26 (262): "Clinical Data Model" (org preference, object list, Spring '23 note, Experience Cloud permission set), "Mapping FHIR v4.0 to Salesforce Standard Objects," "Considerations for Integration," Address, CodeableConcept, Coding, and Condition mapping tables, "Coverage Requirement Discovery," "Health Cloud FHIR APIs." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/health_cloud_dev_guide.pdf
- Salesforce Healthcare API guide, "Get Started" (fetched 2026-10-03): https://developer.salesforce.com/docs/industries/health/guide/get-started.html
- Salesforce Healthcare API guide, "Call the API" (fetched 2026-10-03): https://developer.salesforce.com/docs/industries/health/guide/call-the-api.html
- Salesforce Healthcare API guide, "Authorization" (fetched 2026-10-03): https://developer.salesforce.com/docs/industries/health/guide/authorization.html
- Salesforce Healthcare API guide, "Considerations" (fetched 2026-10-03): https://developer.salesforce.com/docs/industries/health/guide/considerations.html
- Salesforce Healthcare API guide, "FAQ" and "Prerequisites" (fetched 2026-10-03): https://developer.salesforce.com/docs/industries/health/guide/faq.html and https://developer.salesforce.com/docs/industries/health/guide/prerequisites.html
- Salesforce Healthcare API guide, "Explore MuleSoft Direct Integration Apps" (fetched 2026-10-03): https://developer.salesforce.com/docs/industries/health/guide/integrations.html

### Earlier references kept from version 1.0.0 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- Health Cloud Developer Guide, Mapping FHIR v4.0 (atlas page; the 262 PDF above was read instead): https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_fhir_mapping.htm
- MuleSoft Direct Integration Apps, healthcare FHIR patterns: https://docs.mulesoft.com/ (page retired; see host index)
- FHIR R4 Support for Better Interoperability (Release Notes): https://help.salesforce.com/s/articleView?id=release-notes.rn_ind_hc_fhir_r4.htm (help.salesforce.com does not return article text to a fetch)
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (Well-Architected guide pages redirect to the home page)
