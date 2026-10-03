# Well-Architected Notes — Health Cloud APIs

## Relevant Pillars

- **Security**: The Healthcare API authorizes each resource and method with its own OAuth custom scope (for example `system_condition_read`), and the external client app must also hold `refresh_token`. Grant the narrowest scope per consumer. FHIR payloads carry PHI, so tokens and refresh tokens need secure storage and rotation. Clinical objects on Experience Cloud sites need the FHIR R4 for Experience Cloud Sites permission set.
- **Performance**: Bundles cap at 30 entries (10 reads), Salesforce recommends at most five concurrent requests per org, and the documented typical response time is about three seconds. Internal, high-volume consumers belong on the SObject API or Bulk API 2.0.
- **Reliability**: Only `batch` bundles are supported, so partial success is normal. A 424 marks an entry cancelled because an entry it depends on failed. Retry logic must resend failed roots and their dependents, never the whole bundle, and writes must be idempotent.

## Architectural Tradeoffs

**Healthcare API vs. SObject API vs. Business APIs:** The Healthcare API gives external FHIR clients FHIR R4 resources but adds regional hosts, custom scopes, bundle limits, and no code-set validation. The SObject API has higher throughput and full SOQL for internal consumers. The Business APIs under `/connect/health` wrap multi-object operations such as medication statements and enrollments in one call, which is the safer choice when business rules must apply.

**Batch bundles vs. a Salesforce-side atomic write:** An earlier version of these notes described atomic `transaction` bundles. The Healthcare API supports only `batch`. When resources must commit together, write them through a Business API or the SObject API with `allOrNone`, and keep the Healthcare API for interoperability reads and independent writes.

## Anti-Patterns

1. **Calling `/services/data/.../fhir` paths or requesting a `healthcare` scope**: Neither exists in the Healthcare API guide; use `api.healthcloud.salesforce.com` and resource custom scopes.
2. **Assuming standard API batch limits apply to FHIR bundles**: Bundles are limited to 30 entries, 10 of them reads.
3. **Not handling HTTP 424 dependency errors specifically**: Generic 4xx handling misdiagnoses bundle failures and duplicates committed writes on retry.

## Official Sources Used

Fetched and read on 2026-10-03.

- Salesforce Healthcare API, Get Started (resources, Bundle batch-only rule, 30-entry and 10-read limits, 424 behavior, data centers). https://developer.salesforce.com/docs/industries/health/guide/get-started.html
- Salesforce Healthcare API, Authorization (OAuth custom scopes per resource and method, refresh_token requirement). https://developer.salesforce.com/docs/industries/health/guide/authorization.html
- Salesforce Healthcare API, Call the API (URL format, modules, regional and sandbox domains). https://developer.salesforce.com/docs/industries/health/guide/call-the-api.html
- Salesforce Healthcare API, Considerations (three-second response time, five concurrent requests, no code-set validation, SMART scope format not supported). https://developer.salesforce.com/docs/industries/health/guide/considerations.html
- Salesforce Healthcare API, FAQ and Consent (Winter '23 minimum, SKU, Industry APIs terms). https://developer.salesforce.com/docs/industries/health/guide/faq.html and https://developer.salesforce.com/docs/industries/health/guide/consent.html
- Agentforce Health Developer Guide, Summer '26: Clinical Data Model (FHIR R4 Support Settings org preference, FHIR R4 for Experience Cloud Sites permission set), HealthCondition and ClinicalEncounter (API 51.0), Health Cloud Business APIs (REST Reference, Medication Statements, Create Patient Apex), Health Cloud FHIR APIs. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/health_cloud_dev_guide.pdf
- Metadata API Developer Guide, Version 67.0: OauthCustomScope, ExtlClntAppOauthSettings, ExtlClntAppOauthConfigurablePolicies. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce Well-Architected Overview, archived 2026-06-16. http://web.archive.org/web/20260616115029/https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Listed by an earlier version of this skill and not readable on 2026-10-03: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_healthcare_api.htm (redirects to help.salesforce.com, which returns a script shell) and https://developer.salesforce.com/docs/atlas.en-us.health_cloud_object_reference.meta/health_cloud_object_reference/ (superseded by the PDF above).
