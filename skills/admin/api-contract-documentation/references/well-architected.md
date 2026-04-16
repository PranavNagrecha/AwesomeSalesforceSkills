# Well-Architected Notes — API Contract Documentation

## Relevant Pillars

### Reliability
API contract documentation is a reliability prerequisite — consumer teams cannot build reliable integrations without knowing versioning policy, rate limits, and error handling requirements. The EOL check cadence and rate limit monitoring patterns in this skill directly support integration reliability.

### Security
Documenting authentication requirements and error code meanings prevents consumer teams from implementing incorrect error handling that might expose sensitive data (e.g., treating 401 as a retriable error without re-authentication).

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Change Management | API versioning policy documentation with upgrade SLA prevents surprise breaking changes |
| Observability | Sforce-Limit-Info monitoring pattern provides visibility into API consumption trends |
| Documentation Standards | OpenAPI 3.0 as the documentation format ensures machine-readable, tooling-compatible specs |

## Cross-Skill References

- `integration/apex-rest-services` — Use for implementing custom Apex REST endpoints that this skill documents
- `integration/api-led-connectivity` — Use for designing the API layer architecture before documenting individual endpoints
- `integration/connected-app-security` — Use for OAuth flow setup referenced in API authentication documentation

## Official Sources Used

- Salesforce REST API Developer Guide — API End-of-Life Policy: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/api_rest_eol.htm
- Salesforce REST API Developer Guide — Status Codes and Error Responses: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm
- Salesforce REST API Developer Guide — Limits Resource: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm
- Salesforce Developer Limits Quick Reference: https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/
- OpenAPI 3.0 for sObjects REST API (Beta): https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/openapi_beta.htm
