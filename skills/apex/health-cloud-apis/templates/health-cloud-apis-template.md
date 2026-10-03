# Health Cloud APIs — Work Template

Use this template when building or debugging Health Cloud API integrations.

## Scope

**Skill:** `health-cloud-apis`

**Request summary:** (fill in what the user asked for)

## API Layer Selection

| Operation | Standard SObject API | Healthcare API (FHIR R4) |
|-----------|---------------------|---------------------|
| SOQL queries on clinical objects | Yes | No |
| FHIR-conformant reads for external FHIR clients | No | Yes |
| Bulk data loads | Yes (Bulk API) | No (30-entry limit, five concurrent requests) |
| Business operation with rules (medication statement, enrollment) | Use the Business API under /connect/health | No |
| Internal analytics queries | Yes | No |

**Selected API layer for this integration:** _______________

## Authentication Checklist

- [ ] Org access token for SObject and Business API calls (standard OAuth scopes such as `api`)
- [ ] Healthcare API: OAuth custom scopes for each resource and method (for example `system_condition_read`) assigned to the external client app
- [ ] Healthcare API: `refresh_token` scope assigned to the external client app
- [ ] Healthcare API: Industry APIs terms accepted and SKU present
- [ ] FHIR R4 Support Settings: FHIR-Aligned Clinical Data Model enabled
- [ ] Base URL per region and environment (api., eu., ca., au.; /sandBox/ for sandboxes)

## FHIR Bundle Configuration (if applicable)

- Maximum entries per bundle: 30
- Maximum read/search operations per bundle: 10
- Bundle type: batch (transaction is not supported)
- Concurrency cap: 5 requests per org
- Bundle chunking implemented: [ ] Yes [ ] No
- HTTP 424 dependency error handling implemented: [ ] Yes [ ] No

## Error Handling Pattern

For FHIR bundles:
1. Scan all bundle entries for HTTP 424 status
2. Trace each 424 to its referenced bundle entry
3. Find root non-424 failure
4. Fix root cause
5. Resend the failed root and its dependents only (successful batch entries are already committed)

## Notes

(API version used, specific FHIR resources and custom scopes in scope, error handling decisions)
